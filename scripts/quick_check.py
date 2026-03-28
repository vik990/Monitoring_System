from django.test import Client
from django.contrib.auth.models import User
from dashboard.models import Resident, Appliance, UsageRecord
import datetime

# Create/cleanup test user
User.objects.filter(username='testuser').delete()
u = User.objects.create_user('testuser', 'test@example.com', 'testpass')

# Login client
c = Client()
logged_in = c.login(username='testuser', password='testpass')
print('login', logged_in)

# Create two resident profiles
Resident.objects.filter(user=u).delete()
r1 = Resident.objects.create(user=u, profile_name='Home', full_name='Home User')
r2 = Resident.objects.create(user=u, profile_name='Holiday', full_name='Holiday User')
print('profiles', list(Resident.objects.filter(user=u).values_list('profile_name', flat=True)))

# Add appliance and usage for current month
Appliance.objects.filter(resident=r1, name='Fridge').delete()
a = Appliance.objects.create(resident=r1, name='Fridge', power_rating=150, threshold_hours=8)
now = datetime.date.today()
UsageRecord.objects.filter(appliance=a, date=now).delete()
ur = UsageRecord.objects.create(appliance=a, date=now, hours_used=10)
print('usage created', ur.id)

# Fetch charts page (set HTTP_HOST so Django accepts the request)
resp = c.get('/charts/', HTTP_HOST='127.0.0.1')
print('charts_status', resp.status_code)
content = resp.content.decode()
has_label = 'Fridge' in content
print('charts_contains_label', has_label)

# Test delete resident profile via POST (include HTTP_HOST)
resp2 = c.post(f'/residents/{r2.id}/delete/', {}, follow=True, HTTP_HOST='127.0.0.1')
print('delete_status', resp2.status_code, 'redirected_to_profiles', '/residents/' in resp2.request['PATH_INFO'])
print('remaining_profiles', list(Resident.objects.filter(user=u).values_list('profile_name', flat=True)))