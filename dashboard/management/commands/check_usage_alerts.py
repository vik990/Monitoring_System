from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Resident, Alert
import calendar

class Command(BaseCommand):
    help = 'Check for high electricity usage and send alerts to residents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=100.0,
            help='Usage threshold in kWh for triggering alerts (default: 100.0)',
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        current_year = timezone.now().year
        current_month = timezone.now().month

        self.stdout.write(
            self.style.SUCCESS(f'Checking usage alerts for {calendar.month_name[current_month]} {current_year} (threshold: {threshold} kWh)')
        )

        residents = Resident.objects.filter(is_active=True)
        alerts_sent = 0

        for resident in residents:
            monthly_usage = resident.get_monthly_usage(current_year, current_month)

            if monthly_usage['total_energy'] >= threshold:
                # Check if alert already exists for this month
                existing_alert = Alert.objects.filter(
                    user=resident.user,
                    alert_type='HIGH_USAGE',
                    date_created__year=current_year,
                    date_created__month=current_month
                ).exists()

                if not existing_alert:
                    # Create alert in database
                    alert = Alert.objects.create(
                        user=resident.user,
                        message=f'High Usage Alert - {monthly_usage["month_name"]} {current_year}: Your electricity usage has exceeded {threshold} kWh. '
                               f'Total usage: {monthly_usage["total_energy"]} kWh, '
                               f'Estimated cost: MUR {monthly_usage["total_cost"]}. '
                               f'Please review your consumption patterns.',
                        alert_type='HIGH_USAGE',
                        is_read=False
                    )

                    # Send email alert
                    email_sent = resident.send_high_usage_alert(monthly_usage, threshold)

                    if email_sent:
                        self.stdout.write(
                            self.style.SUCCESS(f'Alert sent to {resident.full_name} ({monthly_usage["total_energy"]} kWh)')
                        )
                        alerts_sent += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Failed to send email alert to {resident.full_name}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Alert already exists for {resident.full_name} this month')
                    )
            else:
                self.stdout.write(
                    f'Usage OK for {resident.full_name}: {monthly_usage["total_energy"]} kWh'
                )

        self.stdout.write(
            self.style.SUCCESS(f'Usage alert check completed. {alerts_sent} alerts sent.')
        )