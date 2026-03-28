# MySQL Database Clearing & Real-time Tuya Data Capture Guide

## Overview

This guide provides complete instructions for clearing your MySQL database tables and setting up real-time data capture from your Tuya smart plug. The system captures live electricity consumption data and stores it in both SQLite (for Django) and MySQL databases.

## Current Status ✅

Your system is now configured for real-time data capture:

- **MySQL Database**: Tables have been cleared and are ready for new data
- **Tuya Integration**: Successfully connected and capturing data every minute
- **Data Storage**: Both SQLite and MySQL databases are being populated
- **Monitoring Appliance**: Special appliance created for Tuya smart plug monitoring

## Data Being Captured 📊

Your Tuya smart plug is currently capturing the following data in real-time:

### Live Metrics
- **Power (Watts)**: Real-time power consumption
- **Current (Amps)**: Electrical current draw
- **Voltage (Volts)**: Supply voltage
- **Total Energy (kWh)**: Cumulative energy consumption
- **Device Status**: Whether the device is on/off
- **Timestamp**: Exact time of each measurement

### Database Storage
The data is being saved to MySQL table `tuya_realtime_data` with these fields:
- `appliance_id`: Reference to the monitoring appliance
- `date`: Date of measurement
- `timestamp`: Exact datetime of measurement
- `power_w`: Power in watts (DECIMAL 10,2)
- `current_a`: Current in amps (DECIMAL 10,3)
- `voltage_v`: Voltage in volts (DECIMAL 10,1)
- `total_energy_kwh`: Cumulative energy in kWh (DECIMAL 10,3)
- `is_on`: Boolean device status
- `created_at`: Record creation timestamp

## Usage Instructions 🚀

### Option 1: Django Management Command (Recommended)

Use the Django management command for easier operation:

```bash
# Clear MySQL tables and start real-time capture
python manage.py clear_mysql_and_start_realtime

# Start capture without clearing tables (if already cleared)
python manage.py clear_mysql_and_start_realtime --no-clear

# Capture with custom interval (e.g., every 30 seconds)
python manage.py clear_mysql_and_start_realtime --interval 30
```

### Option 2: Standalone Script

Use the standalone script if you prefer:

```bash
# Clear MySQL tables and start capture
python clear_mysql_and_setup_realtime.py

# Note: This script has Unicode issues on Windows but works correctly
```

## Monitoring Your Data 📈

### Check MySQL Data

Connect to your MySQL database and run:

```sql
-- View recent captures
SELECT * FROM tuya_realtime_data ORDER BY timestamp DESC LIMIT 10;

-- View today's data
SELECT * FROM tuya_realtime_data 
WHERE date = CURDATE() 
ORDER BY timestamp DESC;

-- View summary statistics
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as readings,
    AVG(power_w) as avg_power_w,
    MAX(power_w) as max_power_w,
    MIN(power_w) as min_power_w,
    SUM(power_w * 60 / 3600000) as total_kwh  -- Assuming 60-second intervals
FROM tuya_realtime_data 
GROUP BY DATE(timestamp) 
ORDER BY date DESC;
```

### Check Django Admin

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Visit `http://127.0.0.1:8000/admin/`

3. Log in with your Django admin credentials

4. Navigate to:
   - **Dashboard → Appliances**: View the "Tuya Smart Plug - Live Monitoring" appliance
   - **Dashboard → Usage Records**: View daily usage records
   - **Dashboard → Residents**: View the monitoring resident profile

### Check Django Dashboard

1. Visit your dashboard: `http://127.0.0.1:8000/`

2. Log in with username: `VIK`, password: `VB1234`

3. View real-time data:
   - **Dashboard Home**: Shows live metrics if available
   - **Charts**: View usage trends over time
   - **Usage Records**: View detailed usage history

## Troubleshooting 🔧

### Common Issues

