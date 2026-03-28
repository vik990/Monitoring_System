#!/usr/bin/env python3
"""
Test script to verify Tuya connection and IP configuration.
Run this script to test your Tuya integration setup.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')

# Setup Django
django.setup()

def test_tuya_connection():
    """Test Tuya API connection and display results."""
    print("🔍 Testing Tuya Connection Setup...")
    print("=" * 50)
    
    try:
        from dashboard.ip_utils import get_server_info, generate_tuya_whitelist_instructions
        from dashboard.tuya_client import TuyaCloudClient, TuyaCredentials, extract_live_metrics
        from django.conf import settings
        
        # Get server information
        print("📡 Getting server information...")
        server_info = get_server_info()
        
        print(f"📍 Public IP: {server_info['public_ip'] or 'Unable to detect'}")
        print(f"🏠 Local IP: {server_info['local_ip'] or 'Unable to detect'}")
        print(f"🖥️  Hostname: {server_info['hostname']}")
        print(f"🔧 Debug Mode: {server_info['debug_mode']}")
        print()
        
        # Check Tuya configuration
        print("🔌 Checking Tuya Configuration...")
        tuya_config = {
            'TUYA_ACCESS_ID': getattr(settings, 'TUYA_ACCESS_ID', ''),
            'TUYA_ACCESS_SECRET': getattr(settings, 'TUYA_ACCESS_SECRET', ''),
            'TUYA_BASE_URL': getattr(settings, 'TUYA_BASE_URL', ''),
            'TUYA_DEVICE_ID': getattr(settings, 'TUYA_DEVICE_ID', ''),
        }
        
        missing_config = []
        for key, value in tuya_config.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {'Configured' if value else 'Missing'}")
            if not value:
                missing_config.append(key)
        
        print()
        
        if missing_config:
            print("❌ Missing Tuya Configuration:")
            for config in missing_config:
                print(f"   - {config}")
            print("\n💡 Please update your settings.py or environment variables.")
            return False
        
        # Test Tuya connection
        print("🌐 Testing Tuya API Connection...")
        try:
            creds = TuyaCredentials(
                access_id=tuya_config['TUYA_ACCESS_ID'],
                access_secret=tuya_config['TUYA_ACCESS_SECRET'],
                base_url=tuya_config['TUYA_BASE_URL'],
            )
            client = TuyaCloudClient(creds)
            
            print("  📡 Getting device info...")
            device_info = client.get_device_info(tuya_config['TUYA_DEVICE_ID'])
            print("  ✅ Device info retrieved successfully")
            
            print("  📊 Getting device status...")
            status_response = client.get_device_status(tuya_config['TUYA_DEVICE_ID'])
            print("  ✅ Device status retrieved successfully")
            
            # Extract live metrics
            live_metrics = extract_live_metrics(status_response.get('result', []))
            print(f"  📈 Live metrics extracted: {live_metrics}")
            
            print("\n🎉 Tuya Connection Test Successful!")
            print("✅ Your Tuya integration is working correctly.")
            
        except Exception as e:
            print(f"  ❌ Tuya API Error: {str(e)}")
            print("\n🔧 Troubleshooting:")
            print("   1. Check your Tuya credentials in settings.py")
            print("   2. Verify your device ID is correct")
            print("   3. Ensure your IP is whitelisted in Tuya Developer Console")
            print("   4. Check your internet connection")
            return False
        
        # Generate IP whitelist instructions
        print("\n📋 Tuya IP Whitelist Instructions:")
        print("-" * 40)
        instructions = generate_tuya_whitelist_instructions()
        print(instructions)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("💡 Make sure you're running this from the project root directory.")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

def main():
    """Main function to run the test."""
    print("🏠 Electricity Monitor Dashboard - Tuya Connection Test")
    print("=" * 60)
    print()
    
    success = test_tuya_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Your Tuya integration is ready.")
        print("\n🚀 Next Steps:")
        print("   1. Deploy your application to Vercel")
        print("   2. Add your Vercel URL to Tuya IP whitelist")
        print("   3. Configure environment variables in Vercel")
        print("   4. Test your deployed application")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Need Help?")
        print("   - Check the DEPLOYMENT_GUIDE.md file")
        print("   - Visit Tuya Developer Console")
        print("   - Ensure all dependencies are installed")
    
    print()

if __name__ == "__main__":
    main()