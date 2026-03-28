"""
Appliance Detection and Identification System for Tuya Smart Plug

This module provides functionality to:
1. Manually identify appliances plugged into the smart plug
2. Automatically detect appliance types based on power consumption patterns
3. Display detailed appliance information on the dashboard
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils import timezone
from django.conf import settings
from .models import Appliance, UsageRecord, Resident
from .tuya_client import TuyaCloudClient, TuyaCredentials, extract_live_metrics

logger = logging.getLogger(__name__)

# Appliance power consumption patterns (in Watts)
APPLIANCE_PATTERNS = {
    'refrigerator': {
        'typical_power': (100, 200),
        'description': 'Refrigerator/Freezer',
        'icon': '🧊',
        'category': 'Kitchen',
        'duty_cycle': 'Cyclic (on/off every 10-30 mins)'
    },
    'air_conditioner': {
        'typical_power': (1000, 3500),
        'description': 'Air Conditioner',
        'icon': '❄️',
        'category': 'Climate Control',
        'duty_cycle': 'Cyclic (on/off based on temperature)'
    },
    'water_heater': {
        'typical_power': (1500, 3000),
        'description': 'Water Heater',
        'icon': '🔥',
        'category': 'Water Heating',
        'duty_cycle': 'Cyclic (heats water, then cycles off)'
    },
    'washing_machine': {
        'typical_power': (400, 2500),
        'description': 'Washing Machine',
        'icon': '👕',
        'category': 'Laundry',
        'duty_cycle': 'Intermittent (varies during cycle)'
    },
    'dryer': {
        'typical_power': (1800, 5000),
        'description': 'Clothes Dryer',
        'icon': '👗',
        'category': 'Laundry',
        'duty_cycle': 'Continuous during cycle (30-60 mins)'
    },
    'microwave': {
        'typical_power': (600, 1500),
        'description': 'Microwave Oven',
        'icon': '🍿',
        'category': 'Kitchen',
        'duty_cycle': 'Short bursts (1-10 minutes)'
    },
    'electric_kettle': {
        'typical_power': (1500, 3000),
        'description': 'Electric Kettle',
        'icon': '☕',
        'category': 'Kitchen',
        'duty_cycle': 'Short bursts (2-5 minutes)'
    },
    'toaster': {
        'typical_power': (800, 1800),
        'description': 'Toaster',
        'icon': '🍞',
        'category': 'Kitchen',
        'duty_cycle': 'Short bursts (1-5 minutes)'
    },
    'coffee_maker': {
        'typical_power': (800, 1500),
        'description': 'Coffee Maker',
        'icon': '☕',
        'category': 'Kitchen',
        'duty_cycle': 'Short cycles (5-15 minutes)'
    },
    'computer': {
        'typical_power': (50, 500),
        'description': 'Computer/Laptop',
        'icon': '💻',
        'category': 'Electronics',
        'duty_cycle': 'Variable (depends on usage)'
    },
    'television': {
        'typical_power': (50, 400),
        'description': 'Television',
        'icon': '📺',
        'category': 'Entertainment',
        'duty_cycle': 'Continuous during use'
    },
    'gaming_console': {
        'typical_power': (50, 350),
        'description': 'Gaming Console',
        'icon': '🎮',
        'category': 'Entertainment',
        'duty_cycle': 'Variable (depends on game)'
    },
    'vacuum_cleaner': {
        'typical_power': (500, 3000),
        'description': 'Vacuum Cleaner',
        'icon': '🧹',
        'category': 'Cleaning',
        'duty_cycle': 'Short bursts (10-30 minutes)'
    },
    'hair_dryer': {
        'typical_power': (800, 1800),
        'description': 'Hair Dryer',
        'icon': '💨',
        'category': 'Personal Care',
        'duty_cycle': 'Short bursts (2-15 minutes)'
    },
    'iron': {
        'typical_power': (800, 1800),
        'description': 'Clothes Iron',
        'icon': '🔥',
        'category': 'Laundry',
        'duty_cycle': 'Intermittent (heats up, cycles off)'
    },
    'fan': {
        'typical_power': (20, 100),
        'description': 'Electric Fan',
        'icon': '🌀',
        'category': 'Climate Control',
        'duty_cycle': 'Continuous during use'
    },
    'lighting': {
        'typical_power': (5, 100),
        'description': 'LED/Lighting',
        'icon': '💡',
        'category': 'Lighting',
        'duty_cycle': 'Continuous during use'
    },
    'unknown': {
        'typical_power': (0, float('inf')),
        'description': 'Unknown Appliance',
        'icon': '❓',
        'category': 'Unknown',
        'duty_cycle': 'Unknown pattern'
    }
}

class ApplianceDetector:
    """Intelligent appliance detection system."""
    
    def __init__(self, resident=None):
        self.resident = resident or self._get_monitoring_resident()
        self.tuya_appliance = self._get_tuya_appliance()
        
    def _get_monitoring_resident(self):
        """Get the Tuya monitoring resident."""
        try:
            return Resident.objects.get(profile_name='Tuya Monitoring')
        except Resident.DoesNotExist:
            return None
    
    def _get_tuya_appliance(self):
        """Get the Tuya smart plug appliance."""
        try:
            return Appliance.objects.get(name='Tuya Smart Plug - Live Monitoring')
        except Appliance.DoesNotExist:
            return None
    
    def detect_appliance_type(self, power_w=None, current_a=None, voltage_v=None):
        """
        Detect appliance type based on power consumption patterns.
        
        Args:
            power_w: Current power consumption in watts
            current_a: Current in amps
            voltage_v: Voltage in volts
            
        Returns:
            dict: Detected appliance information
        """
        if power_w is None:
            # Get current live data from Tuya
            try:
                creds = TuyaCredentials(
                    access_id=settings.TUYA_ACCESS_ID,
                    access_secret=settings.TUYA_ACCESS_SECRET,
                    base_url=settings.TUYA_BASE_URL,
                )
                client = TuyaCloudClient(creds)
                status_response = client.get_device_status(settings.TUYA_DEVICE_ID)
                live_metrics = extract_live_metrics(status_response.get('result', []))
                
                power_w = live_metrics.get('power_w')
                current_a = live_metrics.get('current_a')
                voltage_v = live_metrics.get('voltage_v')
                
            except Exception as e:
                logger.error(f"Error getting live Tuya data: {e}")
                return self._get_unknown_appliance()
        
        if power_w is None or power_w <= 0:
            return self._get_unknown_appliance()
        
        # Find matching appliance type
        best_match = None
        min_diff = float('inf')
        
        for appliance_type, pattern in APPLIANCE_PATTERNS.items():
            if appliance_type == 'unknown':
                continue
                
            min_power, max_power = pattern['typical_power']
            
            if min_power <= power_w <= max_power:
                # Exact match found
                return {
                    'type': appliance_type,
                    'description': pattern['description'],
                    'icon': pattern['icon'],
                    'category': pattern['category'],
                    'duty_cycle': pattern['duty_cycle'],
                    'confidence': 'HIGH',
                    'power_w': power_w,
                    'current_a': current_a,
                    'voltage_v': voltage_v,
                    'match_score': 100
                }
            else:
                # Calculate how close this is to the range
                if power_w < min_power:
                    diff = min_power - power_w
                else:
                    diff = power_w - max_power
                
                if diff < min_diff:
                    min_diff = diff
                    best_match = appliance_type
        
        # If no exact match, return closest match with lower confidence
        if best_match:
            pattern = APPLIANCE_PATTERNS[best_match]
            confidence = 'MEDIUM' if min_diff < 200 else 'LOW'
            match_score = max(0, 100 - (min_diff // 10))
            
            return {
                'type': best_match,
                'description': pattern['description'],
                'icon': pattern['icon'],
                'category': pattern['category'],
                'duty_cycle': pattern['duty_cycle'],
                'confidence': confidence,
                'power_w': power_w,
                'current_a': current_a,
                'voltage_v': voltage_v,
                'match_score': match_score
            }
        
        return self._get_unknown_appliance(power_w, current_a, voltage_v)
    
    def _get_unknown_appliance(self, power_w=None, current_a=None, voltage_v=None):
        """Return unknown appliance information."""
        return {
            'type': 'unknown',
            'description': 'Unknown Appliance',
            'icon': '❓',
            'category': 'Unknown',
            'duty_cycle': 'Unknown pattern',
            'confidence': 'UNKNOWN',
            'power_w': power_w,
            'current_a': current_a,
            'voltage_v': voltage_v,
            'match_score': 0
        }
    
    def get_appliance_usage_history(self, days=7):
        """
        Get usage history for the Tuya appliance.
        
        Args:
            days: Number of days to look back
            
        Returns:
            dict: Usage statistics and patterns
        """
        if not self.tuya_appliance:
            return {}
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        usage_records = UsageRecord.objects.filter(
            appliance=self.tuya_appliance,
            date__gte=start_date
        ).order_by('date')
        
        if not usage_records:
            return {'message': 'No usage data available for the specified period'}
        
        # Analyze usage patterns
        daily_stats = defaultdict(list)
        total_energy = 0
        active_days = 0
        
        for record in usage_records:
            energy = record.energy_kwh
            total_energy += energy
            if energy > 0:
                active_days += 1
                daily_stats[record.date].append(energy)
        
        # Calculate statistics
        avg_daily_energy = total_energy / days if days > 0 else 0
        avg_active_daily_energy = total_energy / active_days if active_days > 0 else 0
        
        # Detect usage patterns
        usage_patterns = self._analyze_usage_patterns(usage_records)
        
        return {
            'total_energy': round(total_energy, 3),
            'avg_daily_energy': round(avg_daily_energy, 3),
            'avg_active_daily_energy': round(avg_active_daily_energy, 3),
            'active_days': active_days,
            'total_days': days,
            'usage_patterns': usage_patterns,
            'detection_confidence': self._calculate_detection_confidence(usage_records)
        }
    
    def _analyze_usage_patterns(self, usage_records):
        """Analyze usage patterns from historical data."""
        patterns = {
            'peak_usage_times': [],
            'average_daily_usage': [],
            'usage_frequency': 'Unknown'
        }
        
        # Group by hour of day to find peak usage times
        hourly_usage = defaultdict(float)
        
        for record in usage_records:
            # This is a simplified analysis - in a real implementation,
            # you'd want more granular time data
            hourly_usage[record.date.hour] += record.energy_kwh
        
        # Find peak usage hours
        if hourly_usage:
            sorted_hours = sorted(hourly_usage.items(), key=lambda x: x[1], reverse=True)
            patterns['peak_usage_times'] = [hour for hour, _ in sorted_hours[:3]]
        
        return patterns
    
    def _calculate_detection_confidence(self, usage_records):
        """Calculate confidence in appliance detection based on usage history."""
        if not usage_records:
            return 'LOW'
        
        # More data points = higher confidence
        data_points = len(usage_records)
        if data_points >= 14:  # 2 weeks of data
            return 'HIGH'
        elif data_points >= 7:  # 1 week of data
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def create_identified_appliance(self, appliance_type, custom_name=None):
        """
        Create a new appliance record for the identified appliance.
        
        Args:
            appliance_type: Type of appliance (from APPLIANCE_PATTERNS)
            custom_name: Optional custom name for the appliance
            
        Returns:
            Appliance: Created appliance instance
        """
        if not self.resident or not self.tuya_appliance:
            logger.error("Cannot create identified appliance: resident or tuya appliance not found")
            return None
        
        pattern = APPLIANCE_PATTERNS.get(appliance_type, APPLIANCE_PATTERNS['unknown'])
        
        name = custom_name or pattern['description']
        
        # Create new appliance
        appliance = Appliance.objects.create(
            resident=self.resident,
            name=name,
            power_rating=self.tuya_appliance.power_rating,
            threshold_hours=8.0,
            is_critical=False,
            priority_level=2
        )
        
        logger.info(f"Created identified appliance: {name} ({appliance_type})")
        return appliance
    
    def get_appliance_recommendations(self, power_w):
        """
        Get recommendations based on current power consumption.
        
        Args:
            power_w: Current power consumption
            
        Returns:
            list: List of recommendations
        """
        recommendations = []
        
        if power_w > 2000:
            recommendations.append({
                'type': 'high_consumption',
                'message': f'High power consumption detected ({power_w}W). Consider energy-efficient alternatives.',
                'priority': 'HIGH'
            })
        elif power_w > 500:
            recommendations.append({
                'type': 'moderate_consumption',
                'message': f'Moderate power consumption ({power_w}W). Monitor usage during peak hours.',
                'priority': 'MEDIUM'
            })
        
        if power_w > 0:
            recommendations.append({
                'type': 'usage_optimization',
                'message': 'Consider using this appliance during off-peak hours to save on electricity costs.',
                'priority': 'LOW'
            })
        
        return recommendations

def get_current_appliance_info():
    """Get current appliance information for dashboard display."""
    detector = ApplianceDetector()
    
    # Get current live data
    current_data = detector.detect_appliance_type()
    
    # Get usage history
    usage_history = detector.get_appliance_usage_history(days=7)
    
    # Get recommendations
    recommendations = detector.get_appliance_recommendations(current_data['power_w'])
    
    return {
        'current_detection': current_data,
        'usage_history': usage_history,
        'recommendations': recommendations,
        'timestamp': timezone.now()
    }

def identify_appliance_manually(appliance_type, custom_name=None):
    """
    Manually identify the appliance plugged into the smart plug.
    
    Args:
        appliance_type: Type of appliance
        custom_name: Optional custom name
        
    Returns:
        dict: Result of the identification
    """
    detector = ApplianceDetector()
    
    if not detector.resident:
        return {'success': False, 'error': 'Monitoring resident not found'}
    
    if appliance_type not in APPLIANCE_PATTERNS:
        return {'success': False, 'error': 'Invalid appliance type'}
    
    # Create identified appliance
    identified_appliance = detector.create_identified_appliance(appliance_type, custom_name)
    
    if identified_appliance:
        return {
            'success': True,
            'appliance': {
                'name': identified_appliance.name,
                'type': appliance_type,
                'description': APPLIANCE_PATTERNS[appliance_type]['description'],
                'icon': APPLIANCE_PATTERNS[appliance_type]['icon']
            }
        }
    else:
        return {'success': False, 'error': 'Failed to create identified appliance'}

def get_available_appliance_types():
    """Get list of available appliance types for manual identification."""
    return [
        {
            'type': key,
            'description': value['description'],
            'icon': value['icon'],
            'category': value['category'],
            'power_range': f"{value['typical_power'][0]}W - {value['typical_power'][1]}W"
        }
        for key, value in APPLIANCE_PATTERNS.items()
        if key != 'unknown'
    ]