from django.db import models
from sites.models import Site

class DailySiteStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)
    visitors = models.PositiveIntegerField(default=0)
    pageviews = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date')
        ordering = ['-date']

class DailyPageStats(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_page_stats')
    date = models.DateField(db_index=True)
    path = models.TextField()
    visitors = models.PositiveIntegerField(default=0)
    pageviews = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('site', 'date', 'path')
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