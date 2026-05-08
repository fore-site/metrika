import uuid
from django.conf import settings
from django.db import models

class Site(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sites',
    )
    domain = models.CharField(max_length=255)
    tracking_token = models.CharField(
        max_length=64,
        unique=True,
        default='',
        editable=False,
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