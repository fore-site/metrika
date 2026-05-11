from datetime import date, timedelta
from django.core.management.base import BaseCommand
from sites.services import SiteService
from django.db import transaction
from ...services import AggregationService

class Command(BaseCommand):
    help = 'Aggregate yesterday’s analytics for all active sites'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (default: yesterday)')

    def handle(self, *args, **options):
        day = options['date']
        if day:
            target_date = date.fromisoformat(day)
        else:
            target_date = date.today() - timedelta(days=1)

        active_sites = SiteService().get_all_active_sites()

        for site in active_sites:
            self.stdout.write(f'Aggregating {site.domain} for {target_date}')
            try:
                # Failed aggregation of one site triggers rollback and does not affect other sites
                with transaction.atomic():
                    AggregationService().aggregate_date(site.id, target_date)
            except Exception as e:
                self.stderr.write(f'Aggregate failed for {site.domain}: {e}')
        self.stdout.write('Done.')