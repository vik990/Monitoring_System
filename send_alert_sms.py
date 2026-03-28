#!/usr/bin/env python3
"""
Send SMS alert to specified phone number using Twilio.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / '.env')
except ImportError:
    print("python-dotenv not installed")

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.conf import settings
from dashboard.utils import send_sms

def main():
    # Phone number to send alert to
    target_phone = "+23058068426"
    message = "ALERT: High electricity usage detected in your household. Please check your appliances and consider reducing consumption to avoid high bills."

    print(f"Sending SMS alert to: {target_phone}")
    print(f"Message: {message}")
    print()

    # Check Twilio configuration
    if not getattr(settings, 'TWILIO_ACCOUNT_SID', None):
        print("ERROR: TWILIO_ACCOUNT_SID not configured")
        return False

    if not getattr(settings, 'TWILIO_AUTH_TOKEN', None):
        print("ERROR: TWILIO_AUTH_TOKEN not configured")
        return False

    if not getattr(settings, 'TWILIO_FROM_NUMBER', None):
        print("ERROR: TWILIO_FROM_NUMBER not configured")
        return False

    print("Twilio configuration OK")
    print(f"From: {settings.TWILIO_FROM_NUMBER}")
    print(f"To: {target_phone}")
    print()

    # Send SMS
    success = send_sms(target_phone, message)

    if success:
        print("✅ SMS sent successfully!")
        return True
    else:
        print("❌ Failed to send SMS")
        print("Note: If you're using a Twilio trial account, you need to verify the recipient phone number first.")
        print("Go to https://www.twilio.com/console/phone-numbers/verified to verify +23058068426")
        return False

if __name__ == "__main__":
    main()