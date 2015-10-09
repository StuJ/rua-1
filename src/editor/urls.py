from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	# Review
    url(r'dashboard/$', 'editor.views.editor_dashboard', name='editor_dashboard'),
    url(r'^submission/(?P<submission_id>\d+)/$', 'editor.views.editor_submission', name='editor_submission'),
    url(r'^submission/(?P<submission_id>\d+)/tasks/$', 'editor.views.editor_tasks', name='editor_tasks'),
    url(r'^submission/(?P<submission_id>\d+)/status/$', 'editor.views.editor_status', name='editor_status'),

    url(r'^submission/(?P<submission_id>\d+)/review/$', 'editor.views.editor_review', name='editor_review'),
    url(r'^submission/(?P<submission_id>\d+)/review/round/(?P<round_number>\d+)/$', 'editor.views.editor_review_round', name='editor_review_round'),
    url(r'^submission/(?P<submission_id>\d+)/review/round/(?P<round_id>\d+)/assignment/(?P<review_id>\d+)/$', 'editor.views.editor_review_assignment', name='editor_review_assignment'),
    url(r'^submission/(?P<submission_id>\d+)/files/(?P<review_type>[-\w]+)/add/$', 'editor.views.add_review_files', name='add_review_files'),
    url(r'^submission/(?P<submission_id>\d+)/files/(?P<file_id>\d+)/(?P<review_type>[-\w]+)/delete/$', 'editor.views.delete_review_files', name='delete_review_files'),
    url(r'^submission/(?P<submission_id>\d+)/reviewers/(?P<review_type>[-\w]+)/add/(?P<round_number>\d+)/$', 'editor.views.editor_add_reviewers', name='editor_add_reviewers'),

    url(r'^submission/(?P<submission_id>\d+)/editing/$', 'editor.views.editor_editing', name='editor_editing'),
    url(r'^submission/(?P<submission_id>\d+)/editing/assign/copyeditor/$', 'editor.views.assign_copyeditor', name='assign_copyeditor'),
    url(r'^submission/(?P<submission_id>\d+)/editing/view/copyeditor/(?P<copyedit_id>\d+)$', 'editor.views.view_copyedit', name='view_copyedit'),
    url(r'^submission/(?P<submission_id>\d+)/editing/assign/indexer/$', 'editor.views.assign_indexer', name='assign_indexer'),
    url(r'^submission/(?P<submission_id>\d+)/editing/view/indexer/(?P<index_id>\d+)$', 'editor.views.view_index', name='view_index'),


    url(r'^submission/(?P<submission_id>\d+)/production/$', 'editor.views.editor_production', name='editor_production'),

    url(r'^submission/(?P<submission_id>\d+)/production/add/format/$', 'editor.views.add_format', name='add_format'),
    url(r'^submission/(?P<submission_id>\d+)/production/add/chapter/$', 'editor.views.add_chapter', name='add_chapter'),
    url(r'^submission/(?P<submission_id>\d+)/production/delete/(?P<format_or_chapter>[-\w]+)/(?P<id>\d+)/$', 'editor.views.delete_format_or_chapter', name='delete_format_or_chapter'),
    url(r'^submission/(?P<submission_id>\d+)/production/update/(?P<format_or_chapter>[-\w]+)/(?P<id>\d+)/$', 'editor.views.update_format_or_chapter', name='update_format_or_chapter'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/$', 'editor.views.catalog', name='catalog'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/identifiers/$', 'editor.views.identifiers', name='identifiers'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/identifiers/(?P<identifier_id>\d+)/$', 'editor.views.identifiers', name='identifiers_with_id'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/retailers/$', 'editor.views.retailers', name='retailers'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/retailers/(?P<retailer_id>\d+)/$', 'editor.views.retailers', name='retailer_with_id'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/contributor/(?P<contributor_type>[-\w]+)/(?P<contributor_id>\d+)/$', 'editor.views.update_contributor', name='update_contributor'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/contributor/(?P<contributor_type>[-\w]+)/$', 'editor.views.update_contributor', name='add_contributor'),
    url(r'^submission/(?P<submission_id>\d+)/production/catalog/contributor/(?P<contributor_type>[-\w]+)/(?P<contributor_id>\d+)/delete/$', 'editor.views.delete_contributor', name='delete_contributor'),
    url(r'^submission/(?P<submission_id>\d+)/production/assign/typesetter/$', 'editor.views.assign_typesetter', name='assign_typesetter'),\
    url(r'^submission/(?P<submission_id>\d+)/production/view/typesetter/(?P<typeset_id>\d+)$', 'editor.views.view_typesetter', name='view_typesetter'),

    url(r'^submission/(?P<submission_id>\d+)/decline/$', 'editor.views.decline_submission', name='editor_decline_submission'),
	)