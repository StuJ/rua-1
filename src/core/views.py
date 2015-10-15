from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import logout as logout_user
from django.contrib.auth import login as login_user
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse, StreamingHttpResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django import forms
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core import serializers
from django.conf import settings
from  __builtin__ import any as string_any
from core import log
from core import models
from core import forms
from core import logic
from email import send_email
from core import models, forms, logic, log
from files import handle_file_update,handle_attachment,handle_file
from submission import models as submission_models
from core.decorators import is_editor, is_book_editor, is_book_editor_or_author, is_onetasker
from pprint import pprint
import json
from time import strftime
from uuid import uuid4
import os
import mimetypes
import mimetypes as mime

# Website Views

def index(request):
	return redirect(reverse('login'))

def contact(request):

	template = "core/contact.html"
	context = {}

	return render(request, template, context)

# Authentication Views
def dashboard(request):
	if request.user.is_authenticated():
		roles=  request.user.profile.roles.all()
		if request.GET.get('next'):
			return redirect(request.GET.get('next'))
		elif string_any('Editor' for role in roles):
			return redirect(reverse('editor_dashboard'))
		elif string_any('Author' for role in roles):
			return redirect(reverse('author_dashboard'))
		elif string_any('Reviewer' for role in roles):
			return redirect(reverse('reviewer_dashboard'))
		else:
			return redirect(reverse('onetasker_dashboard'))
			
def login(request):
	if request.user.is_authenticated():
		messages.info(request, 'You are already logged in.')
		roles=  request.user.profile.roles.all()
		if request.GET.get('next'):
			return redirect(request.GET.get('next'))
		else:
			return redirect(reverse('user_dashboard'))
			

	if request.POST:
		user = request.POST.get('user_name')
		pawd = request.POST.get('user_pass')

		user = authenticate(username=user, password=pawd)

		if user is not None:
			if user.is_active:
				login_user(request, user)
				messages.info(request, 'Login successful.')
				roles=  user.profile.roles.all()
				if request.GET.get('next'):
					return redirect(request.GET.get('next'))
				else:
					return redirect(reverse('user_dashboard'))
			else:
				messages.add_message(request, messages.ERROR, 'User account is not active.')
		else:
			messages.add_message(request, messages.ERROR, 'Account not found with those details.')

	context = {}
	template = 'core/login.html'

	return render(request, template, context)

@login_required
def logout(request):
	messages.info(request, 'You have been logged out.')
	logout_user(request)
	return redirect(reverse('index'))

def register(request):
	if request.method == 'POST':
		form = forms.UserCreationForm(request.POST)
		if form.is_valid():
			new_user = form.save()
			return redirect(reverse('login'))
	else:
		form = forms.UserCreationForm()

	return render(request, "core/register.html", {
		'form': form,
	})

def activate(request, code):
	profile = get_object_or_404(models.Profile, activation_code=code)
	if profile:
		profile.user.is_active = True
		profile.date_confirmed = timezone.now()
		profile.activation_code = ''
		profile.save()
		profile.user.save()
		messages.add_message(request, messages.INFO, 'Registration complete, you can login now.')
		return redirect(reverse('login'))

@login_required
def view_profile(request):
	try:
		user_profile = models.Profile.objects.get(user=request.user)
	except:
		user_profile = models.Profile(user=request.user)
		user_profile.save()


	template = 'core/user/profile.html'
	context = {
		'user_profile': user_profile,
	}

	return render(request, template, context)

@login_required
def update_profile(request):
	user_profile = models.Profile.objects.get(user=request.user)
	user_form = forms.UserProfileForm(instance=request.user)
	profile_form = forms.ProfileForm(instance=user_profile)
	if request.method == 'POST':
		user_form = forms.UserProfileForm(request.POST, instance=request.user)
		profile_form = forms.ProfileForm(request.POST, request.FILES, instance=user_profile)
		if profile_form.is_valid() and user_form.is_valid():
			user = user_form.save()
			profile = profile_form.save()
			return redirect(reverse('view_profile'))

	template = 'core/user/update_profile.html'
	context = {
		'profile_form' : profile_form,
		'user_form': user_form,
	}

	return render(request, template, context)

