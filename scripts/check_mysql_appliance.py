import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
django.setup()
from django.conf import settings
mysql_cfg = settings.DATABASES.get('mysql')
conn = pymysql.connect(host=mysql_cfg['HOST'], port=int(mysql_cfg['PORT']), user=mysql_cfg['USER'], password=mysql_cfg['PASSWORD'], db=mysql_cfg['NAME'])
cur = conn.cursor()
cur.execute("SELECT id,name,resident_id FROM dashboard_appliance WHERE name=%s", ('AUTO_USAGE_TEST_20260201',))
rows = cur.fetchall()
print(rows)
conn.close()