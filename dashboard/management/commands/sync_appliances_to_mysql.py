import pymysql
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import Appliance
from django.utils import timezone


class Command(BaseCommand):
    help = 'Sync existing Appliance rows into the configured MySQL database (appliances table)'

    def handle(self, *args, **options):
        mysql_cfg = settings.DATABASES.get('mysql')
        if not mysql_cfg:
            self.stderr.write(self.style.ERROR('No mysql database configured in settings.DATABASES'))
            return

        host = mysql_cfg.get('HOST', '127.0.0.1')
        port = int(mysql_cfg.get('PORT', 3306) or 3306)
        user = mysql_cfg.get('USER')
        password = mysql_cfg.get('PASSWORD')
        db = mysql_cfg.get('NAME')

        conn = None
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8mb4')
            cur = conn.cursor()

            # Ensure table exists (simple schema compatible with Django model fields used)
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `dashboard_appliance` (
                `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `resident_id` INT NULL,
                `name` VARCHAR(100) NOT NULL,
                `power_rating` DOUBLE NOT NULL DEFAULT 0,
                `threshold_hours` DOUBLE NOT NULL DEFAULT 8,
                `is_critical` TINYINT(1) NOT NULL DEFAULT 0,
                `priority_level` TINYINT(1) NOT NULL DEFAULT 1,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uniq_resident_name` (`resident_id`, `name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cur.execute(create_table_sql)
            conn.commit()

            upsert_sql = f"""
            INSERT INTO `dashboard_appliance` (`resident_id`, `name`, `power_rating`, `threshold_hours`, `is_critical`, `priority_level`, `created_at`, `updated_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                power_rating=VALUES(power_rating),
                threshold_hours=VALUES(threshold_hours),
                is_critical=VALUES(is_critical),
                priority_level=VALUES(priority_level),
                updated_at=VALUES(updated_at);
            """

            appliances = Appliance.objects.all()
            if not appliances:
                self.stdout.write('No appliances found in the default DB to sync.')
                return

            inserted = 0
            for a in appliances:
                resident_id = a.resident.id if a.resident else None
                now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                try:
                    cur.execute(upsert_sql, (
                        resident_id,
                        a.name,
                        a.power_rating,
                        a.threshold_hours,
                        1 if a.is_critical else 0,
                        a.priority_level,
                        now,
                        now,
                    ))
                    inserted += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Failed to upsert appliance {a.id} {a.name}: {e}'))

            conn.commit()
            self.stdout.write(self.style.SUCCESS(f'Synced {inserted} appliances to MySQL database `{db}`'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'MySQL connection or operation failed: {e}'))

        finally:
            if conn:
                conn.close()