# Twilio SMS Integration and Alert Confirmation Guide

## Overview

Your Django dashboard now has advanced SMS alert capabilities with Twilio integration! The system intelligently filters alerts and provides confirmation mechanisms to ensure only important alerts are sent via SMS.

## Features Implemented ✨

### **Smart Alert Filtering**
- **Energy Threshold**: SMS alerts only when energy usage exceeds 5.0 kWh
- **Time Threshold**: SMS alerts only when usage duration exceeds 2.0 hours
- **Importance-Based**: Only high-priority alerts trigger SMS notifications

### **Multi-Channel Alert System**
1. **WhatsApp** (Primary): Fast delivery for immediate alerts
2. **SMS** (Important Alerts Only): For critical situations requiring confirmation
3. **Email** (Fallback): Traditional email notifications

### **Alert Confirmation System**
- **Dashboard Confirmation**: Confirm/dismiss alerts directly from the dashboard
- **SMS Confirmation**: Send SMS with confirmation links
- **Automatic Dismissal**: Alerts can be dismissed via URL parameters

## Configuration Setup 🔧

### **Environment Variables**

Your `.env` file now includes:

```bash
# Twilio SMS Configuration
TWILIO_SMS_ENABLED=True
TWILIO_SMS_THRESHOLD_KWH=5.0
TWILIO_SMS_THRESHOLD_HOURS=2.0

# Your Twilio Credentials (already configured)
TWILIO_ACCOUNT_SID=AC28d5d971c97d6eacaf595250f043f389
TWILIO_AUTH_TOKEN=81cb8d50bef3ea4c71484ab112bd4bd4
TWILIO_FROM_NUMBER=+15822884737
```

### **Database Models**

New models added:
- **Alert**: Enhanced with SMS, WhatsApp, and confirmation tracking
- **AlertConfirmation**: Tracks user confirmation status and method

## How It Works 🧠

### **Alert Flow Process**

1. **Alert Triggered**: High usage detected or manual alert sent
2. **Channel Selection**: 
   - WhatsApp first (if configured)
   - SMS if thresholds met and WhatsApp fails
   - Email as final fallback
3. **Confirmation Required**: Important alerts require user confirmation
4. **User Action**: User confirms or dismisses via dashboard or SMS

### **SMS Threshold Logic**

```python
def should_send_sms_alert(appliance, hours_used, energy_kwh):
    # Check if SMS is enabled
    if not TWILIO_SMS_ENABLED:
        return False, "SMS alerts disabled"
    
    # Check energy threshold (5.0 kWh default)
    if energy_kwh >= 5.0:
        return True, f"High energy usage: {energy_kwh:.2f} kWh"
    
    # Check hours threshold (2.0 hours default)
    if hours_used >= 2.0:
        return True, f"Long usage duration: {hours_used:.1f} hours"
    
    return False, "Usage within normal limits"
```

## Using the Alert System 🚀

### **Viewing Alerts**

1. **Main Dashboard**: Unread alerts shown in the sidebar
2. **Alerts Page**: Full list of all alerts
3. **Confirmation Required**: Special page for pending confirmations

### **Confirming Alerts**

#### **Via Dashboard**
1. Visit `/alert-confirmation/{alert_id}/`
2. Click "Confirm Alert" or "Dismiss Alert"
3. Alert status updated automatically

#### **Via SMS**
1. SMS sent with confirmation link: `/alert-confirmation/{alert_id}/`
2. User clicks link to view confirmation page
3. Can confirm or dismiss directly

#### **Via SMS Dismiss**
1. SMS includes dismiss link: `/alert-confirmation/{alert_id}/?action=dismiss`
2. User clicks link to automatically dismiss alert

### **Sending Manual Alerts**

1. Go to Resident Profiles
2. Click "Send Manual Alert" for any profile
3. System analyzes high-usage appliances
4. Sends alert via WhatsApp/SMS/Email based on configuration

## Alert Types and Examples 📊

### **High Usage Alerts**
```
Alert Type: HIGH_USAGE
Message: "High usage detected for Washing Machine: 3.5h (approx 2.8 kWh) - threshold 8.0h"
SMS Triggered: Yes (exceeds 2-hour threshold)
```

### **Manual Alerts**
```
Alert Type: MANUAL
Message: "Manual alert: No appliances are exceeding thresholds for profile 'Main Household'"
SMS Triggered: No (normal usage)
```

### **SMS Message Format**
```
ALERT: High Usage
Washing Machine: Long usage duration: 3.5 hours

High usage detected for Washing Machine: 3.5h (approx 2.8 kWh) - threshold 8.0h

Confirm: http://127.0.0.1:8000/alert-confirmation/123/
Dismiss: http://127.0.0.1:8000/alert-confirmation/123/?action=dismiss
```

## API Endpoints 🔌

