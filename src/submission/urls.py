from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns(
    '',
    url(
        r'^book/new/stage/1/$',
        'submission.views.start_submission',
        name='submission_start',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/1/$',
        'submission.views.start_submission',
        name='edit_start',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/2/$',
        'submission.views.submission_two',
        name='submission_two'
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/3/$',
        'submission.views.submission_three',
        name='submission_three',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/4/$',
        'submission.views.submission_three_additional',
        name='submission_three_additional',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/5/$',
        'submission.views.submission_four',
        name='submission_four',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/5/author/new/$',
        'submission.views.author',
        name='author',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/5/author/(?P<author_id>\d+)/$',
        'submission.views.author',
        name='author_edit',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/5/editor/new/$',
        'submission.views.editor',
        name='editor',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/5/editor/(?P<editor_id>\d+)/$',
        'submission.views.editor',
        name='editor_edit',
    ),
    url(
        r'^book/(?P<book_id>\d+)/stage/6/$',
        'submission.views.submission_five',
        name='submission_five'),
    url(
        r'^book/(?P<book_id>\d+)/stage/3/(?P<file_type>[-\w./]+)/$',
        'submission.views.submission_additional_files',
        name='submission_additional_files',
    ),
    url(
        r'^book/(?P<book_id>\d+)/order/(?P<type_to_handle>[-\w./]+)/$',
        'submission.views.file_order',
        name='file_order',
    ),
    url(
        r'^book/(?P<book_id>\d+)/type/(?P<type_to_handle>[-\w./]+)/upload/',
        'submission.views.upload',
        name='jfu_upload',
    ),
    url(
        r'^book/(?P<book_id>\d+)/file/(?P<file_pk>\d+)/delete/$',
        'submission.views.upload_delete',
        name='jfu_delete',
    ),
    url(
        r'^proposal/$',
        'submission.views.start_proposal',
        name='proposal_start',
    ),
    url(
        r'^incomplete-proposal/(?P<proposal_id>\d+)/$',
        'submission.views.incomplete_proposal',
        name='incomplete_proposal',
    ),
    url(
        r'^incomplete-proposal/delete/(?P<proposal_id>\d+)/$',
        'submission.views.delete_incomplete_proposal',
        name='delete_incomplete_proposal',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/view/$',
        'submission.views.proposal_view',
        name='proposal_view_submitted',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/history/$',
        'submission.views.proposal_history',
        name='proposal_history_submitted',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/history/(?P<history_id>\d+)/$',
        'submission.views.proposal_history_view',
        name='proposal_history_view_submitted',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/notes/(?P<note_id>\d+)/$',
        'submission.views.proposal_notes',
        name='submission_notes_view',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/notes/update/(?P<note_id>\d+)/$',
        'submission.views.proposal_update_note',
        name='submission_notes_update',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/notes/add$',
        'submission.views.proposal_add_note',
        name='submission_notes_add',
    ),
    url(
        r'^proposal/(?P<proposal_id>\d+)/revisions/$',
        'submission.views.proposal_revisions',
        name='proposal_revisions',
    ),
)
