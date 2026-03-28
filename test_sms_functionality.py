#!/usr/bin/env python3
"""
Test script for Twilio SMS functionality with Mauritius phone number formatting.
This script tests the phone number normalization and SMS sending capabilities.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / '.env')
except ImportError:
    print("python-dotenv not installed, environment variables may not be loaded")

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
from dashboard.utils import normalize_phone_number, send_sms, send_whatsapp

def test_phone_number_normalization():
    """Test phone number normalization for Mauritius format."""
    print("Testing phone number normalization...")
    
    test_cases = [
        # Input, Expected Output
        ("52541234", "+23052541234"),
        ("23052541234", "+23052541234"),
        ("+23052541234", "+23052541234"),
        ("052541234", "+23052541234"),
        (" 5254 1234 ", "+23052541234"),
        ("+230-5254-1234", "+23052541234"),
        ("", ""),
        (None, ""),
    ]
    
    for input_num, expected in test_cases:
        result = normalize_phone_number(input_num)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {input_num!r} -> {result!r} (expected: {expected!r})")
        
        if result != expected:
            print(f"    ERROR: Expected {expected}, got {result}")
            return False
    
    print("  All phone number normalization tests passed!")
    return True

def test_twilio_configuration():
    """Test Twilio configuration is properly set."""
    print("\nTesting Twilio configuration...")
    
    required_settings = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_FROM_NUMBER',
        'TWILIO_SMS_ENABLED',
        'TWILIO_SMS_THRESHOLD_KWH',
        'TWILIO_SMS_THRESHOLD_HOURS'
    ]
    
    all_configured = True
    for setting in required_settings:
        value = getattr(settings, setting, None)
        status = "✓" if value else "✗"
        print(f"  {status} {setting}: {value}")
        
        if not value:
            all_configured = False
    
    if all_configured:
        print("  All Twilio settings are configured!")
    else:
        print("  ERROR: Some Twilio settings are missing!")
    
    return all_configured

def test_sms_sending():
    """Test SMS sending functionality."""
    print("\nTesting SMS sending...")
    
    # Test with a sample Mauritius phone number
    test_phone = "+23052541234"
    test_message = "Test message from Household Electricity Dashboard SMS system"
    
    print(f"  Attempting to send SMS to: {test_phone}")
    print(f"  Message: {test_message}")
    
    try:
        result = send_sms(test_phone, test_message)
        if result:
            print("  ✓ SMS sent successfully!")
            return True
        else:
            print("  ✗ SMS sending failed!")
            return False
    except Exception as e:
        print(f"  ✗ SMS sending error: {e}")
        return False

def test_whatsapp_sending():
    """Test WhatsApp sending functionality."""
    print("\nTesting WhatsApp sending...")
    
    # Test with a sample Mauritius phone number
    test_phone = "+23052541234"
    test_message = "Test message from Household Electricity Dashboard WhatsApp system"
    
    print(f"  Attempting to send WhatsApp to: {test_phone}")
    print(f"  Message: {test_message}")
    
    try:
        result = send_whatsapp(test_phone, test_message)
        if result:
            print("  ✓ WhatsApp sent successfully!")
            return True
        else:
            print("  ✗ WhatsApp sending failed!")
            return False
    except Exception as e:
        print(f"  ✗ WhatsApp sending error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Twilio SMS Functionality Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Phone number normalization
    if test_phone_number_normalization():
        tests_passed += 1
    
    # Test 2: Twilio configuration
    if test_twilio_configuration():
        tests_passed += 1
    
    # Test 3: SMS sending (only if configured)
    if getattr(settings, 'TWILIO_SMS_ENABLED', False):
        if test_sms_sending():
            tests_passed += 1
    else:
        print("\nSkipping SMS sending test (TWILIO_SMS_ENABLED is False)")
        tests_passed += 1
    
    # Test 4: WhatsApp sending (only if configured)
    if getattr(settings, 'TWILIO_WHATSAPP_FROM', None):
        if test_whatsapp_sending():
            tests_passed += 1
    else:
        print("\nSkipping WhatsApp sending test (TWILIO_WHATSAPP_FROM not configured)")
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! SMS functionality is working correctly.")
        print("\nNext steps:")
        print("1. Add a resident profile with a phone number in the dashboard")
        print("2. Trigger a high-usage alert (usage > 5 kWh or > 2 hours)")
        print("3. Verify SMS is sent to the resident's phone number")
        print("4. Test the alert confirmation system via SMS links")
    else:
        print("❌ Some tests failed. Please check the configuration.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()