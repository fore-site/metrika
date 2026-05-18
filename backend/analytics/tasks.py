from django.core.management import call_command

def aggregate_daily_task():
    call_command('aggregate_daily')