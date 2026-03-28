#!/usr/bin/env python3
"""
Script to clear MySQL database tables and set up real-time data capture from Tuya smart plug.
Run this script to reset your MySQL database and start capturing live data.
"""

import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')

# Setup Django
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clear_mysql_tables():
    """Clear all tables in the MySQL database."""
    logger.info("🧹 Clearing MySQL database tables...")
    
    try:
        import pymysql
        from django.conf import settings
        
        mysql_cfg = settings.DATABASES.get('mysql')
        if not mysql_cfg:
            logger.error("❌ MySQL database configuration not found in settings")
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
                logger.info(f"  🗑️  Clearing table: {table_name}")
                cur.execute(f"TRUNCATE TABLE {table_name};")
            
            # Re-enable foreign key checks
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ MySQL database tables cleared successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing MySQL tables: {str(e)}")
        return False

def create_tuya_monitoring_appliance():
    """Create a special appliance for Tuya monitoring."""
    logger.info("🔌 Setting up Tuya monitoring appliance...")
    
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
            logger.info(f"  ✅ Created new appliance: {appliance.name}")
        else:
            logger.info(f"  📝 Using existing appliance: {appliance.name}")
        
        return appliance
        
    except Exception as e:
        logger.error(f"❌ Error creating Tuya monitoring appliance: {str(e)}")
        return None

def capture_tuya_data():
    """Capture real-time data from Tuya smart plug and save to database."""
    logger.info("📡 Starting real-time Tuya data capture...")
    
    try:
        from dashboard.tuya_client import TuyaCloudClient, TuyaCredentials, extract_live_metrics
        from dashboard.models import UsageRecord, Appliance
        from django.utils import timezone
        from dashboard.tariffs import calculate_tariff_cost
        
        # Get Tuya credentials
        from django.conf import settings
        creds = TuyaCredentials(
            access_id=settings.TUYA_ACCESS_ID,
            access_secret=settings.TUYA_ACCESS_SECRET,
            base_url=settings.TUYA_BASE_URL,
        )
        client = TuyaCloudClient(creds)
        
        # Get the Tuya monitoring appliance
        appliance = Appliance.objects.filter(
            name='Tuya Smart Plug - Live Monitoring'
        ).first()
        
        if not appliance:
            logger.error("❌ Tuya monitoring appliance not found. Run setup first.")
            return False
        
        logger.info("📡 Connected to Tuya API. Starting data capture...")
        logger.info("Press Ctrl+C to stop capturing")
        
        capture_count = 0
        last_power = None
        
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
                
                # Create usage record for this minute/hour
                if power_w is not None and power_w > 0:
                    # Calculate energy for this interval (assuming 1-minute intervals)
                    energy_kwh = (power_w * (1/60)) / 1000  # kWh for 1 minute
                    
                    # Create or update usage record
                    usage_record, created = UsageRecord.objects.get_or_create(
                        appliance=appliance,
                        date=current_date,
                        defaults={
                            'hours_used': 1/60  # 1 minute
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        usage_record.hours_used += 1/60
                        usage_record.save()
                    else:
                        logger.info(f"  📊 Created new usage record for {current_date}")
                    
                    capture_count += 1
                    
                    # Log the captured data
                    logger.info(f"  📈 Capture #{capture_count}: {power_w:.2f}W, {current_a:.3f}A, {voltage_v:.1f}V, Total: {total_energy_kwh:.3f}kWh")
                    
                    # Save to MySQL database (if configured)
                    save_to_mysql(appliance, current_date, power_w, current_a, voltage_v, total_energy_kwh, is_on)
                
                else:
                    logger.info(f"  ⏸️  No power detected or device offline")
                
                # Wait 60 seconds before next capture
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping data capture...")
                break
            except Exception as e:
                logger.error(f"❌ Error during data capture: {str(e)}")
                time.sleep(10)  # Wait before retrying
        
        logger.info(f"✅ Data capture stopped. Total captures: {capture_count}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in Tuya data capture: {str(e)}")
        return False

def save_to_mysql(appliance, date, power_w, current_a, voltage_v, total_energy_kwh, is_on):
    """Save Tuya data to MySQL database."""
    try:
        import pymysql
        from django.conf import settings
        
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
        logger.error(f"❌ Error saving to MySQL: {str(e)}")

def main():
    """Main function to run the setup and data capture."""
    print("🏠 Electricity Monitor Dashboard - MySQL Setup & Real-time Capture")
    print("=" * 70)
    print()
    
    # Step 1: Clear MySQL tables
    print("Step 1: Clearing MySQL database tables...")
    if not clear_mysql_tables():
        print("❌ Failed to clear MySQL tables. Exiting.")
        return
    
    # Step 2: Create Tuya monitoring appliance
    print("\nStep 2: Setting up Tuya monitoring appliance...")
    appliance = create_tuya_monitoring_appliance()
    if not appliance:
        print("❌ Failed to create Tuya monitoring appliance. Exiting.")
        return
    
    # Step 3: Start real-time data capture
    print("\nStep 3: Starting real-time data capture from Tuya smart plug...")
    print("📡 This will capture live data every minute and save to both SQLite and MySQL databases.")
    print()
    
    try:
        capture_tuya_data()
    except KeyboardInterrupt:
        print("\n🛑 Data capture stopped by user.")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()