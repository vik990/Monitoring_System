from django.urls import path
from . import views
from . import ip_utils

app_name = 'dashboard'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Dashboard Home
    path('', views.index, name='index'),
    path('api/tuya/live-metrics/', views.tuya_live_metrics, name='tuya_live_metrics'),

    # Resident Profiles
    path('residents/', views.resident_profiles, name='resident_profiles'),
    path('residents/add/', views.resident_profile, name='add_resident_profile'),
    path('residents/<int:profile_id>/', views.resident_profile, name='resident_details'),
    path('residents/<int:profile_id>/delete/', views.delete_resident_profile, name='delete_resident_profile'),
    path('residents/<int:profile_id>/edit/', views.resident_profile, name='edit_resident_profile'),
    path('residents/<int:profile_id>/set-default/', views.set_default_resident_profile, name='set_default_profile'),
    path('residents/<int:profile_id>/send-test-email/', views.send_test_email, name='send_test_email'),

    # Appliances
    path('appliances/', views.appliances, name='appliances'),
    path('appliances/add/', views.add_appliance, name='add_appliance'),
    path('appliances/<int:appliance_id>/delete/', views.delete_appliance, name='delete_appliance'),
    path('appliances/critical/', views.critical_appliances, name='critical_appliances'),

    # Usage Records
    path('usage-records/', views.usage_records, name='usage_records'),
    path('usage-records/add/', views.add_usage_record, name='add_usage_record'),
    path('usage-records/<int:record_id>/edit/', views.edit_usage_record, name='edit_usage_record'),
    path('usage-records/<int:record_id>/delete/', views.delete_usage_record, name='delete_usage_record'),

    # Alerts
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/mark-read/<int:alert_id>/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/send-manual/<int:profile_id>/', views.send_manual_alert, name='send_manual_alert'),
    path('check_usage_alerts/', views.check_usage_alerts, name='check_usage_alerts'),

    # Analytics & Exports
    path('charts/', views.charts, name='charts'),
    path('send-sms-alert/', views.send_sms_alert, name='send_sms_alert'),
    path('export/', views.export, name='export'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('high-usage-sms/', views.high_usage_sms_dashboard, name='high_usage_sms'),

    # IP and Tuya Configuration Utilities
    path('ip-info/', ip_utils.get_ip_info_api, name='ip_info'),
    path('test-tuya-connection/', ip_utils.test_tuya_connection, name='test_tuya_connection'),

    # Appliance Detection and Identification
    path('appliance-detection/', views.appliance_detection_view, name='appliance_detection'),
    path('identify-appliance/', views.identify_appliance_view, name='identify_appliance'),
    path('appliance-info/', views.get_appliance_info_api, name='appliance_info'),

    # Alert Confirmation System
    path('alert-confirmation/<int:alert_id>/', views.alert_confirmation_view, name='alert_confirmation'),
    path('confirm-alert/<int:alert_id>/', views.confirm_alert, name='confirm_alert'),
    path('dismiss-alert/<int:alert_id>/', views.dismiss_alert, name='dismiss_alert'),
    path('send-sms-confirmation/<int:alert_id>/', views.send_alert_confirmation_sms, name='send_sms_confirmation'),
    path('alerts-with-confirmation/', views.alerts_with_confirmation, name='alerts_with_confirmation'),
]