### **Alert Management**
- `POST /confirm-alert/{id}/` - Confirm an alert
- `POST /dismiss-alert/{id}/` - Dismiss an alert
- `POST /send-sms-confirmation/{id}/` - Send SMS confirmation
- `GET /alerts-with-confirmation/` - View pending confirmations

### **Alert Status Tracking**
- `sms_sent`: Boolean indicating SMS was sent
- `whatsapp_sent`: Boolean indicating WhatsApp was sent
- `requires_confirmation`: Boolean for confirmation requirement
- `confirmed_at`: Timestamp of confirmation

## Customization Options ⚙️

### **Adjusting SMS Thresholds**

Edit your `.env` file:
```bash
# More sensitive (lower thresholds)
TWILIO_SMS_THRESHOLD_KWH=2.0
TWILIO_SMS_THRESHOLD_HOURS=1.0

# Less sensitive (higher thresholds)
TWILIO_SMS_THRESHOLD_KWH=10.0
TWILIO_SMS_THRESHOLD_HOURS=4.0
```

### **Disabling SMS Alerts**

```bash
TWILIO_SMS_ENABLED=False
```

### **Custom SMS Messages**

Modify the SMS body in `tasks.py`:
```python
sms_body = f"CUSTOM MESSAGE: {alert.alert_type.replace('_', ' ').title()}\n{alert.appliance.name}: {reason}\n\n{body[:500]}"
```

## Troubleshooting 🔍

### **Common Issues**

#### **1. SMS Not Sending**
- **Check**: Twilio credentials in `.env`
- **Check**: Phone number format (must include country code)
- **Check**: SMS enabled in settings
- **Check**: Twilio account balance

#### **2. Alerts Not Requiring Confirmation**
- **Check**: Alert has appliance associated
- **Check**: SMS thresholds are met
- **Check**: Alert type is HIGH_USAGE or CRITICAL

#### **3. Confirmation Links Not Working**
- **Check**: URLs are properly formatted
- **Check**: Alert ID exists and belongs to user
- **Check**: CSRF tokens are included in POST requests

### **Testing SMS Functionality**

1. **Test Environment Variables**:
   ```python
   from django.conf import settings
   print(settings.TWILIO_ACCOUNT_SID)
   print(settings.TWILIO_FROM_NUMBER)
   ```

2. **Test SMS Function**:
   ```python
   from dashboard.utils import send_sms
   result = send_sms('+1234567890', 'Test message from dashboard')
   print(f"SMS sent: {result}")
   ```

3. **Test Alert Creation**:
   ```python
   from dashboard.models import Alert
   alert = Alert.objects.create(
       user=request.user,
       message="Test alert",
       alert_type="HIGH_USAGE"
   )
   ```

## Security Considerations 🔒

### **SMS Security**
- **Phone Validation**: Only validated phone numbers receive SMS
- **Rate Limiting**: Built-in protection against SMS spam
- **Confirmation Required**: Important alerts require user confirmation

### **URL Security**
- **User Ownership**: Alerts can only be confirmed by the owning user
- **CSRF Protection**: All POST requests require CSRF tokens
- **URL Parameters**: Dismiss action uses safe GET parameters

## Integration with Existing Features 🔗

### **Resident Profiles**
- Each resident can have different phone numbers
- SMS alerts sent to resident's phone number
- Profile-specific alert thresholds

### **Appliance Detection**
- SMS alerts include detected appliance information
- Real-time power data shown in confirmation interface
- Usage history displayed for context

### **Charts and Analytics**
- Confirmed alerts can be excluded from usage statistics
- Alert frequency tracked for pattern analysis
- SMS delivery rates monitored

## Future Enhancements 🔮

### **Planned Features**
1. **SMS Templates**: Customizable SMS message templates
2. **Alert Scheduling**: Time-based alert restrictions
3. **Group Alerts**: Send alerts to multiple contacts
4. **Alert Escalation**: Escalate unconfirmed alerts
5. **SMS Analytics**: Track SMS delivery and response rates

### **Advanced Filtering**
1. **Machine Learning**: AI-based alert importance scoring
2. **Usage Patterns**: Learn from user confirmation behavior
3. **Time-based Rules**: Different thresholds for different times
4. **Appliance-specific**: Different rules per appliance type

## Support 🆘

### **Getting Help**
1. **Check Logs**: Review Django logs for Twilio errors
2. **Test Credentials**: Verify Twilio account status
3. **Review Configuration**: Check all environment variables
4. **Contact Support**: Provide error messages and logs

### **Monitoring**
- Monitor SMS delivery rates in Twilio console
- Track alert confirmation rates in dashboard
- Review system logs for failed deliveries
- Check database for alert status updates

## Conclusion 🎉

Your dashboard now provides intelligent SMS alerting that:

- **Filters alerts** to only send important notifications
- **Provides confirmation** to ensure alerts are acknowledged
- **Integrates seamlessly** with existing dashboard features
- **Scales easily** with configurable thresholds and settings

The system ensures users receive only the most important alerts while providing multiple ways to confirm or dismiss notifications!