@login_required
def user_home(request):

	task_list = models.Task.objects.filter(assignee=request.user, completed__isnull=True).order_by('due')
	new_task_form = forms.TaskForm()

	template = 'core/user/home.html'
	context = {
		'task_list': task_list,
		'proposals': submission_models.Proposal.objects.filter(status='submission').count(),
		'new_submissions': models.Book.objects.filter(stage__current_stage='submission').count(),
		'in_review': models.Book.objects.filter(stage__current_stage='review').count(),
		'in_editing': models.Book.objects.filter(stage__current_stage='editing').count(),
		'in_production': models.Book.objects.filter(stage__current_stage='production').count(),
		'copyedits': models.CopyeditAssignment.objects.filter(copyeditor=request.user, completed__isnull=True),
		'new_task_form': new_task_form,
		'user_submissions': models.Book.objects.filter(owner=request.user),
		'author_copyedit_tasks': logic.author_tasks(request.user),
		'indexes': models.IndexAssignment.objects.filter(indexer=request.user, completed__isnull=True),
		'typesetting': models.TypesetAssignment.objects.filter((Q(requested__isnull=False) & Q(completed__isnull=True)) | (Q(typesetter_invited__isnull=False) & Q(typesetter_completed__isnull=True)), typesetter=request.user),
		'user_proposals': submission_models.Proposal.objects.filter(owner=request.user)
	}

	return render(request, template, context)


@login_required
def user_submission(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	template = 'core/user/user_submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
	}

	return render(request, template, context)

@login_required
def reset_password(request):

	if request.method == 'POST':
		password_1 = request.POST.get('password_1')
		password_2 = request.POST.get('password_2')

		if password_1 == password_2:
			if len(password_1) > 8:
				user = User.objects.get(username=request.user.username)
				user.set_password(password_1)
				user.save()
				messages.add_message(request, messages.SUCCESS, 'Password successfully changed.')
				return redirect(reverse('login'))
			else:
				messages.add_message(request, messages.ERROR, 'Password is not long enough, must be greater than 8 characters.')
		else:
			messages.add_message(request, messages.ERROR, 'Your passwords do not match.')

	template = 'core/user/reset_password.html'
	context = {}

	return render(request, template, context)

def unauth_reset(request):
	pass

def permission_denied(request):

	template = 'core/403.html'
	context = {}

	return render(request, template, context)


# Dashboard
@login_required
def overview(request):

	template = 'core/dashboard/dashboard.html'
	context = {
		'proposals': submission_models.Proposal.objects.exclude(status='declined').exclude(status='accepted'),
		'new_submissions': models.Book.objects.filter(stage__current_stage='submission'),
		'in_review': models.Book.objects.filter(stage__current_stage='review'),
		'in_editing': models.Book.objects.filter(stage__current_stage='editing'),
		'in_production': models.Book.objects.filter(stage__current_stage='production'),
	}

	return render(request, template, context)

# AJAX Handlers

@csrf_exempt
@login_required
def task_complete(request, task_id):

	task = get_object_or_404(models.Task, pk=task_id, assignee=request.user, completed__isnull=True)
	task.completed = timezone.now()
	task.save()
	return HttpResponse('Thanks')

@login_required
def task_new(request):

	new_task_form = forms.TaskForm(request.POST)
	if new_task_form.is_valid():
		task = new_task_form.save(commit=False)
		task.creator = request.user
		task.assignee = request.user
		task.save()

		return HttpResponse(json.dumps({'id': task.pk,'text': task.text}))
	else:
		return HttpResponse(new_task_form.errors)

