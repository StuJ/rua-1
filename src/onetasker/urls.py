from django.conf.urls import url, patterns


urlpatterns = patterns(
    '',
    # Review
    url(
        r'^$',
        'onetasker.views.dashboard',
        name='onetasker_dashboard'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)$',
        'onetasker.views.task_hub',
        name='onetasker_task_hub'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)/decline/$',
        'onetasker.views.task_hub_decline',
        name='onetasker_task_hub_decline'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)/'
        r'(?P<about>[-\w]+)$',
        'onetasker.views.task_hub',
        name='onetasker_task_about'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)/'
        r'type/(?P<type_to_handle>[-\w./]+)/upload/',
        'onetasker.views.upload',
        name='assignment_jfu_upload'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)/'
        r'type/(?P<type_to_handle>[-\w./]+)/upload-author/',
        'onetasker.views.upload_author',
        name='assignment_jfu_upload_author'
    ),
    url(
        r'^(?P<assignment_type>[-\w]+)/(?P<assignment_id>\d+)/'
        r'file/(?P<file_pk>\d+)/delete/$',
        'onetasker.views.upload_delete',
        name='assignment_jfu_delete'
    ),
)
