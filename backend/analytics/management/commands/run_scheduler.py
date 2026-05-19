import time
import redis
from rq_scheduler import Scheduler
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime, timedelta, timezone
import os

class Command(BaseCommand):
    help = 'Start the RQ scheduler that enqueues daily aggregation at 01:30 UTC'

    def handle(self, *args, **options):
        redis_url = settings.RQ_QUEUES['default'].get('URL', os.getenv('REDIS_URL'))
        redis_conn = redis.Redis.from_url(redis_url)
        scheduler = Scheduler(connection=redis_conn, queue_name='default')

        # Remove any previous schedule for this job (to avoid duplicates)
        scheduler.cancel('daily_aggregation')

        # Schedule the job to run at 01:30 UTC every day
        target = datetime.now(timezone.utc).replace(hour=1, minute=30, second=0, microsecond=0)
        if target < datetime.now(timezone.utc):
            target += timedelta(days=1)   # start tomorrow if it's already past

        scheduler.schedule(
            scheduled_time=target,
            func='analytics.tasks.aggregate_daily_task',
            interval=86400,        # 24 hours in seconds
            repeat=None,           # repeat indefinitely
            id='daily_aggregation',
        )

        self.stdout.write(self.style.SUCCESS(
            f'Daily aggregation scheduled. First run at {target.isoformat()} UTC.'
        ))

        while True:
            try:
                scheduler.enqueue_jobs()
            except Exception as e:
                self.stderr.write(f'Enqueue error: {e}')
            except KeyboardInterrupt:
                self.stdout.write(f'Exiting scheduler...')
            time.sleep(60)