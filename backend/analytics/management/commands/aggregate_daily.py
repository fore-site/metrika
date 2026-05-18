from datetime import timedelta, datetime, timezone
from django.core.management.base import BaseCommand
from sites.services import SiteService
from django.db import transaction
from django.utils import timezone as django_timezone
from common.utils import get_site_timezone
from ...services import AggregationService

class Command(BaseCommand):
    help = 'Aggregate yesterday’s analytics for all active sites'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Specific date YYYY-MM-DD (local)')
        parser.add_argument('--site', type=int, help='Aggregate only this site ID')

    def handle(self, *args, **options):
        utc_now = datetime.now(timezone.utc)

        active_sites = SiteService().get_all_active_sites()
        if options['site']:
            active_sites = active_sites.filter(id=options['site'])
            
        for site in active_sites:
            
            try:
                tz = get_site_timezone(site)
                local_now = utc_now.astimezone(tz)
                if options['date']:
                    local_yesterday = django_timezone.datetime.fromisoformat(options['date']).date()
                else:
                    local_yesterday = (local_now - timedelta(days=1)).date()
                self.stdout.write(f'Aggregating {site.domain} for {local_yesterday}')
                # Failed aggregation of one site triggers rollback and does not affect other sites
                with transaction.atomic():
                    AggregationService().aggregate_date(site, day=local_yesterday)
            except Exception as e:
                self.stderr.write(f'Aggregate failed for {site.domain}: {e}')
        self.stdout.write('Done.')