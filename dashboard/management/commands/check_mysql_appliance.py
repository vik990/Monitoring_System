from django.core.management.base import BaseCommand
import pymysql
from django.conf import settings

class Command(BaseCommand):
    help = 'Check MySQL for an appliance by name'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Appliance name to search for')

    def handle(self, *args, **options):
        name = options['name']
        mysql_cfg = settings.DATABASES.get('mysql')
        if not mysql_cfg:
            self.stderr.write(self.style.ERROR('No mysql database configured'))
            return
        try:
            conn = pymysql.connect(host=mysql_cfg['HOST'], port=int(mysql_cfg.get('PORT', 3306) or 3306), user=mysql_cfg['USER'], password=mysql_cfg['PASSWORD'], db=mysql_cfg['NAME'])
            cur = conn.cursor()
            cur.execute("SELECT id, name, resident_id FROM dashboard_appliance WHERE name=%s", (name,))
            rows = cur.fetchall()
            if rows:
                for r in rows:
                    self.stdout.write(self.style.SUCCESS(f'Found in MySQL: id={r[0]}, name={r[1]}, resident_id={r[2]}'))
            else:
                self.stdout.write(self.style.WARNING('No rows found'))
            conn.close()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'MySQL query failed: {e}'))