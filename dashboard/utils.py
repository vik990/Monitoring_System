from django.conf import settings

# Optional Twilio integration for SMS notifications
try:
    from twilio.rest import Client
except Exception:
    Client = None


def normalize_phone_number(phone_number: str) -> str:
    """Normalize phone number to +230 format for Mauritius."""
    if not phone_number:
        return ""
    
    # Remove all spaces and special characters
    cleaned = ''.join(c for c in phone_number if c.isdigit())
    
    # If number starts with 230 but doesn't have +, add +
    if cleaned.startswith('230') and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # If number doesn't start with +230, add +230 prefix
    elif not cleaned.startswith('+230'):
        # Remove leading 0 if present
        if cleaned.startswith('0'):
            cleaned = cleaned[1:]
        cleaned = '+230' + cleaned
    
    return cleaned

def send_sms(to_number: str, body: str) -> bool:
    """Send an SMS using Twilio if configured.

    Returns True on success, False otherwise.
    """
    if not getattr(settings, 'TWILIO_ACCOUNT_SID', None) or not getattr(settings, 'TWILIO_AUTH_TOKEN', None) or not getattr(settings, 'TWILIO_FROM_NUMBER', None):
        print('Twilio not configured; skipping SMS')
        return False

    if Client is None:
        print('Twilio SDK not installed')
        return False

    to_value = normalize_phone_number(to_number)
    if not to_value:
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=to_value
        )
        return True
    except Exception as e:
        print(f'Failed to send SMS via Twilio: {e}')
        return False


def send_whatsapp(to_number: str, body: str) -> bool:
    """Send a WhatsApp message using Twilio WhatsApp API.

    to_number can be either:
    - '+2305xxxxxxx' (we will normalize to whatsapp:+2305xxxxxxx)
    - 'whatsapp:+2305xxxxxxx'
    """
    if not getattr(settings, 'TWILIO_ACCOUNT_SID', None) or not getattr(settings, 'TWILIO_AUTH_TOKEN', None) or not getattr(settings, 'TWILIO_WHATSAPP_FROM', None):
        print('Twilio WhatsApp not configured; skipping WhatsApp send')
        return False

    if Client is None:
        print('Twilio SDK not installed')
        return False

    to_value = normalize_phone_number(to_number)
    if not to_value:
        return False
    if not to_value.startswith('whatsapp:'):
        to_value = f'whatsapp:{to_value}'

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_value,
        )
        return True
    except Exception as e:
        print(f'Failed to send WhatsApp via Twilio: {e}')
        return False


def should_send_sms_alert(appliance, hours_used, energy_kwh):
    """Determine if an SMS alert should be sent based on thresholds."""
    # Check if SMS is enabled
    if not getattr(settings, 'TWILIO_SMS_ENABLED', False):
        return False, "SMS alerts disabled"
    
    # Check energy threshold
    energy_threshold = getattr(settings, 'TWILIO_SMS_THRESHOLD_KWH', 5.0)
    if energy_kwh >= energy_threshold:
        return True, f"High energy usage: {energy_kwh:.2f} kWh"
    
    # Check hours threshold
    hours_threshold = getattr(settings, 'TWILIO_SMS_THRESHOLD_HOURS', 2.0)
    if hours_used >= hours_threshold:
        return True, f"Long usage duration: {hours_used:.1f} hours"
    
    return False, "Usage within normal limits"