@csrf_exempt
@login_required
def new_message(request, book_id):

	new_message_form = forms.MessageForm(request.POST)
	if new_message_form.is_valid():
		new_message = new_message_form.save(commit=False)
		new_message.sender = request.user
		new_message.book = get_object_or_404(models.Book, pk=book_id)
		new_message.save()

		response_dict = {
			'status_code': 200, 
			'message_id': new_message.pk,
			'sender': '%s %s' % (new_message.sender.first_name, new_message.sender.last_name),
			'message': new_message.message,
			'date_sent': str(new_message.date_sent),
		}

		return HttpResponse(json.dumps(response_dict))
	else:
		return HttpResponse(json.dumps(new_message_form.errors))

def get_authors(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        authors = models.Author.objects.filter(first_name__icontains = q )[:20]
        results = []
        for author in authors:
            author_json = {}
            author_json['id'] = author.id
            author_json['label'] = author.full_name()
            author_json['value'] = author.author_email
            results.append(author_json)
        data = json.dumps(results)
    else:
        data = 'Unable to get authors'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)



@is_book_editor
def email_authors(request,submission_id,author_id=None):
	submission = get_object_or_404(models.Book, pk=submission_id)
	to_value=""
	if request.POST:
		attachment = request.FILES.get('attachment')
		subject = request.POST.get('subject')
		body = request.POST.get('body')
		
		to_addresses = request.POST.get('to_values').split(';')
		cc_addresses = request.POST.get('cc_values').split(';')
		bcc_addresses = request.POST.get('bcc_values').split(';')

		to_list=logic.clean_email_list(to_addresses)
		cc_list=logic.clean_email_list(cc_addresses)
		bcc_list=logic.clean_email_list(bcc_addresses)
		
		if attachment: 
			attachment = handle_file(attachment, submission, 'other', request.user, "Attachment: Uploaded by %s" % (request.user.username))
		
		if to_addresses:
			if attachment: 
				send_email(subject=subject, context={}, from_email=request.user.email, to=to_list, bcc=bcc_list,cc=cc_list, html_template=body, book=submission, attachment=attachment)
			else:
				send_email(subject=subject, context={}, from_email=request.user.email, to=to_list,bcc=bcc_list,cc=cc_list, html_template=body, book=submission)
			messages.add_message(request, messages.INFO, "E-mail with subject '%s' was sent." % subject)

	if author_id:
		author = get_object_or_404(models.Author, pk=author_id)
		to_value="%s;" % (author.author_email)

	template = 'core/email_author.html'
	context = {
		'submission': submission,
		'from': request.user,
		'to_value':to_value
		
	}

	return render(request, template, context)


@is_book_editor
def upload_misc_file(request, submission_id):

	submission = get_object_or_404(models.Book, pk=submission_id)
	if request.POST:
		file_form = forms.UploadMiscFile(request.POST)
		if file_form.is_valid():
			new_file = handle_file(request.FILES.get('misc_file'), submission, file_form.cleaned_data.get('file_type'), request.user, file_form.cleaned_data.get('label'))
			submission.misc_files.add(new_file)
			return redirect(reverse('editor_submission', kwargs={'submission_id': submission.id}))
	else:
		file_form = forms.UploadMiscFile()

	template = 'core/misc_files/upload.html'
	context = {
		'submission': submission,
		'file_form': file_form,
	}

	return render(request, template, context)
