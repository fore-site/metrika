from datetime import date, timedelta, datetime, timezone
from django.core.management.base import BaseCommand
from sites.services import SiteService
from django.db import transaction
from common.utils import get_site_timezone
from ...services import AggregationService

class Command(BaseCommand):
    help = 'Aggregate yesterday’s analytics for all active sites'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (default: yesterday)')

    def handle(self, *args, **options):
        utc_now = datetime.now(timezone.utc)

        active_sites = SiteService().get_all_active_sites()

        for site in active_sites:
            
            try:
                tz = get_site_timezone(site)
                local_now = utc_now.astimezone(tz)
                local_yesterday = (local_now - timedelta(days=1)).date()
                self.stdout.write(f'Aggregating {site.domain} for {local_yesterday}')
                # Failed aggregation of one site triggers rollback and does not affect other sites
                with transaction.atomic():
                    AggregationService().aggregate_date(site, day=local_yesterday)
            except Exception as e:
                self.stderr.write(f'Aggregate failed for {site.domain}: {e}')
        self.stdout.write('Done.')