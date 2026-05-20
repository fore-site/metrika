import uuid
from django.conf import settings
from django.db import models
from typing import Callable, List, Tuple
import zoneinfo

from django.utils.deconstruct import deconstructible

@deconstructible
class CachedTimezoneChoices:
    def __init__(self):
        self._choices = None

    def __call__(self):
        if self._choices is None:
            allowed_regions = ("Africa", "America", "Antarctica", "Arctic", "Asia", "Atlantic", "Australia", "Europe", "Indian", "Pacific")
            self._choices = sorted([
                (tz, tz) for tz in zoneinfo.available_timezones() 
                if tz.startswith(allowed_regions) or tz == "UTC"
            ])
        return self._choices

# Instantiate the callable
get_common_timezone_choices = CachedTimezoneChoices()

class Site(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sites',
    )
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    domain = models.CharField(max_length=255)
    tracking_token = models.CharField(
        max_length=64,
        unique=True,
        default='',
        editable=False,
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        choices=get_common_timezone_choices, #type: ignore
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'domain')
        indexes = [
            models.Index(fields=['tracking_token']),
        ]

    def __str__(self):
        return f'{self.domain} ({self.user.email})'

    def save(self, *args, **kwargs):
        if not self.tracking_token:
            self.tracking_token = uuid.uuid4().hex
        super().save(*args, **kwargs)