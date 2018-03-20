import os
from celery.schedules import crontab
from celery.task import periodic_task
import taiga.agile_statistics.stats as stats

hour = 11
minute = 44


# генерация данных для Cumulative Flow Diagram
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute)),
    name="store_daily"
)
def store_daily():
    stats.main({'command': 'store_daily'})


# store_daily()

# генерация снэпшота Cumulative Flow Diagram
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+1)),
    name="cfd"
)
def cfd():
    stats.main({'command': 'cfd'})


# cfd()

# генерация данных для User Story Dependency Graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+2)),
    name="deps_dot"
)
def deps_dot():
    stats.main({'command': 'deps_dot'})


# deps_dot()


# генерация снэпшота User Story Dependency Graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+3)),
    name="deps_gen"
)
def deps_gen():
    stats.main({'command': 'deps_gen'})
    # os.system('unflatten -l1 -c5 ./deps_dat/dependencies_8.dot | dot -T png -o ../../media/agile_stats_snapshots/dot/dependencies_8.png')


# deps_gen()

# генерация снэпшота Burnup graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+4)),
    name="burnup_gen"
)
def burnup_gen():
    stats.main({'command': 'burnup'})


# burnup_gen()

# генерация снэпшота Velocity graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+5)),
    name="velocity_gen"
)
def velocity_gen():
    stats.main({'command': 'velocity'})


# velocity_gen()
