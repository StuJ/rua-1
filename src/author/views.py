from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib import messages

from core import models, log, task
from author import forms
from author import logic
from workflow.logic import order_data, decode_json
from submission import models as submission_models
from revisions import models as revision_models, forms as revision_forms
from review import models as review_models
from workflow.views import handle_file_update
from copyedit import forms as copyedit_forms
from copyedit.views import handle_copyedit_file
from typeset import forms as typeset_forms
from typeset.views import handle_typeset_file

@login_required
def author_dashboard(request):

	template = 'author/dashboard.html'
	context = {
		'user_submissions': models.Book.objects.filter(owner=request.user),
		'user_proposals': submission_models.Proposal.objects.filter(owner=request.user),
		'author_tasks': logic.author_tasks(request.user),
	}

	return render(request, template, context)

@login_required
def author_submission(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	template = 'author/submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
		'author_include': 'author/submission_details.html',
		'submission_files': 'author/submission_files.html'
	}

	return render(request, template, context)

@login_required
def status(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	template = 'author/submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
		'author_include': 'author/status.html',
		'submission_files': 'shared/messages.html',
		'timeline': logic.build_time_line(book),
	}

	return render(request, template, context)

@login_required
def review(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	review_rounds = models.ReviewRound.objects.filter(book=book).order_by('-round_number')
	
	template = 'author/submission.html'
	context = {
		'submission': book,
		'author_include': 'author/review_revision.html',
		'review_rounds': review_rounds,
		'revision_requests': revision_models.Revision.objects.filter(book=book, revision_type='review')
	}

	return render(request, template, context)

@login_required
def view_review_round(request, submission_id, round_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)
	review_round = get_object_or_404(models.ReviewRound, book=book, round_number=round_id)
	reviews = models.ReviewAssignment.objects.filter(book=book, review_round__book=book, review_round__round_number=round_id)

	review_rounds = models.ReviewRound.objects.filter(book=book).order_by('-round_number')
	internal_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='internal', review_round__round_number=round_id).select_related('user', 'review_round')
	external_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='external', review_round__round_number=round_id).select_related('user', 'review_round')

	template = 'author/submission.html'
	context = {
		'submission': book,
		'author_include': 'author/review_revision.html',
		'submission_files': 'author/view_review_round.html',
		'review_round': review_round,
		'review_rounds': review_rounds,
		'round_id': round_id,
		'revision_requests': revision_models.Revision.objects.filter(book=book, revision_type='review'),
		'internal_review_assignments': internal_review_assignments,
		'external_review_assignments': external_review_assignments,
	}

	return render(request, template, context)

@login_required
def view_review_assignment(request, submission_id, round_id, review_id):

	submission = get_object_or_404(models.Book, pk=submission_id, owner=request.user)
	review_assignment = get_object_or_404(models.ReviewAssignment, pk=review_id)
	review_rounds = models.ReviewRound.objects.filter(book=submission).order_by('-round_number')
	result = review_assignment.results
	relations = review_models.FormElementsRelationship.objects.filter(form=result.form)
	data_ordered = order_data(decode_json(result.data), relations)

	template = 'author/submission.html'
	context = {
		'author_include': 'author/review_revision.html',
		'submission_files': 'shared/view_review.html',
		'submission': submission,
		'review': review_assignment,
		'data_ordered': data_ordered,
		'result': result,
		'active': 'review',
		'review_rounds': review_rounds,
		'revision_requests': revision_models.Revision.objects.filter(book=submission, revision_type='review'),
	}

	return render(request, template, context)

