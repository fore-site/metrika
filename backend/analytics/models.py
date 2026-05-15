from django.db import models
from sites.models import Site
from decimal import Decimal

class DailySiteStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)
    visitors = models.PositiveIntegerField(default=0)
    pageviews = models.PositiveIntegerField(default=0)
    single_page_sessions = models.PositiveIntegerField(default=0)
    total_duration_seconds = models.PositiveIntegerField(default=0, help_text="Sum of all session lengths")
    total_pageviews_in_sessions = models.PositiveIntegerField(default=0, help_text="Total no of pageviews that were part of a visit (session)")
    total_visits = models.PositiveIntegerField(default=0, help_text="Total sessions in a day")

    class Meta:
        unique_together = ('site', 'date')
        ordering = ['-date']

class DailyPageStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_page_stats')
    date = models.DateField(db_index=True)
    url = models.TextField()
    visitors = models.PositiveIntegerField(default=0)
    pageviews = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'url')
        ordering = ['-pageviews']

class DailyReferrerStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_referrer_stats')
    date = models.DateField(db_index=True)
    source = models.CharField(max_length=255)
    medium = models.CharField(max_length=50)
    visitors = models.PositiveIntegerField(default=0)
    pageviews = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'source', 'medium')
        ordering = ['-pageviews']

class DailyCountryStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_country_stats')
    date = models.DateField(db_index=True)
    country = models.CharField(max_length=100)
    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'country')
        ordering = ['-visitors']

class DailyDeviceStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_device_stats')
    date = models.DateField(db_index=True)
    device_type = models.CharField(max_length=32)
    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'device_type')
        ordering = ['-visitors']

class DailyBrowserStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_browser_stats')
    date = models.DateField(db_index=True)
    browser = models.CharField(max_length=64)
    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'browser')
        ordering = ['-visitors']

class DailyOSStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_os_stats')
    date = models.DateField(db_index=True)
    os = models.CharField(max_length=64)
    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'os')
        ordering = ['-visitors']