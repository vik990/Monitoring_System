from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import Appliance
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create default user VIK with password VB1234 and sample critical appliances'

    def handle(self, *args, **options):
        # Create default user
        if not User.objects.filter(username='VIK').exists():
            User.objects.create_user(username='VIK', password='VB1234')
            self.stdout.write(self.style.SUCCESS('Successfully created user VIK'))

        # Create sample critical appliances
        critical_appliances = [
            {'name': 'Air Conditioner', 'power_rating': 1500, 'threshold_hours': 8, 'is_critical': True, 'priority_level': 3},
            {'name': 'Refrigerator', 'power_rating': 200, 'threshold_hours': 24, 'is_critical': True, 'priority_level': 2},
            {'name': 'Water Heater', 'power_rating': 3000, 'threshold_hours': 4, 'is_critical': True, 'priority_level': 3},
            {'name': 'Washing Machine', 'power_rating': 800, 'threshold_hours': 2, 'is_critical': False, 'priority_level': 1},
            {'name': 'Microwave', 'power_rating': 1200, 'threshold_hours': 1, 'is_critical': False, 'priority_level': 1},
        ]

        # Create or update appliances and link to a default resident for the demo user
        demo_user = User.objects.filter(username='VIK').first()
        from dashboard.models import Resident, UsageRecord

        # Ensure a demo resident exists for the demo user
        demo_resident, _ = Resident.objects.get_or_create(
            user=demo_user,
            profile_name='Main Household',
            defaults={
                'full_name': 'Demo Household',
                'email': 'demo@example.com',
                'phone': '',
                'address': 'Demo Address',
                'household_size': 3,
                'is_default': True,
            }
        )

        for appliance_data in critical_appliances:
            appliance = Appliance.objects.filter(name=appliance_data['name']).first()
            if not appliance:
                appliance = Appliance.objects.create(
                    resident=demo_resident,
                    name=appliance_data['name'],
                    power_rating=appliance_data['power_rating'],
                    threshold_hours=appliance_data['threshold_hours'],
                    is_critical=appliance_data['is_critical'],
                    priority_level=appliance_data['priority_level'],
                )
                self.stdout.write(self.style.SUCCESS(f'Created appliance: {appliance.name}'))
            else:
                appliance.resident = demo_resident
                appliance.power_rating = appliance_data['power_rating']
                appliance.threshold_hours = appliance_data['threshold_hours']
                appliance.is_critical = appliance_data['is_critical']
                appliance.priority_level = appliance_data['priority_level']
                appliance.save()
                self.stdout.write(self.style.SUCCESS(f'Updated appliance: {appliance.name}'))

        # Create some usage records to demonstrate the system (recent days)
        today = timezone.now().date()
        sample_usage = [
            {'name': 'Air Conditioner', 'days_ago': 0, 'hours': 6},
            {'name': 'Air Conditioner', 'days_ago': 1, 'hours': 9},
            {'name': 'Refrigerator', 'days_ago': 0, 'hours': 24},
            {'name': 'Water Heater', 'days_ago': 0, 'hours': 3.5},
            {'name': 'Washing Machine', 'days_ago': 2, 'hours': 1.5},
            {'name': 'Microwave', 'days_ago': 0, 'hours': 0.2},
        ]

        for su in sample_usage:
            app = Appliance.objects.filter(name=su['name']).first()
            if app:
                record_date = today - timedelta(days=su['days_ago'])
                UsageRecord.objects.get_or_create(appliance=app, date=record_date, defaults={'hours_used': su['hours']})
                self.stdout.write(self.style.SUCCESS(f'Added usage record: {app.name} - {su["hours"]}h on {record_date}'))

        self.stdout.write(self.style.SUCCESS('Demo data created/updated.'))