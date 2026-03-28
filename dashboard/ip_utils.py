"""
IP utilities for Tuya integration and server configuration.
This module provides functions to detect server IP addresses and generate
configuration instructions for Tuya platform setup.
"""

import requests
import socket
import subprocess
from typing import Dict, List, Optional
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


def get_public_ip() -> Optional[str]:
    """
    Get the public IP address of the server.
    Returns the public IP address as a string, or None if unable to determine.
    """
    try:
        # Method 1: Use ipify API
        response = requests.get('https://api.ipify.org', timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass

    try:
        # Method 2: Use ifconfig.me API
        response = requests.get('https://ifconfig.me/ip', timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass

    try:
        # Method 3: Use icanhazip.com API
        response = requests.get('https://icanhazip.com', timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass

    return None


def get_local_ip() -> Optional[str]:
    """
    Get the local IP address of the server.
    Returns the local IP address as a string, or None if unable to determine.
    """
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return None


def get_server_info() -> Dict[str, Optional[str]]:
    """
    Get comprehensive server information including IP addresses.
    Returns a dictionary with server information.
    """
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    
    # Get hostname
    hostname = socket.gethostname()
    
    # Get Django settings info
    debug_mode = getattr(settings, 'DEBUG', True)
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    
    return {
        'public_ip': public_ip,
        'local_ip': local_ip,
        'hostname': hostname,
        'debug_mode': debug_mode,
        'allowed_hosts': allowed_hosts,
        'tuya_base_url': getattr(settings, 'TUYA_BASE_URL', 'Not configured'),
        'tuya_device_id': getattr(settings, 'TUYA_DEVICE_ID', 'Not configured'),
    }


def generate_tuya_whitelist_instructions() -> str:
    """
    Generate instructions for adding the server IP to Tuya whitelist.
    Returns formatted instructions as a string.
    """
    server_info = get_server_info()
    public_ip = server_info['public_ip']
    
    instructions = """
# Tuya Platform IP Whitelist Configuration Instructions

## For Local Development (127.0.0.1:8000)
When running locally, Tuya cannot reach your development server directly.
You have two options:

### Option 1: Use ngrok for Local Testing
1. Install ngrok: https://ngrok.com/download
2. Run: `ngrok http 8000`
3. Copy the generated HTTPS URL (e.g., https://abc123.ngrok.io)
4. Add this URL to your Tuya project's IP whitelist

### Option 2: Deploy to a Server with Public IP
Deploy your application to a cloud platform (Vercel, Heroku, AWS, etc.)

## For Production Deployment

"""
    
    if public_ip:
        instructions += f"""
### Your Current Public IP Address: {public_ip}

To add your IP to Tuya whitelist:

1. Log in to Tuya Developer Platform: https://developer.tuya.com/
2. Go to your project settings
3. Navigate to "API Authorization" or "IP Whitelist"
4. Add the following IP addresses:
   - {public_ip} (Your current public IP)
   
5. For the TUYA_BASE_URL, use:
   - {server_info['tuya_base_url']}

6. Your TUYA_DEVICE_ID is: {server_info['tuya_device_id']}

## Important Notes:
- If your IP address changes (dynamic IP), you'll need to update the whitelist
- Consider using a static IP or domain name for production
- Test the connection after adding the IP to the whitelist
"""
    else:
        instructions += """
### Unable to detect public IP automatically

This usually happens when:
- You're behind a corporate firewall
- Your network configuration blocks external requests
- You're running in a restricted environment

To find your public IP manually:
1. Visit https://whatismyipaddress.com/
2. Or run: curl https://api.ipify.org
3. Or check your router's external IP

Then follow the steps above to add it to Tuya whitelist.
"""
    
    return instructions


@require_GET
def get_ip_info_api(request):
    """
    API endpoint to get server IP information.
    Returns JSON response with server information.
    """
    try:
        server_info = get_server_info()
        return JsonResponse({
            'success': True,
            'server_info': server_info,
            'instructions': generate_tuya_whitelist_instructions()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_GET
def test_tuya_connection(request):
    """
    Test connection to Tuya API.
    Returns JSON response with connection test results.
    """
    try:
        from .tuya_client import TuyaCloudClient, TuyaCredentials
        
        # Get Tuya credentials from settings
        access_id = getattr(settings, 'TUYA_ACCESS_ID', '')
        access_secret = getattr(settings, 'TUYA_ACCESS_SECRET', '')
        base_url = getattr(settings, 'TUYA_BASE_URL', '')
        device_id = getattr(settings, 'TUYA_DEVICE_ID', '')
        
        if not all([access_id, access_secret, base_url, device_id]):
            return JsonResponse({
                'success': False,
                'error': 'Tuya credentials not configured in settings',
                'missing_fields': [
                    'TUYA_ACCESS_ID' if not access_id else None,
                    'TUYA_ACCESS_SECRET' if not access_secret else None,
                    'TUYA_BASE_URL' if not base_url else None,
                    'TUYA_DEVICE_ID' if not device_id else None,
                ]
            }, status=400)
        
        # Test Tuya connection
        creds = TuyaCredentials(
            access_id=access_id,
            access_secret=access_secret,
            base_url=base_url,
        )
        client = TuyaCloudClient(creds)
        
        # Try to get device status
        status_response = client.get_device_status(device_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Tuya connection successful',
            'device_status': status_response.get('result', []),
            'server_info': get_server_info()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'server_info': get_server_info()
        }, status=500)


def check_deployment_readiness() -> Dict[str, any]:
    """
    Check if the application is ready for deployment.
    Returns a dictionary with readiness status and recommendations.
    """
    readiness = {
        'status': 'unknown',
        'checks': [],
        'recommendations': []
    }
    
    # Check Tuya configuration
    tuya_checks = []
    access_id = getattr(settings, 'TUYA_ACCESS_ID', '')
    access_secret = getattr(settings, 'TUYA_ACCESS_SECRET', '')
    base_url = getattr(settings, 'TUYA_BASE_URL', '')
    device_id = getattr(settings, 'TUYA_DEVICE_ID', '')
    
    if all([access_id, access_secret, base_url, device_id]):
        tuya_checks.append({'check': 'Tuya credentials', 'status': 'pass'})
    else:
        tuya_checks.append({
            'check': 'Tuya credentials', 
            'status': 'fail',
            'missing': [
                'TUYA_ACCESS_ID' if not access_id else None,
                'TUYA_ACCESS_SECRET' if not access_secret else None,
                'TUYA_BASE_URL' if not base_url else None,
                'TUYA_DEVICE_ID' if not device_id else None,
            ]
        })
    
    # Check IP availability
    public_ip = get_public_ip()
    if public_ip:
        tuya_checks.append({'check': 'Public IP detection', 'status': 'pass', 'ip': public_ip})
    else:
        tuya_checks.append({'check': 'Public IP detection', 'status': 'warn', 'message': 'Unable to detect public IP'})
    
    # Check debug mode
    debug_mode = getattr(settings, 'DEBUG', True)
    if debug_mode:
        tuya_checks.append({'check': 'Debug mode', 'status': 'warn', 'message': 'Debug mode is enabled'})
        readiness['recommendations'].append('Set DEBUG=False for production deployment')
    else:
        tuya_checks.append({'check': 'Debug mode', 'status': 'pass'})
    
    readiness['checks'] = tuya_checks
    
    # Determine overall status
    failed_checks = [check for check in tuya_checks if check['status'] == 'fail']
    if failed_checks:
        readiness['status'] = 'fail'
        readiness['recommendations'].append('Fix all failed checks before deployment')
    elif any(check['status'] == 'warn' for check in tuya_checks):
        readiness['status'] = 'warn'
        readiness['recommendations'].append('Address warning issues for optimal deployment')
    else:
        readiness['status'] = 'ready'
    
    return readiness