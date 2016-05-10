from django.conf import settings
from sis_provisioner.management.commands import SISProvisionerCommand
from restclients.canvas.external_tools import ExternalTools
from restclients.canvas.accounts import Accounts
from restclients.exceptions import DataFailureException
from lti_manager.models import ExternalTool, ExternalToolAccount


class Command(SISProvisionerCommand):
    help = "Sync LTI Manager app with actual external tools in Canvas"

    def handle(self, *args, **options):
        self._accounts = Accounts()
        self._tools = ExternalTools()

        account = self._accounts.get_account(
            getattr(settings, 'RESTCLIENTS_CANVAS_ACCOUNT_ID'))

        self.update_tools_in_account(account)
        self.update_job()

    def update_tools_in_account(self, account):
        for tool in self._tools.get_external_tools_in_account(account_id)
            self.update_model(account, tool)

        for account in self._accounts.get_sub_accounts(account.account_id):
            self.update_tools_in_account(account)

    def update_model(self, account, config):
        canvas_id = config.id
        try:
            external_tool = ExternalTool.objects.get(canvas_id=canvas_id)
        except ExternalTool.DoesNotExist:
            external_tool = ExternalTool(canvas_id=canvas_id)

        try:
            et_account = ExternalToolAccount.objects.get(
                account_id=account.account_id)
        except ExternalToolAccount.DoesNotExist:
            et_account = ExternalToolAccount(account_id=account.account_id)
            et.sis_account_id = account.sis_account_id
            et_account.name = account.name
            et_account.save()

        external_tool.account = et_account
        external_tool.config = json.dumps(config)
        external_tool.save()