@login_required
def tasks(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	template = 'author/submission.html'
	context = {
		'submission': book,
		'tasks': logic.submission_tasks(book, request.user),
		'author_include': 'author/tasks.html',
	}

	return render(request, template, context)

@login_required

def view_revisions(request, submission_id, revision_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)
	revision = get_object_or_404(revision_models.Revision, pk=revision_id, completed__isnull=False, book=book)

	review_rounds = models.ReviewRound.objects.filter(book=book).order_by('-round_number')

	template = 'author/submission.html'
	context = {
		'revision': revision,
		'submission': book,
		'author_include': 'author/review_revision.html',
		'submission_files': 'author/view_revision.html',
		'update': False,
		'review_rounds': review_rounds,
		'revision_requests': revision_models.Revision.objects.filter(book=book, revision_type='review')
	}

	return render(request, template, context)

@login_required
def revision(request, revision_id, submission_id):
	revision = get_object_or_404(revision_models.Revision, pk=revision_id, book__owner=request.user, completed__isnull=True)
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	form = revision_forms.AuthorRevisionForm(instance=revision)

	if request.POST:
		form = revision_forms.AuthorRevisionForm(request.POST, instance=revision)
		if form.is_valid():
			revision = form.save(commit=False)
			revision.completed = timezone.now()
			revision.save()
			task = models.Task(book=revision.book, creator=request.user, assignee=revision.requestor, text='Revisions submitted for %s' % revision.book.title, workflow=revision.revision_type, )
			task.save()
			messages.add_message(request, messages.SUCCESS, 'Revisions recorded, thanks.')
			return redirect(reverse('author_dashboard'))

	template = 'author/submission.html'
	context = {
		'submission': book,
		'revision': revision,
		'form': form,
		'author_include': 'author/revision.html',
	}

	return render(request, template, context)

@login_required
def revise_file(request, submission_id, revision_id, file_id):
	revision = get_object_or_404(revision_models.Revision, pk=revision_id, book__owner=request.user)
	book = revision.book
	_file = get_object_or_404(models.File, pk=file_id)
	form = revision_forms.AuthorRevisionForm(instance=revision)

	if request.POST:
		for file in request.FILES.getlist('update_file'):
			handle_file_update(file, _file, book, _file.kind, request.user)
			messages.add_message(request, messages.INFO, 'File updated.')

		return redirect(reverse('author_revision', kwargs={'submission_id': submission_id, 'revision_id': revision.id}))

	template = 'author/submission.html'
	context = {
		'submission': book,
		'revision': revision,
		'file': _file,
		'author_include': 'author/revision.html',
		'submission_files': 'author/revise_file.html',
		'form': form,
	}

	return render(request, template, context)

@login_required
def editing(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)

	template = 'author/submission.html'
	context = {
		'submission': book,
		'author_include': 'author/editing.html',
	}

	return render(request, template, context)

@login_required
def copyedit_review(request, submission_id, copyedit_id):
	book = get_object_or_404(models.Book, pk=submission_id, owner=request.user)
	copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id, book__owner=request.user, book=book)

	form = copyedit_forms.CopyeditAuthor(instance=copyedit)

	if request.POST:
		form = copyedit_forms.CopyeditAuthor(request.POST, instance=copyedit)
		if form.is_valid():
			form.save()
			for _file in request.FILES.getlist('copyedit_file_upload'):
				new_file = handle_copyedit_file(_file, book, copyedit, 'copyedit')
				copyedit.author_files.add(new_file)

			copyedit.author_completed = timezone.now()
			copyedit.save()
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Copyedit Author review compeleted by %s %s.' % (request.user.first_name, request.user.last_name), short_name='Copyedit Author Review Complete')
			messages.add_message(request, messages.SUCCESS, 'Copyedit task complete. Thanks.')
			new_task = task.create_new_task(book, copyedit.book.owner, copyedit.requestor, "Author Copyediting completed for %s" % book.title, workflow='editing')
			return redirect(reverse('editing', kwargs={"submission_id": submission_id,}))

	template = 'author/submission.html'
	context = {
		'submission': book,
		'copyedit': copyedit,
		'author_include': 'author/copyedit.html',
		'submission_files': 'author/copyedit_review.html',
		'form': form,
	}

	return render(request, template, context)

@login_required
def typeset_review(request, submission_id, typeset_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	typeset = get_object_or_404(models.TypesetAssignment, pk=typeset_id, book__owner=request.user, book=book)

	form = typeset_forms.TypesetAuthor(instance=typeset)

	if request.POST:
		form = typeset_forms.TypesetAuthor(request.POST, instance=typeset)
		if form.is_valid():
			form.save()
			for _file in request.FILES.getlist('typeset_file_upload'):
				new_file = handle_typeset_file(_file, book, typeset, 'typeset')
				typeset.author_files.add(new_file)

			typeset.author_completed = timezone.now()
			typeset.save()
			log.add_log_entry(book=book, user=request.user, kind='production', message='Author Typesetting review %s %s completed.' % (request.user.first_name, request.user.last_name), short_name='Author Typesetting Review Completed')
			messages.add_message(request, messages.SUCCESS, 'Typesetting task complete. Thanks.')
			new_task = task.create_new_task(book, typeset.book.owner, typeset.requestor, "Author Typesetting completed for %s" % book.title, workflow='production')
			return redirect(reverse('editing', kwargs={"submission_id": submission_id,}))

	template = 'author/submission.html'
	context = {
		'submission': book,
		'typeset': typeset,
		'author_include': 'author/typeset.html',
		'submission_files': 'author/typeset_review.html',
		'form': form,
	}

	return render(request, template, context)

@login_required
def author_contract_signoff(request, submission_id, contract_id):
	contract = get_object_or_404(models.Contract, pk=contract_id)
	submission = get_object_or_404(models.Book, pk=submission_id, owner=request.user, contract=contract)

	if request.POST:
		author_signoff_form = forms.AuthorContractSignoff(request.POST, request.FILES)
		if author_signoff_form.is_valid():
			if request.FILES.get('author_file'):
				author_file = request.FILES.get('author_file')
				new_file = handle_file(author_file, submission, 'contract')
				contract.author_file = new_file

			contract.author_signed_off = timezone.now()
			contract.save()
			return redirect(reverse('author_submission', kwargs={'submission_id': submission_id}))
	else:
		author_signoff_form = forms.AuthorContractSignoff()

	template = 'author/author_contract_signoff.html'
	context = {
		'submission': 'submission',
		'contract': 'contract',
		'author_signoff_form': 'author_signoff_form',
	}

	return render(request, template, context)
