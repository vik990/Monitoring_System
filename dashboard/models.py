import calendar
import logging
from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# ========================
# Resident Model
# ========================

class Resident(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_name = models.CharField(max_length=100, help_text="Name for this profile (e.g., 'Main Household')")
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    email_password = models.CharField(max_length=100, blank=True, help_text="App password for sending alerts")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    household_size = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Set as default profile for alerts")

    class Meta:
        unique_together = ['user', 'profile_name']

    def __str__(self):
        return f"{self.full_name} ({self.profile_name})"

    def get_monthly_usage(self, year=None, month=None):
        """Get monthly usage summary for strictly this resident's appliances"""
        if not year: year = timezone.now().year
        if not month: month = timezone.now().month

        start_date = date(year, month, 1)
        days_in_month = calendar.monthrange(year, month)[1]
        end_date = date(year, month, days_in_month)

        # Optimization: Filter by appliances linked to this resident
        usage_records = UsageRecord.objects.filter(
            appliance__resident=self,
            date__range=(start_date, end_date)
        ).select_related('appliance')

        total_energy = 0
        total_cost = 0
        appliance_breakdown = {}

        for record in usage_records:
            energy = record.energy_kwh
            cost = record.estimated_cost
            total_energy += energy
            total_cost += cost

            if record.appliance.name not in appliance_breakdown:
                appliance_breakdown[record.appliance.name] = {'energy': 0, 'cost': 0, 'hours': 0}
            
            appliance_breakdown[record.appliance.name]['energy'] += energy
            appliance_breakdown[record.appliance.name]['cost'] += cost
            appliance_breakdown[record.appliance.name]['hours'] += record.hours_used

        return {
            'year': year,
            'month': month,
            'total_energy': round(total_energy, 2),
            'total_cost': round(total_cost, 2),
            'appliance_breakdown': appliance_breakdown,
            'month_name': calendar.month_name[month],
            'avg_daily': round(total_energy / days_in_month, 2) if total_energy > 0 else 0
        }

    def send_alert(self, subject, message):
        """Standardized Alert Sender with custom SMTP fallback"""
        import smtplib, ssl, certifi
        from email.message import EmailMessage as StdEmailMessage

        if self.email and self.email_password:
            host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            port = getattr(settings, 'EMAIL_PORT', 587)
            
            ctx = ssl.create_default_context(cafile=certifi.where())
            try:
                with smtplib.SMTP(host, port, timeout=10) as server:
                    server.starttls(context=ctx)
                    server.login(self.email, self.email_password)
                    msg = StdEmailMessage()
                    msg.set_content(message)
                    msg['Subject'] = subject
                    msg['From'] = self.email
                    msg['To'] = self.email
                    server.send_message(msg)
                return True
            except Exception as e:
                logger.error(f"Custom SMTP failed for {self.email}: {e}")

        # Final Fallback to Global Settings
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email])
            return True
        except Exception as e:
            logger.error(f"Global fallback failed: {e}")
            return False

# ========================
# Appliance & Usage
# ========================

class Appliance(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, null=True, blank=True, related_name='appliances')
    name = models.CharField(max_length=100)
    power_rating = models.FloatField(help_text="Power rating in watts")
    threshold_hours = models.FloatField(default=8.0, help_text="Daily usage threshold in hours")
    is_critical = models.BooleanField(default=False)
    priority_level = models.IntegerField(default=1, choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')])

    def __str__(self):
        return self.name

    def get_priority_display_text(self):
        return dict(self._meta.get_field('priority_level').choices).get(self.priority_level)

class UsageRecord(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    date = models.DateField()
    hours_used = models.FloatField(help_text="Number of hours used")

    def __str__(self):
        return f"{self.appliance.name} - {self.date}"

    @property
    def energy_kwh(self):
        return (self.hours_used * self.appliance.power_rating) / 1000

    @property
    def estimated_cost(self):
        return self.energy_kwh * 5  # MUR 5 per kWh

# ========================
# Alerts & Aggregates
# ========================

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, default='GENERAL')
    date_created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    whatsapp_sent = models.BooleanField(default=False)
    requires_confirmation = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

class AlertConfirmation(models.Model):
    alert = models.OneToOneField(Alert, on_delete=models.CASCADE, related_name='confirmation')
    user_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmation_method = models.CharField(max_length=20, choices=[
        ('DASHBOARD', 'Dashboard'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
    ], null=True, blank=True)
    
    def __str__(self):
        return f"Confirmation for {self.alert.alert_type}"

class MonthlyApplianceUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, null=True, blank=True)
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    total_hours = models.FloatField(default=0.0)
    total_energy_kwh = models.FloatField(default=0.0)
    total_cost = models.FloatField(default=0.0)
    avg_daily_hours = models.FloatField(default=0.0)
    threshold_exceeded = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('appliance', 'year', 'month')

# ========================
# Signals
# ========================

@receiver([post_save, post_delete], sender=UsageRecord)
def _update_monthly_stats(sender, instance, **kwargs):
    y, m = instance.date.year, instance.date.month
    app = instance.appliance
    
    agg = UsageRecord.objects.filter(appliance=app, date__year=y, date__month=m).aggregate(total_h=Sum('hours_used'))
    total_h = agg['total_h'] or 0.0
    days = calendar.monthrange(y, m)[1]
    energy = (total_h * app.power_rating) / 1000
    
    MonthlyApplianceUsage.objects.update_or_create(
        appliance=app, year=y, month=m,
        defaults={
            'user': app.resident.user if app.resident else None,
            'resident': app.resident,
            'total_hours': total_h,
            'total_energy_kwh': energy,
            'total_cost': energy * 5,
            'avg_daily_hours': total_h / days,
            'threshold_exceeded': (total_h / days) > app.threshold_hours,
        }
    )

@receiver(post_save, sender=Appliance)
def mirror_appliance_to_mysql(sender, instance, **kwargs):
    mysql_cfg = settings.DATABASES.get('mysql')
    if not mysql_cfg: return

    import pymysql
    try:
        conn = pymysql.connect(
            host=mysql_cfg.get('HOST', '127.0.0.1'),
            port=int(mysql_cfg.get('PORT', 3306)),
            user=mysql_cfg.get('USER'),
            password=mysql_cfg.get('PASSWORD'),
            db=mysql_cfg.get('NAME')
        )
        with conn.cursor() as cur:
            sql = """INSERT INTO dashboard_appliance (resident_id, name, power_rating, threshold_hours, is_critical, priority_level, created_at, updated_at)
                     VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                     ON DUPLICATE KEY UPDATE power_rating=VALUES(power_rating), is_critical=VALUES(is_critical)"""
            cur.execute(sql, (instance.resident_id, instance.name, instance.power_rating, instance.threshold_hours, instance.is_critical, instance.priority_level))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"MySQL Mirror failed: {e}")