@login_required
def serve_marc21_file(request, submission_id,type):
	book = get_object_or_404(models.Book, pk=submission_id)
	if type=='xml':
		file_pk=logic.book_to_mark21_file(book,request.user,True)
	else:
		file_pk=logic.book_to_mark21_file(book,request.user)
	_file = get_object_or_404(models.File, pk=file_pk)
	file_path = os.path.join(settings.BOOK_DIR, submission_id, _file.uuid_filename)

	print file_path

	try:
		fsock = open(file_path, 'r')
		mimetype = mimetypes.guess_type(file_path)
		response = StreamingHttpResponse(fsock, content_type=mimetype)
		response['Content-Disposition'] = "attachment; filename=%s" % (_file.uuid_filename)
		log.add_log_entry(book=book, user=request.user, kind='file', message='File %s downloaded.' % _file.uuid_filename, short_name='Download')
		return response
	except IOError:
		messages.add_message(request, messages.ERROR, 'File not found. %s' % (file_path))
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@is_onetasker
def serve_file(request, submission_id, file_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	file_path = os.path.join(settings.BOOK_DIR, submission_id, _file.uuid_filename)

	print file_path

	try:
		fsock = open(file_path, 'r')
		mimetype = mimetypes.guess_type(file_path)
		response = StreamingHttpResponse(fsock, content_type=mimetype)
		response['Content-Disposition'] = "attachment; filename=%s" % (_file.uuid_filename)
		log.add_log_entry(book=book, user=request.user, kind='file', message='File %s downloaded.' % _file.uuid_filename, short_name='Download')
		return response
	except IOError:
		messages.add_message(request, messages.ERROR, 'File not found. %s' % (file_path))
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@is_book_editor_or_author
def serve_versioned_file(request, submission_id, revision_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	versions_file = get_object_or_404(models.FileVersion, pk=revision_id)
	file_path = os.path.join(settings.BOOK_DIR, submission_id, versions_file.uuid_filename)

	try:
		fsock = open(file_path, 'r')
		mimetype = mimetypes.guess_type(file_path)
		response = StreamingHttpResponse(fsock, content_type=mimetype)
		response['Content-Disposition'] = "attachment; filename=%s" % (versions_file.uuid_filename)
		log.add_log_entry(book=book, user=request.user, kind='file', message='File %s downloaded.' % versions_file.uuid_filename, short_name='Download')
		return response
	except IOError:
		messages.add_message(request, messages.ERROR, 'File not found. %s/%s' % (file_path, versions_file.uuid_filename))
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@is_book_editor_or_author
def delete_file(request, submission_id, file_id, returner):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	file_id = _file.id
	_file.delete()

	if returner == 'new':
		return redirect(reverse('editor_submission', kwargs={'submission_id': book.id}))
	elif returner == 'review':
		return redirect(reverse('editor_review', kwargs={'submission_id': book.id}))
	elif returner == 'production':
		return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

@is_book_editor_or_author
def update_file(request, submission_id, file_id, returner):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	if request.POST:
		label = request.POST['rename']
		if label:
			_file.label=label
			_file.save()

		for file in request.FILES.getlist('update_file'):
			handle_file_update(file, _file, book, _file.kind, request.user)
			messages.add_message(request, messages.INFO, 'File updated.')

		if returner == 'new':
			return redirect(reverse('editor_submission', kwargs={'submission_id': book.id}))
		elif returner == 'review':
			return redirect(reverse('editor_review', kwargs={'submission_id': book.id}))
		elif returner == 'production':
			return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

	template = 'core/update_file.html'
	context = {
		'submission': book,
		'file': _file,
		'update': True
	}

	return render(request, template, context)

@is_book_editor_or_author
def view_file(request, submission_id, file_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	
	template = 'core/update_file.html'
	context = {
		'submission': book,
		'file': _file,
		'update': False
	}

	return render(request, template, context)

@is_book_editor_or_author
def versions_file(request, submission_id, file_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	versions = models.FileVersion.objects.filter(file=_file).extra(order_by = ['date_uploaded'])

	template = 'core/versions_file.html'
	context = {
		'submission': book,
		'file': _file,
		'versions': versions
	}

	return render(request, template, context)

# Log
@is_book_editor
def view_log(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	log_list = models.Log.objects.filter(book=book).order_by('-date_logged')
	email_list = models.EmailLog.objects.filter(book=book).order_by('-sent')

	template = 'editor/log.html'
	context = {
		'submission': book,
		'log_list': log_list,
		'email_list': email_list,
		'active': 'log',
	}

	return render(request, template, context)

## PROPOSALS ##

@is_editor
def proposal(request):
	proposal_list = submission_models.Proposal.objects.exclude(status='declined').exclude(status='accepted')

	template = 'core/proposals/proposal.html'
	context = {
		'proposal_list': proposal_list,
	}

	return render(request, template, context)

@is_editor
def view_proposal(request, proposal_id):
	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id)
	relationships = models.ProposalFormElementsRelationship.objects.filter(form=proposal.form)
	data = json.loads(proposal.data)

	template = 'core/proposals/view_proposal.html'
	context = {
		'proposal': proposal,
		'relationships':relationships,
		'data':data,
	}

	return render(request, template, context)

@is_editor
def start_proposal_review(request, proposal_id):
	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id, date_review_started__isnull=True)
	reviewers = models.User.objects.filter(profile__roles__slug='reviewer')
	committees = manager_models.Group.objects.filter(group_type='review_committee')
	start_form = submission_forms.ProposalStart()

	if request.POST:
		start_form = submission_forms.ProposalStart(request.POST, instance=proposal)
		if start_form.is_valid():
			proposal = start_form.save(commit=False)
			proposal.date_review_started = timezone.now()
			due_date = request.POST.get('due_date')
			email_text = models.Setting.objects.get(group__name='email', name='proposal_review_request').value
			reviewers = User.objects.filter(pk__in=request.POST.getlist('reviewer'))
			committees = manager_models.Group.objects.filter(pk__in=request.POST.getlist('committee'))

			# Handle reviewers
			for reviewer in reviewers:
				new_review_assignment = submission_models.ProposalReview(
					user=reviewer,
					proposal=proposal,
					due=due_date,
				)

				try:
					new_review_assignment.save()
					proposal.review_assignments.add(new_review_assignment)
					send_proposal_review_request(proposal, new_review_assignment, email_text)
				except IntegrityError:
					messages.add_message(request, messages.WARNING, '%s %s is already a reviewer' % (reviewer.first_name, reviewer.last_name))

			# Handle committees
			for committee in committees:
				members = manager_models.GroupMembership.objects.filter(group=committee)
				for member in members:
					new_review_assignment = submission_models.ProposalReview(
						user=member.user,
						proposal=proposal,
						due=due_date,
					)

					try:
						new_review_assignment.save()
						proposal.review_assignments.add(new_review_assignment)
						send_proposal_review_request(proposal, new_review_assignment, email_text)
					except IntegrityError:
						messages.add_message(request, messages.WARNING, '%s %s is already a reviewer' % (member.user.first_name, member.user.last_name))

			# Tidy up and save

			proposal.date_review_started = timezone.now()
			proposal.save()

			return redirect(reverse('view_proposal', kwargs={'proposal_id': proposal.id}))

	template = 'core/proposals/start_proposal_review.html'
	context = {
		'proposal': proposal,
		'start_form': start_form,
		'reviewers': reviewers,
		'committees': committees,
	}

	return render(request, template, context)

@is_editor
def view_proposal_review(request, submission_id, assignment_id):

	submission = get_object_or_404(submission_models.Proposal, pk=submission_id)
	review_assignment = get_object_or_404(submission_models.ProposalReview, pk=assignment_id)
	result = review_assignment.results
	if result:
		relations = review_models.FormElementsRelationship.objects.filter(form=result.form)
		data_ordered = logic.order_data(logic.decode_json(result.data), relations)
	else:
		relations = None
		data_ordered = None

	template = 'core/review/review_assignment.html'
	context = {
		'submission': submission,
		'review': review_assignment,
		'data_ordered': data_ordered,
		'result': result,
		'active': 'proposal_review',
	}

	return render(request, template, context)

@is_editor
def add_proposal_reviewers(request, proposal_id):

	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id)
	reviewers = models.User.objects.filter(profile__roles__slug='reviewer')
	committees = manager_models.Group.objects.filter(group_type='review_committee')

	if request.POST:
		due_date = request.POST.get('due_date')
		email_text = models.Setting.objects.get(group__name='email', name='proposal_review_request').value
		reviewers = User.objects.filter(pk__in=request.POST.getlist('reviewer'))
		committees = manager_models.Group.objects.filter(pk__in=request.POST.getlist('committee'))

		# Handle reviewers
		for reviewer in reviewers:
			new_review_assignment = submission_models.ProposalReview(
				user=reviewer,
				proposal=proposal,
				due=due_date,
			)

			try:
				new_review_assignment.save()
				proposal.review_assignments.add(new_review_assignment)
				send_proposal_review_request(proposal, new_review_assignment, email_text)
			except IntegrityError:
				messages.add_message(request, messages.WARNING, '%s %s is already a reviewer' % (reviewer.first_name, reviewer.last_name))

		# Handle committees
		for committee in committees:
			members = manager_models.GroupMembership.objects.filter(group=committee)
			for member in members:
				new_review_assignment = submission_models.ProposalReview(
					user=reviewer,
					proposal=proposal,
					due=due_date,
				)

				try:
					new_review_assignment.save()
					proposal.review_assignments.add(new_review_assignment)
					send_proposal_review_request(proposal, new_review_assignment, email_text)
				except IntegrityError:
					messages.add_message(request, messages.WARNING, '%s %s is already a reviewer' % (member.user.first_name, member.user.last_name))

		# Tidy up and save

		proposal.date_review_started = timezone.now()
		proposal.save()

		return redirect(reverse('view_proposal', kwargs={'proposal_id': proposal.id}))

	template = 'core/proposals/add_reviewers.html'
	context = {
		'proposal': proposal,
		'reviewers': reviewers,
		'committees': committees,
	}

	return render(request, template, context)

@is_editor
def decline_proposal(request, proposal_id):

	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id)
	email_text = models.Setting.objects.get(group__name='email', name='proposal_decline').value

	if request.POST:
		proposal.status = 'declined'
		logic.close_active_reviews(proposal)
		proposal.save()
		logic.send_proposal_decline(proposal, email_text=request.POST.get('decline-email'), sender=request.user)
		return redirect(reverse('proposals'))

	template = 'core/proposals/decline_proposal.html'
	context = {
		'proposal': proposal,
		'email_text': email_text,
	}

	return render(request, template, context)


@is_editor
def accept_proposal(request, proposal_id):
	'Marks a proposal as accepted, creates a submission and emails the user'
	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id)
	email_text = models.Setting.objects.get(group__name='email', name='proposal_accept').value

	if request.POST:
		proposal.status = 'accepted'
		logic.close_active_reviews(proposal)
		submission = logic.create_submission_from_proposal(proposal, proposal_type=request.POST.get('proposal-type'))
		attachment = handle_attachment(request, submission)
		logic.send_proposal_accept(proposal, email_text=request.POST.get('accept-email'), submission=submission, sender=request.user, attachment=attachment)
		proposal.save()
		return redirect(reverse('proposals'))

	template = 'core/proposals/accept_proposal.html'
	context = {
		'proposal': proposal,
		'email_text': email_text,
	}

	return render(request, template, context)

@is_editor
def request_proposal_revisions(request, proposal_id):

	proposal = get_object_or_404(submission_models.Proposal, pk=proposal_id)
	email_text = models.Setting.objects.get(group__name='email', name='proposal_request_revisisons').value

	if request.POST:
		proposal.status = 'revisions_required'
		logic.close_active_reviews(proposal)
		logic.send_proposal_revisions(proposal, email_text=request.POST.get('revisions-email'), sender=request.user)
		proposal.save()
		return redirect(reverse('proposals'))

	template = 'core/proposals/revisions_proposal.html'
	context = {
		'proposal': proposal,
		'email_text': email_text,
	}

	return render(request, template, context)

## END PROPOSAL ##

