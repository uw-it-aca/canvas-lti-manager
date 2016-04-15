from django.conf.urls import patterns, url, include
from lti_manager.views.api import ExternalToolView, ExternalToolListView


urlpatterns = patterns(
    'lti_manager.views',
    url(r'^$', 'ManageExternalTools'),
    url(r'api/v1/external_tool/(?P<tool_id>[0-9]+)?$', ExternalToolView().run),
    url(r'api/v1/external_tools/?$', ExternalToolListView().run),
) 
