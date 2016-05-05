from django.utils.log import getLogger
from lti_manager.models import ExternalTool, ExternalToolAccount
from lti_manager.views import can_manage_external_tools
from sis_provisioner.views.rest_dispatch import RESTDispatch
from userservice.user import UserService
from restclients.canvas.external_tools import ExternalTools
from restclients.canvas.accounts import Accounts
from restclients.exceptions import DataFailureException
from django.utils.timezone import utc
from blti.models import BLTIKeyStore
from datetime import datetime
import json
import re


logger = getLogger(__name__)


class ExternalToolView(RESTDispatch):
    """ Retrieves an ExternalTool model.
        GET returns 200 with ExternalTool details.
        PUT returns 200.
    """
    def GET(self, request, **kwargs):
        tool_id = kwargs['tool_id']
        read_only = False if can_manage_external_tools() else True
        try:
            external_tool = ExternalTool.objects.get(id=tool_id)
            data = external_tool.json_data()
            data['read_only'] = read_only

            if not read_only:
                keystore = BLTIKeyStore.objects.get(
                    consumer_key=data['consumer_key'])
                data['config']['shared_secret'] = keystore.shared_secret

        except ExternalTool.DoesNotExist:
            return self.json_response(
                '{"error":"external tool %s not found"}' % tool_id,
                status=404)
        except BLTIKeyStore.DoesNotExist:
            pass

        return self.json_response(json.dumps({'external_tool': data},
                                             sort_keys=True))

    def PUT(self, request, **kwargs):
        if not can_manage_external_tools():
            return self.json_response('{"error":"Unauthorized"}', status=401)

        tool_id = kwargs['tool_id']
        try:
            json_data = json.loads(request.body).get('external_tool', {})
            self.validate(json_data)
        except Exception as ex:
            logger.error('PUT ExternalTool error: %s' % ex)
            return self.json_response('{"error": "%s"}' % ex, status=400)

        try:
            external_tool = ExternalTool.objects.get(id=tool_id)
            curr_data = external_tool.json_data()
            keystore = BLTIKeyStore.objects.get(
                consumer_key=curr_data['consumer_key'])
        except ExternalTool.DoesNotExist:
            return self.json_response(
                '{"error":"external_tool %s not found"}' % tool_id,
                status=404)
        except BLTIKeyStore.DoesNotExist:
            keystore = BLTIKeyStore()

        # PUT does not update account_id
        external_tool.config = json.dumps(json_data['config'])
        external_tool.changed_by = UserService().get_original_user()
        external_tool.changed_date = datetime.utcnow().replace(tzinfo=utc)
        external_tool.save()

        keystore.consumer_key = json_data['config']['consumer_key']

        shared_secret = json_data['config']['shared_secret']
        if (shared_secret is None or not len(shared_secret)):
            del json_data['config']['shared_secret']
        else:
            keystore.shared_secret = shared_secret

        try:
            new_config = ExternalTools().update_external_tool_in_account(
                external_tool.account_id, json_data['config']['id'],
                json_data['config'])

            external_tool.config = json.dumps(new_config)
            external_tool.provisioned_date = datetime.utcnow().replace(
                tzinfo=utc)
            external_tool.save()
            if keystore.shared_secret:
                keystore.save()

            logger.info('%s updated External Tool "%s"' % (
                external_tool.changed_by, external_tool.id))

        except DataFailureException as err:
            return self.json_response(
                '{"error":"%s: $s"}' % (err.status, err.msg), status=500)

        return self.json_response(json.dumps({
            'external_tool': external_tool.json_data()}))

    def POST(self, request, **kwargs):
        if not can_manage_external_tools():
            return self.json_response('{"error":"Unauthorized"}', status=401)

        try:
            json_data = json.loads(request.body).get('external_tool', {})
            self.validate(json_data)
        except Exception as ex:
            logger.error('POST ExternalTool error: %s' % ex)
            return self.json_response('{"error": "%s"}' % ex, status=400)

        try:
            account_id = json_data['account_id']
            account = ExternalToolAccount.objects.get(account_id=account_id)
        except ExternalToolAccount.DoesNotExist:
            account = ExternalToolAccount(account_id=account_id)
            try:
                canvas_account = Accounts().get_account(account_id)
                account.name = canvas_account.name
                account.sis_account_id = canvas_account.sis_account_id
            except DataFailureException as ex:
                pass
            account.save()

        external_tool = ExternalTool()
        external_tool.account = account
        external_tool.config = json.dumps(json_data['config'])
        external_tool.changed_by = UserService().get_original_user()
        external_tool.changed_date = datetime.utcnow().replace(tzinfo=utc)
        external_tool.save()

        canvas_id = json_data['config']['id']
        try:
            keystore = BLTIKeyStore.objects.get(
                consumer_key=json_data['config']['consumer_key'])
            # Re-using an existing key/secret (clone?)
            json_data['config']['shared_secret'] = keystore.shared_secret

        except BLTIKeyStore.DoesNotExist:
            keystore = BLTIKeyStore()
            keystore.consumer_key = json_data['config']['consumer_key']

            shared_secret = json_data['config']['shared_secret']
            if (shared_secret is None or not len(shared_secret)):
                if canvas_id is None or not len(canvas_id):
                    # New external tool, generate a secret
                    shared_secret = external_tool.generate_shared_secret()
                    keystore.shared_secret = shared_secret
                    json_data['config']['shared_secret'] = shared_secret
                else:
                    # Existing external tool, don't overwrite the secret
                    del json_data['config']['shared_secret'] 

            keystore.save()

        try:
            if canvas_id is None or not len(canvas_id):
                new_config = ExternalTools().create_external_tool_in_account(
                    external_tool.account_id, json_data['config'])
            else:
                new_config = ExternalTools().update_external_tool_in_account(       
                    external_tool.account_id, canvas_id, json_data['config'])

            external_tool.config = json.dumps(new_config)
            external_tool.provisioned_date = datetime.utcnow().replace(
                tzinfo=utc)
            external_tool.save()

            logger.info('%s created External Tool "%s"' % (
                external_tool.changed_by, external_tool.id))

        except DataFailureException as err:
            return self.json_response(
                '{"error":"%s: $s"}' % (err.status, err.msg), status=500)

        return self.json_response(json.dumps({
            'external_tool': external_tool.json_data()}))

    def DELETE(self, request, **kwargs):
        if not can_manage_external_tools():
            return self.json_response('{"error":"Unauthorized"}', status=401)

        tool_id = kwargs['tool_id']
        try:
            external_tool = ExternalTool.objects.get(id=tool_id)
            curr_data = external_tool.json_data()
            keystore = BLTIKeyStore.objects.get(
                consumer_key=curr_data['consumer_key'])

        except ExternalTool.DoesNotExist:
            return self.json_response(
                '{"error":"external_tool %s not found"}' % tool_id, status=404)
        except BLTIKeyStore.DoesNotExist:
            keystore = None

        try:
            canvas_id = external_tool.json_data().config.id
            ExternalTools().delete_external_tool_in_account(
                external_tool.account_id, canvas_id)
            external_tool.delete()
            if keystore is not None:
                keystore.delete()

            logger.info('%s deleted ExternalTool "%s"' % (
                external_tool.changed_by, external_tool.id))

        except DataFailureException as err:
            return self.json_response(
                '{"error":"%s: $s"}' % (err.status, err.msg), status=500)

        return self.json_response(json.dumps({
            'external_tool': external_tool.json_data()}))

    def validate(self, json_data):
        re_canvas_id = re.compile(r"^\d+$")
        account_id = json_data.get('account_id', None)
        if account_id is None or not len(account_id):
            raise Exception('Subaccount ID is required')
        elif re.match(r'^\d+$', account_id) is None:
            raise Exception('Subaccount ID is invalid')

        config = json_data.get('config', {})
        name = config.get('name', None)
        if name is None or not len(name):
            raise Exception('name is required')

        privacy_level = config.get('privacy_level', None)
        if privacy_level is None or not len(privacy_level):
            raise Exception('privacy_level is required')

        consumer_key = config.get('consumer_key', None)
        if consumer_key is None or not len(consumer_key):
            raise Exception('consumer_key is required')


class ExternalToolListView(RESTDispatch):
    """ Retrieves a list of ExternalTools.
    """
    def GET(self, request, **kwargs):
        read_only = False if can_manage_external_tools() else True
        external_tools = []
        for external_tool in ExternalTool.objects.all():
            data = external_tool.json_data()
            data['read_only'] = read_only
            del data['config']
            external_tools.append(data)

        return self.json_response(
            json.dumps({'external_tools': external_tools}))
