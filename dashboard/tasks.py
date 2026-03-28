from celery import shared_task
import logging
import pymysql
from django.conf import settings
from django.utils import timezone

from .models import Alert, Resident
from .utils import send_whatsapp, send_sms, should_send_sms_alert

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def mirror_appliance_task(self, appliance_id, name, resident_id, power_rating, threshold_hours, is_critical, priority_level):
    """Background task to upsert appliance into the MySQL database."""
    mysql_cfg = settings.DATABASES.get('mysql')
    if not mysql_cfg:
        logger.warning('mirror_appliance_task: no mysql configuration found')
        return False

    try:
        host = mysql_cfg.get('HOST', '127.0.0.1')
        port = int(mysql_cfg.get('PORT', 3306) or 3306)
        user = mysql_cfg.get('USER')
        password = mysql_cfg.get('PASSWORD')
        db = mysql_cfg.get('NAME')

        conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8mb4')
        cur = conn.cursor()
        upsert_sql = """
            INSERT INTO `dashboard_appliance` (`resident_id`, `name`, `power_rating`, `threshold_hours`, `is_critical`, `priority_level`, `created_at`, `updated_at`)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                power_rating=VALUES(power_rating),
                threshold_hours=VALUES(threshold_hours),
                is_critical=VALUES(is_critical),
                priority_level=VALUES(priority_level),
                updated_at=VALUES(updated_at);
        """
        cur.execute(upsert_sql, (
            resident_id,
            name,
            power_rating,
            threshold_hours,
            1 if is_critical else 0,
            priority_level,
        ))
        conn.commit()
        conn.close()
        logger.info(f'mirror_appliance_task: upserted appliance {name} (id={appliance_id})')
        return 
        
    except Exception as e:
        logger.exception(f'mirror_appliance_task failed for {name}: {e}')
        return False


@shared_task(bind=True)
def dispatch_alert_notification_task(self, alert_id, resident_id=None):
    """Send alert via WhatsApp first, then SMS, then fallback to email."""
    try:
        alert = Alert.objects.select_related('user').get(pk=alert_id)
    except Alert.DoesNotExist:
        logger.warning(f'dispatch_alert_notification_task: alert {alert_id} not found')
        return {'success': False, 'reason': 'alert_not_found'}

    resident = None
    if resident_id:
        resident = Resident.objects.filter(pk=resident_id, user=alert.user).first()
    if resident is None:
        resident = Resident.objects.filter(user=alert.user, is_default=True).first() or Resident.objects.filter(user=alert.user, is_active=True).first()

    if resident is None:
        logger.warning(f'dispatch_alert_notification_task: no resident profile for alert {alert_id}')
        return {'success': False, 'reason': 'resident_not_found'}

    subject = f"Electricity Alert - {alert.alert_type.replace('_', ' ').title()}"
    body = alert.message

    # 1) WhatsApp (preferred for speed)
    try:
        if resident.phone and send_whatsapp(resident.phone, f"{subject}\n\n{body[:1000]}"):
            alert.email_sent = True
            alert.save(update_fields=['email_sent'])
            return {'success': True, 'channel': 'whatsapp'}
    except Exception as e:
        logger.exception(f'WhatsApp send failed for alert {alert_id}: {e}')

    # 2) SMS (for important alerts only)
    try:
        if resident.phone and alert.appliance:
            # Check if this alert meets SMS criteria
            should_send, reason = should_send_sms_alert(alert.appliance, alert.appliance.threshold_hours, alert.appliance.power_rating / 1000 * alert.appliance.threshold_hours)
            if should_send:
                sms_body = f"ALERT: {alert.alert_type.replace('_', ' ').title()}\n{alert.appliance.name}: {reason}\n\n{body[:500]}"
                if send_sms(resident.phone, sms_body):
                    Alert.objects.filter(pk=alert_id).update(sms_sent=True)
                    return {'success': True, 'channel': 'sms'}
    except Exception as e:
        logger.exception(f'SMS send failed for alert {alert_id}: {e}')

    # 3) Email fallback
    try:
        if resident.email and resident.send_alert(subject, body):
            alert.email_sent = True
            alert.save(update_fields=['email_sent'])
            return {'success': True, 'channel': 'email'}
    except Exception as e:
        logger.exception(f'Email fallback failed for alert {alert_id}: {e}')

    return {'success': False, 'reason': 'all_channels_failed'}
