from celery.schedules import crontab
from celery.task import periodic_task

hour = 7
minute = 4


# генерация данных для Cumulative Flow Diagram
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute)),
    name="store_daily"
)
def store_daily():
    pass
    # stats.main({'command': 'store_daily'})


# генерация снэпшота Cumulative Flow Diagram
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+1)),
    name="cfd"
)
def cfd():
    pass
    # stats.main({'command': 'cfd'})


# генерация данных для User Story Dependency Graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+2)),
    name="deps_dot"
)
def deps_dot():
    pass
    # stats.main({'command': 'deps_dot'})


# генерация снэпшота User Story Dependency Graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+3)),
    name="deps_gen"
)
def deps_gen():
    pass
    # stats.main({'command': 'deps_gen'})
    # os.system('unflatten -l1 -c5 ./deps_dat/dependencies_8.dot | dot -T png -o ../../media/agile_stats_snapshots/dot/dependencies_8.png')


# генерация снэпшота Burnup graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+4)),
    name="burnup_gen"
)
def burnup_gen():
    pass
    # stats.main({'command': 'burnup'})


# генерация снэпшота Velocity graph
@periodic_task(
    run_every=(crontab(hour=hour, minute=minute+5)),
    name="velocity_gen"
)
def velocity_gen():
    pass
    # stats.main({'command': 'velocity'})
