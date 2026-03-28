from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
import calendar

from django.db.models import Sum
from django.contrib.auth.models import User

from dashboard.models import Appliance, UsageRecord, MonthlyApplianceUsage


class Command(BaseCommand):
    help = 'Compute monthly appliance usage aggregates (year/month).'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='Year to compute (default: current year)')
        parser.add_argument('--month', type=int, help='Month to compute (1-12) (default: current month)')
        parser.add_argument('--username', type=str, help='Limit to a specific username')

    def handle(self, *args, **options):
        year = options.get('year') or timezone.now().year
        month = options.get('month') or timezone.now().month
        username = options.get('username')

        self.stdout.write(self.style.NOTICE(f'Computing monthly aggregates for {month}/{year}'))

        qs = UsageRecord.objects.filter(date__year=year, date__month=month)

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {username} not found'))
                return
            qs = qs.filter(appliance__resident__user=user)

        # Aggregate per appliance
        aggs = qs.values('appliance').annotate(total_hours=Sum('hours_used'))
        days = calendar.monthrange(year, month)[1]

        for a in aggs:
            appliance_id = a['appliance']
            total_hours = a['total_hours'] or 0.0
            try:
                appliance = Appliance.objects.get(pk=appliance_id)
            except Appliance.DoesNotExist:
                continue

            total_energy = total_hours * appliance.power_rating / 1000
            total_cost = total_energy * 5  # Use project pricing or configurable setting
            avg_daily = (total_hours / days) if days else 0
            threshold_exceeded = avg_daily > appliance.threshold_hours

            mau, created = MonthlyApplianceUsage.objects.update_or_create(
                appliance=appliance,
                year=year,
                month=month,
                defaults={
                    'user': appliance.resident.user if appliance.resident else None,
                    'resident': appliance.resident,
                    'total_hours': total_hours,
                    'total_energy_kwh': total_energy,
                    'total_cost': total_cost,
                    'avg_daily_hours': avg_daily,
                    'threshold_exceeded': threshold_exceeded,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created monthly entry for {appliance.name} {month}/{year}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated monthly entry for {appliance.name} {month}/{year}'))

        self.stdout.write(self.style.SUCCESS('Monthly aggregate computation complete.'))
