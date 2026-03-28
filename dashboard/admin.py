from django.contrib import admin
from .models import Resident, Appliance, UsageRecord, Alert, MonthlyApplianceUsage

admin.site.register(Resident)
admin.site.register(Appliance)
admin.site.register(UsageRecord)
admin.site.register(Alert)


@admin.register(MonthlyApplianceUsage)
class MonthlyApplianceUsageAdmin(admin.ModelAdmin):
    list_display = ('appliance', 'resident', 'user', 'year', 'month', 'total_hours', 'total_energy_kwh', 'threshold_exceeded')
    list_filter = ('year', 'month', 'threshold_exceeded')
    search_fields = ('appliance__name', 'resident__profile_name', 'user__username')
    ordering = ('-year', '-month')
