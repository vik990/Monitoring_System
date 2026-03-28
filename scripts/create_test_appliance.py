import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
django.setup()
from dashboard.models import Appliance, Resident

r = Resident.objects.filter(user__username='VIK').first() or Resident.objects.first()
a = Appliance.objects.create(resident=r, name='AUTO_MIRROR_TEST_20260201', power_rating=555, threshold_hours=3.5)
print('Created appliance id:', a.id, 'name:', a.name)
