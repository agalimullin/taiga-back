from django.contrib import admin

from . import models


admin.site.register(models.BurnupChart)
admin.site.register(models.CumulativeFlowDiagram)
admin.site.register(models.VelocityChart)
