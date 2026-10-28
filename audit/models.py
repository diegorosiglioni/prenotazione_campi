from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from common.clock import now


class ActionLog(models.Model):
    """An admin action, with the values before and after it (RNF-07). Rows are never changed."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=100)
    object_id = models.BigIntegerField()
    before = models.JSONField(null=True, encoder=DjangoJSONEncoder)
    after = models.JSONField(null=True, encoder=DjangoJSONEncoder)
    created_at = models.DateTimeField(default=now)

    class Meta:
        indexes = [models.Index(fields=["object_type", "object_id"])]