#### 1. MySQL Connection Errors
```bash
# Check MySQL service is running
sudo systemctl status mysql  # Linux
# or check Windows Services for MySQL

# Test MySQL connection
mysql -u root -p -h 127.0.0.1
```

#### 2. Tuya Connection Errors
- **Error**: "IP not allowed"
- **Solution**: Add your current IP to Tuya Developer Console whitelist
- **Check your IP**: Run `python test_tuya_connection.py`

#### 3. No Data Being Captured
- **Check Tuya device**: Ensure your smart plug is powered and connected
- **Check Tuya app**: Verify the device shows live data in the Tuya app
- **Check logs**: Review the `realtime_capture.log` file

#### 4. Unicode/Emoji Issues on Windows
- **Issue**: Logging errors with emojis
- **Solution**: Use Django management command instead of standalone script
- **Alternative**: The script works correctly despite logging warnings

### Log Files

- **Real-time capture log**: `realtime_capture.log`
- **Django logs**: Check your Django logging configuration
- **MySQL logs**: Check MySQL error logs if connection issues occur

## Data Analysis 📊

### Calculate Energy Consumption

```sql
-- Calculate total energy for today
SELECT 
    SUM(power_w * 60 / 3600000) as total_kwh_today
FROM tuya_realtime_data 
WHERE date = CURDATE();

-- Calculate daily averages
SELECT 
    DATE(timestamp) as date,
    AVG(power_w) as avg_power_w,
    MAX(power_w) as peak_power_w,
    SUM(power_w * 60 / 3600000) as daily_kwh
FROM tuya_realtime_data 
GROUP BY DATE(timestamp) 
ORDER BY date DESC;
```

### Export Data

```sql
-- Export to CSV
SELECT * FROM tuya_realtime_data 
INTO OUTFILE '/path/to/export/tuya_data.csv'
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

## Automation 🤖

### Run as Background Service

Create a systemd service (Linux) or Windows service to run continuously:

#### Linux (systemd)
```bash
# Create service file
sudo nano /etc/systemd/system/tuya-capture.service

# Add content:
[Unit]
Description=Tuya Real-time Data Capture
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python manage.py clear_mysql_and_start_realtime --no-clear
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable tuya-capture
sudo systemctl start tuya-capture
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "When computer starts")
4. Set action: Start a program
5. Program: `python`
6. Arguments: `manage.py clear_mysql_and_start_realtime --no-clear`
7. Start in: Your project directory

## Security Considerations 🔒

1. **Database Security**: Ensure MySQL is properly secured with strong passwords
2. **Tuya Credentials**: Store Tuya API credentials securely (use environment variables)
3. **Network Security**: Only allow necessary IP addresses in Tuya whitelist
4. **Data Privacy**: Consider data retention policies for captured electricity data

## Next Steps 🚀

1. **Monitor Data**: Let the system run for a few days to collect baseline data
2. **Analyze Patterns**: Look for usage patterns and peak consumption times
3. **Set Alerts**: Configure alerts for high consumption or unusual patterns
4. **Optimize Usage**: Use data insights to reduce electricity consumption
5. **Expand Monitoring**: Add more Tuya devices or sensors as needed

## Support 🆘

If you encounter issues:

1. **Check logs**: Review `realtime_capture.log` for detailed error messages
2. **Test connection**: Run `python test_tuya_connection.py` to verify Tuya setup
3. **Check MySQL**: Verify MySQL service is running and accessible
4. **Review documentation**: Check `TUYA_IP_CONFIGURATION_SUMMARY.md` for Tuya setup
5. **Contact support**: If issues persist, provide log files and error messages

## Files Created 📁

- `clear_mysql_and_setup_realtime.py` - Standalone script for MySQL clearing and capture
- `dashboard/management/commands/clear_mysql_and_start_realtime.py` - Django management command
- `MYSQL_REALTIME_CAPTURE_GUIDE.md` - This comprehensive guide
- `realtime_capture.log` - Log file for capture operations

Your real-time electricity monitoring system is now fully operational! 🎉