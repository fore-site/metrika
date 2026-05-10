from django.db import models

class Event(models.Model):
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='events',
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    visitor_id = models.CharField(max_length=64)
    
    url = models.URLField(max_length=2048)
    referrer = models.URLField(max_length=2048, null=True, blank=True)
    source = models.CharField(max_length=100, blank=True, default='')
    medium = models.CharField(max_length=50, blank=True, default='')

    timezone = models.CharField(max_length=64, null=True, blank=True)

    # Parsed user-agent fields
    browser = models.CharField(max_length=64, null=True, blank=True)
    os = models.CharField(max_length=64, null=True, blank=True)
    device_type = models.CharField(max_length=32, null=True, blank=True)  # desktop, mobile, tablet

    # Raw user-agent string
    user_agent = models.TextField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    continent = models.CharField(max_length=50, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    region  = models.CharField(max_length=100, blank=True, default='')
    city    = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['site', '-timestamp']),
            models.Index(fields=['visitor_id']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.site.domain} - {self.timestamp}'