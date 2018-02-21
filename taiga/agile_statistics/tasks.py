from celery.schedules import crontab
from celery.task import periodic_task
import taiga.agile_statistics.stats as stats


@periodic_task(
    run_every=(crontab(hour=10, minute=30)),
    name="store_daily"
)
def store_daily():
    stats.main({'command': 'store_daily'})


@periodic_task(
    run_every=(crontab(hour=10, minute=30)),
    name="cfd"
)
def cfd():
    stats.main({'command': 'cfd'})


def deps_dot():
    stats.main({'command': 'deps_dot'})
