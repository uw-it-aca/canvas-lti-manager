from django.conf.urls import patterns, url, include
from lti_manager.views.api import ExternalToolView, ExternalToolListView


urlpatterns = patterns(
    '',
    url(r'^$', 'lti_manager.views.ManageExternalTools'),
    url(r'api/v1/external_tool/(?P<tool_id>[0-9]+)?$', ExternalToolView().run),
    url(r'api/v1/external_tools/?$', ExternalToolListView().run),
) 
