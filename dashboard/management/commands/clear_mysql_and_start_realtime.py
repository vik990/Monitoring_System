"""
Django management command to clear MySQL database and start real-time Tuya data capture.
Run with: python manage.py clear_mysql_and_start_realtime
"""

from django.core.management.base import BaseCommand
import time
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear MySQL database tables and start real-time Tuya data capture'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-clear',
            action='store_true',
            help='Skip clearing MySQL tables',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Capture interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== MySQL Setup & Real-time Capture ==='))
        
        # Step 1: Clear MySQL tables (if not skipped)
        if not options['no_clear']:
            self.stdout.write('Step 1: Clearing MySQL database tables...')
            if not self.clear_mysql_tables():
                self.stdout.write(self.style.ERROR('Failed to clear MySQL tables. Exiting.'))
                return
        else:
            self.stdout.write('Step 1: Skipping MySQL table clearing...')
        
        # Step 2: Create Tuya monitoring appliance
        self.stdout.write('\nStep 2: Setting up Tuya monitoring appliance...')
        appliance = self.create_tuya_monitoring_appliance()
        if not appliance:
            self.stdout.write(self.style.ERROR('Failed to create Tuya monitoring appliance. Exiting.'))
            return
        
        # Step 3: Start real-time data capture
        self.stdout.write(f'\nStep 3: Starting real-time data capture from Tuya smart plug...')
        self.stdout.write(f'Capture interval: {options["interval"]} seconds')
        self.stdout.write('Press Ctrl+C to stop capturing\n')
        
        try:
            self.capture_tuya_data(appliance, options['interval'])
        except KeyboardInterrupt:
            self.stdout.write('\n' + self.style.WARNING('Data capture stopped by user.'))
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Unexpected error: {str(e)}'))

    def clear_mysql_tables(self):
        """Clear all tables in the MySQL database."""
        try:
            import pymysql
            
            mysql_cfg = settings.DATABASES.get('mysql')
            if not mysql_cfg:
                self.stdout.write(self.style.ERROR('MySQL database configuration not found in settings'))
                return False
            
            conn = pymysql.connect(
                host=mysql_cfg.get('HOST', '127.0.0.1'),
                port=int(mysql_cfg.get('PORT', 3306)),
                user=mysql_cfg.get('USER'),
                password=mysql_cfg.get('PASSWORD'),
                db=mysql_cfg.get('NAME')
            )
            
            with conn.cursor() as cur:
                # Disable foreign key checks
                cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
                
                # Get all tables
                cur.execute("SHOW TABLES;")
                tables = cur.fetchall()
                
                # Clear all tables
                for table in tables:
                    table_name = table[0]
                    self.stdout.write(f'  Clearing table: {table_name}')
                    cur.execute(f"TRUNCATE TABLE {table_name};")
                
                # Re-enable foreign key checks
                cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            
            conn.commit()
            conn.close()
            
            self.stdout.write(self.style.SUCCESS('MySQL database tables cleared successfully'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error clearing MySQL tables: {str(e)}'))
            return False

    def create_tuya_monitoring_appliance(self):
        """Create a special appliance for Tuya monitoring."""
        try:
            from dashboard.models import Resident, Appliance, User
            
            # Get or create a default user
            user, created = User.objects.get_or_create(
                username='tuya_monitor',
                defaults={'email': 'monitor@localhost.com', 'password': 'tuya123'}
            )
            
            # Get or create a resident for Tuya monitoring
            resident, created = Resident.objects.get_or_create(
                user=user,
                profile_name='Tuya Monitoring',
                defaults={
                    'full_name': 'Tuya Smart Plug Monitor',
                    'email': 'monitor@localhost.com',
                    'is_default': True
                }
            )
            
            # Create appliance for Tuya smart plug
            appliance, created = Appliance.objects.get_or_create(
                resident=resident,
                name='Tuya Smart Plug - Live Monitoring',
                defaults={
                    'power_rating': 0.0,  # Will be updated from live data
                    'threshold_hours': 24.0,  # Monitor 24/7
                    'is_critical': True,
                    'priority_level': 3  # High priority
                }
            )
            
            if created:
                self.stdout.write(f'  Created new appliance: {appliance.name}')
            else:
                self.stdout.write(f'  Using existing appliance: {appliance.name}')
            
            return appliance
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating Tuya monitoring appliance: {str(e)}'))
            return None

    def capture_tuya_data(self, appliance, interval=60):
        """Capture real-time data from Tuya smart plug and save to database."""
        try:
            from dashboard.tuya_client import TuyaCloudClient, TuyaCredentials, extract_live_metrics
            from dashboard.models import UsageRecord
            
            # Get Tuya credentials
            creds = TuyaCredentials(
                access_id=settings.TUYA_ACCESS_ID,
                access_secret=settings.TUYA_ACCESS_SECRET,
                base_url=settings.TUYA_BASE_URL,
            )
            client = TuyaCloudClient(creds)
            
            self.stdout.write('Connected to Tuya API. Starting data capture...')
            
            capture_count = 0
            
            while True:
                try:
                    # Get live metrics from Tuya
                    status_response = client.get_device_status(settings.TUYA_DEVICE_ID)
                    live_metrics = extract_live_metrics(status_response.get('result', []))
                    
                    current_time = timezone.now()
                    current_date = current_time.date()
                    
                    # Extract data
                    power_w = live_metrics.get('power_w')
                    current_a = live_metrics.get('current_a')
                    voltage_v = live_metrics.get('voltage_v')
                    total_energy_kwh = live_metrics.get('total_energy_kwh')
                    is_on = live_metrics.get('is_on')
                    
                    # Update appliance power rating if we have power data
                    if power_w is not None and power_w > 0:
                        appliance.power_rating = power_w
                        appliance.save()
                    
                    # Create usage record for this interval
                    if power_w is not None and power_w > 0:
                        # Calculate energy for this interval
                        energy_kwh = (power_w * (interval/3600)) / 1000  # kWh for the interval
                        
                        # Create or update usage record
                        usage_record, created = UsageRecord.objects.get_or_create(
                            appliance=appliance,
                            date=current_date,
                            defaults={
                                'hours_used': interval/3600  # Convert seconds to hours
                            }
                        )
                        
                        if not created:
                            # Update existing record
                            usage_record.hours_used += interval/3600
                            usage_record.save()
                        else:
                            self.stdout.write(f'  Created new usage record for {current_date}')
                        
                        capture_count += 1
                        
                        # Log the captured data
                        self.stdout.write(f'  Capture #{capture_count}: {power_w:.2f}W, {current_a:.3f}A, {voltage_v:.1f}V, Total: {total_energy_kwh:.3f}kWh')
                        
                        # Save to MySQL database (if configured)
                        self.save_to_mysql(appliance, current_date, power_w, current_a, voltage_v, total_energy_kwh, is_on)
                    
                    else:
                        self.stdout.write(f'  No power detected or device offline')
                    
                    # Wait before next capture
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.stdout.write('Stopping data capture...')
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error during data capture: {str(e)}'))
                    time.sleep(10)  # Wait before retrying
            
            self.stdout.write(self.style.SUCCESS(f'Data capture stopped. Total captures: {capture_count}'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in Tuya data capture: {str(e)}'))
            return False

    def save_to_mysql(self, appliance, date, power_w, current_a, voltage_v, total_energy_kwh, is_on):
        """Save Tuya data to MySQL database."""
        try:
            import pymysql
            
            mysql_cfg = settings.DATABASES.get('mysql')
            if not mysql_cfg:
                return
            
            conn = pymysql.connect(
                host=mysql_cfg.get('HOST', '127.0.0.1'),
                port=int(mysql_cfg.get('PORT', 3306)),
                user=mysql_cfg.get('USER'),
                password=mysql_cfg.get('PASSWORD'),
                db=mysql_cfg.get('NAME')
            )
            
            with conn.cursor() as cur:
                # Create table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tuya_realtime_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        appliance_id INT,
                        date DATE,
                        timestamp DATETIME,
                        power_w DECIMAL(10,2),
                        current_a DECIMAL(10,3),
                        voltage_v DECIMAL(10,1),
                        total_energy_kwh DECIMAL(10,3),
                        is_on BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_appliance_date (appliance_id, date),
                        INDEX idx_timestamp (timestamp)
                    )
                """)
                
                # Insert data
                cur.execute("""
                    INSERT INTO tuya_realtime_data 
                    (appliance_id, date, timestamp, power_w, current_a, voltage_v, total_energy_kwh, is_on)
                    VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
                """, (appliance.id, date, power_w, current_a, voltage_v, total_energy_kwh, is_on))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error saving to MySQL: {str(e)}'))