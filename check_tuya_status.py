#!/usr/bin/env python3
"""
Tuya Subscription Status Checker and Renewal Guide
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / '.env')
except ImportError:
    pass

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from dashboard.tuya_client import TuyaCloudClient, TuyaCredentials
from django.conf import settings

def check_tuya_status():
    print("🔍 TUYA SUBSCRIPTION STATUS CHECK")
    print("=" * 50)
    print(f"📱 Device ID: {settings.TUYA_DEVICE_ID}")
    print(f"🔑 Access ID: {settings.TUYA_ACCESS_ID}")
    print(f"🌐 Base URL: {settings.TUYA_BASE_URL}")
    print()

    try:
        creds = TuyaCredentials(
            access_id=settings.TUYA_ACCESS_ID,
            access_secret=settings.TUYA_ACCESS_SECRET,
            base_url=settings.TUYA_BASE_URL,
        )
        client = TuyaCloudClient(creds)

        print("📡 Testing API connection...")
        info_response = client.get_device_info(settings.TUYA_DEVICE_ID)
        print("✅ SUCCESS: Tuya subscription is active!")
        print("🎉 Your live measurements should be working.")
        return True

    except Exception as e:
        error_msg = str(e)
        if '28841002' in error_msg:
            print("❌ SUBSCRIPTION EXPIRED")
            print("   Your Tuya Cloud Development Plan has expired.")
            print()
            print("🔧 SOLUTIONS:")
            print("   1. Go to https://iot.tuya.com/")
            print("   2. Login to your developer account")
            print("   3. Go to 'Cloud' → 'Development'")
            print("   4. Find your project and renew the subscription")
            print("   5. Or upgrade to a paid plan")
            print()
            print("💡 ALTERNATIVES:")
            print("   • Use manual data entry for now")
            print("   • Switch to local energy monitoring")
            print("   • Deploy to Vercel for production use")
            return False
        else:
            print(f"❌ CONNECTION ERROR: {error_msg}")
            return False

def show_renewal_steps():
    print("\n📋 TUYA SUBSCRIPTION RENEWAL STEPS:")
    print("=" * 50)
    print("1. Visit: https://iot.tuya.com/")
    print("2. Sign in with your developer account")
    print("3. Navigate to: Cloud → Development")
    print("4. Select your project")
    print("5. Click 'Renew' or 'Upgrade Plan'")
    print("6. Choose a subscription plan:")
    print("   • Free Trial: Limited, expires")
    print("   • Developer Plan: ~$10/month")
    print("   • Enterprise Plan: Higher limits")
    print("7. Complete payment")
    print("8. Wait 5-10 minutes for activation")
    print("9. Test your dashboard - live data should work!")

if __name__ == "__main__":
    status = check_tuya_status()
    if not status:
        show_renewal_steps()
        print("\n💡 In the meantime, your dashboard shows sample data in 'Demo Mode'")
        print("   This allows you to test all features while waiting for renewal.")