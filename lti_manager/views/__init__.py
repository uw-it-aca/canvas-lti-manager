from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from userservice.user import UserService
from authz_group import Group


@login_required
def ManageExternalTools(request, template='lti_manager/external_tools.html'):
    user = UserService().get_original_user()
    authz = Group()
    if not authz.is_member_of_group(
            user, getattr(settings, 'CANVAS_MANAGER_ADMIN_GROUP', ''):
        return HttpResponseRedirect('/')

    return render_to_response(template, params, RequestContext(request))
