import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
django.setup()
from dashboard.models import Resident
for r in Resident.objects.all():
    print(r.id, r.profile_name, r.email, 'default' if r.is_default else '')
