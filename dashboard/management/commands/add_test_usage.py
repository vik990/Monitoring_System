from django.core.management.base import BaseCommand
from dashboard.models import Resident, Appliance, UsageRecord
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create a usage record (optionally with a new appliance name) to test add_usage_record flow.'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Appliance name to use/create', required=True)
        parser.add_argument('--hours', type=float, default=1.0, help='Hours used')
        parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD)', default=None)
        parser.add_argument('--resident', type=int, help='Resident ID to associate', default=None)

    def handle(self, *args, **options):
        name = options['name']
        hours = options['hours']
        date = options['date']
        resident_id = options['resident']

        if resident_id:
            resident = Resident.objects.filter(id=resident_id).first()
        else:
            resident = Resident.objects.first()

        if not resident:
            self.stderr.write('No resident profile available to associate with appliance.')
            return

        appliance = Appliance.objects.filter(name__iexact=name, resident=resident).first()
        if not appliance:
            appliance = Appliance.objects.create(resident=resident, name=name, power_rating=100, threshold_hours=8.0)
            self.stdout.write(self.style.SUCCESS(f'Created appliance {name} id={appliance.id}'))

        if not date:
            date = timezone.now().date()

        ur = UsageRecord.objects.create(appliance=appliance, date=date, hours_used=hours)
        self.stdout.write(self.style.SUCCESS(f'Created usage record {ur.id} for appliance {appliance.id}'))
