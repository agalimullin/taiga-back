from celery.schedules import crontab
from celery.task import periodic_task
from . import services

# генерация данных статистики, графиков
stats_hour = 18
stats_minute = 0

# обновление данных геймификации
gamification_hour = 0
gamification_minute = 0


@periodic_task(
    run_every=(crontab(hour=stats_hour, minute=stats_minute)),
    name="generating_projects_stats"
)
def generating_projects_stats():
    services.update_stats_charts()


@periodic_task(
    run_every=(crontab(hour=gamification_hour, minute=gamification_minute)),
    name="gamification"
)
def generating_users_projects_activity():
    services.update_users_projects_activity()
