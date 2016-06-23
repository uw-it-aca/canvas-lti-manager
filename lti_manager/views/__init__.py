from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from userservice.user import UserService
from astra.models import AdminManager
from authz_group import Group


def can_manage_external_tools():
    return AdminManager().is_account_admin(UserService().get_original_user())


@login_required
def ManageExternalTools(request, template='lti_manager/external_tools.html'):
    user = UserService().get_original_user()
    authz = Group()
    if not authz.is_member_of_group(
            user, getattr(settings, 'CANVAS_MANAGER_ADMIN_GROUP', '')):
        return HttpResponseRedirect('/')

    params = {
        'read_only': False if can_manage_external_tools() else True,
        'canvas_host': settings.RESTCLIENTS_CANVAS_HOST
    }
    return render_to_response(template, params, RequestContext(request))
