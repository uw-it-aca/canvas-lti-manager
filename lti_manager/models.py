from django.db import models
from django.utils.timezone import utc, localtime
import datetime
import json


class ExternalTool(models.Model):
    PRIVACY_ANONYMOUS = 'anonymous'
    PRIVACY_NAMEONLY = 'name_only'
    PRIVACY_PUBLIC = 'public'
    PRIVACY_CHOICES = (
        (PRIVACY_ANONYMOUS, 'Anonymous'),
        (PRIVACY_NAMEONLY, 'Name Only'),
        (PRIVACY_PUBLIC, 'Public')
    )

    VISIBILITY_CHOICES = (
        ('admins', 'Admins'), ('members', 'Members')
    )

    account_id = models.IntegerField(max_length=15)
    config = models.CharField(max_length=2000)
    changed_by = models.CharField(max_length=32)
    changed_date = models.DateTimeField()
    provisioned_date = models.DateTimeField(null=True)

    def json_data(self):
        config = json.loads(self.config)
        return {
            'id': self.pk,
            'account_id': self.account_id,
            'name': config.get('name'),
            'config': config,
            'changed_by': self.changed_by,
            'changed_date': localtime(self.changed_date).isoformat() if (
                self.changed_date is not None) else None,
            'provisioned_date': localtime(
                self.provisioned_date).isoformat() if (
                    self.provisioned_date is not None) else None,
        }
