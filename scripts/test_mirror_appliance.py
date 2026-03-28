import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
django.setup()
from dashboard.models import Appliance, Resident
from django.conf import settings

r = Resident.objects.filter(user__username='VIK').first() or Resident.objects.first()
name = 'AUTO_MIRROR_TEST_20260201_A'
if not Appliance.objects.filter(name=name).exists():
    a = Appliance.objects.create(resident=r, name=name, power_rating=123, threshold_hours=4.2)
    print('Created appliance', a.id)
else:
    a = Appliance.objects.get(name=name)
    print('Appliance already exists in Django, id', a.id)

mysql_cfg = settings.DATABASES.get('mysql')
conn = pymysql.connect(host=mysql_cfg['HOST'], port=int(mysql_cfg['PORT']), user=mysql_cfg['USER'], password=mysql_cfg['PASSWORD'], db=mysql_cfg['NAME'])
cur = conn.cursor()
cur.execute("SELECT id,name,resident_id FROM dashboard_appliance WHERE name=%s", (name,))
rows = cur.fetchall()
print('Rows in MySQL for', name, '=>', rows)
conn.close()