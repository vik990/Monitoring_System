from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Resident, Appliance, UsageRecord, Alert
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .tuya_client import TuyaCloudClient, TuyaCredentials, extract_live_metrics
from .tasks import dispatch_alert_notification_task
from .tariffs import calculate_tariff_cost, get_marginal_rate
from .appliance_detection import get_current_appliance_info, identify_appliance_manually, get_available_appliance_types
from .utils import send_sms
from django.db.models import Sum

# ========================
# AUTH VIEWS
# ========================

from django.contrib import messages


def login_view(request):
    """Professional login: supports `next` redirect and friendly messages."""
    next_url = request.GET.get('next') or request.POST.get('next') or None
    # Normalize values coming from the template (templates render Python None as the string 'None')
    if next_url in (None, 'None', ''):
        next_url = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url or 'dashboard:index')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'dashboard/login.html', {'next': next_url})

    # GET
    return render(request, 'dashboard/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('dashboard:login')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            return render(request, 'dashboard/register.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(username=username, password=password, email=email)
        login(request, user)
        return redirect('dashboard:index')

    return render(request, 'dashboard/register.html')


# ========================
# DASHBOARD INDEX
# ========================

@login_required
def index(request):
    # Fast initial values
    total_appliances = 0
    total_energy = 0.0
    avg_daily_usage = 0.0
    estimated_savings = 0.0
    total_cost = 0.0
    trend_percentage = 0.0
    tariff_rate = get_marginal_rate(0)
    live_metrics = None
    live_error = None
    live_online = None
    monitored_mode = False

    # Energy tips (cached)
    energy_tips = [
        {"text": "Turn off appliances when not in use."},
        {"text": "Use energy-efficient LED bulbs."},
        {"text": "Monitor peak hours to save energy."},
        {"text": "Check appliance efficiency monthly."}
    ]

    # Fast database queries with select_related
    user_residents = Resident.objects.filter(user=request.user).select_related()
    user_appliances = Appliance.objects.filter(resident__user=request.user).select_related('resident')
    
    # Get recent usage records efficiently - limit to last 50 records for speed
    usage_records = UsageRecord.objects.filter(
        appliance__resident__in=user_residents
    ).select_related('appliance').order_by('-date')[:50]

    if usage_records:
        # Fast aggregation
        appliances_set = set()
        total_energy = 0.0
        
        for record in usage_records:
            appliances_set.add(record.appliance.name)
            total_energy += record.hours_used * record.appliance.power_rating / 1000
        
        total_appliances = len(appliances_set)
        total_cost = calculate_tariff_cost(total_energy)
        tariff_rate = get_marginal_rate(total_energy)
        avg_daily_usage = total_energy / len(usage_records) if usage_records else 0
        estimated_savings = total_cost * 0.1

        # Fast trend calculation using recent data only
        today = timezone.now().date()
        last_week_records = [r for r in usage_records if r.date >= today - timedelta(days=7)]
        prev_week_records = [r for r in usage_records if today - timedelta(days=14) <= r.date < today - timedelta(days=7)]

        if prev_week_records:
            last_week_energy = sum(r.hours_used * r.appliance.power_rating / 1000 for r in last_week_records)
            prev_week_energy = sum(r.hours_used * r.appliance.power_rating / 1000 for r in prev_week_records)
            if prev_week_energy > 0:
                trend_percentage = ((last_week_energy - prev_week_energy) / prev_week_energy) * 100

    # Fast alert checking - only check recent records
    recent_date = timezone.now().date() - timedelta(days=1)
    for appliance in user_appliances:
        recent_records = [r for r in usage_records if r.date >= recent_date and r.appliance == appliance]
        total_hours = sum(r.hours_used for r in recent_records)

        if total_hours > appliance.threshold_hours:
            alert_msg = f"High usage alert: {appliance.name} exceeded daily threshold ({total_hours:.1f}h > {appliance.threshold_hours}h)"
            Alert.objects.get_or_create(
                user=request.user,
                appliance=appliance,
                message=alert_msg,
                alert_type='HIGH_USAGE',
                defaults={'is_read': False}
            )

    # Fast alert retrieval with limit
    alerts = Alert.objects.filter(user=request.user, is_read=False).order_by('-date_created')[:3]

    # Fast resident profile lookup
    resident = user_residents.filter(is_default=True).first() or user_residents.first()
    has_profile = resident is not None
    resident_name = resident.full_name if resident else None

    # Fast Tuya metrics with timeout and error handling
    try:
        creds = TuyaCredentials(
            access_id=settings.TUYA_ACCESS_ID,
            access_secret=settings.TUYA_ACCESS_SECRET,
            base_url=settings.TUYA_BASE_URL,
        )
        client = TuyaCloudClient(creds)
        
        # Fast device info check
        try:
            info_response = client.get_device_info(settings.TUYA_DEVICE_ID)
            info = info_response.get('result', {}) if isinstance(info_response, dict) else {}
            if 'online' in info:
                live_online = bool(info.get('online'))
            elif 'is_online' in info:
                live_online = bool(info.get('is_online'))
        except Exception:
            live_online = None

        # Fast status check
        status_response = client.get_device_status(settings.TUYA_DEVICE_ID)
        live_metrics = extract_live_metrics(status_response.get('result', []))
        live_metrics['online'] = live_online
        
        if live_metrics:
            power_w = live_metrics.get('power_w')
            total_energy_kwh = live_metrics.get('total_energy_kwh')
            if power_w is not None:
                live_metrics['estimated_cost_per_hour_mur'] = round((float(power_w) / 1000.0) * tariff_rate, 3)
            if total_energy_kwh is not None:
                live_metrics['estimated_total_cost_mur'] = calculate_tariff_cost(total_energy_kwh)

            monitored_mode = True
            total_appliances = 1
            if total_energy_kwh is not None:
                total_energy = float(total_energy_kwh)
                total_cost = float(live_metrics.get('estimated_total_cost_mur', calculate_tariff_cost(total_energy_kwh)))
                estimated_savings = total_cost * 0.1
            trend_percentage = 0.0
    except Exception as exc:
        live_error = str(exc)

    context = {
        'total_appliances': total_appliances,
        'total_energy': round(total_energy, 2),
        'avg_daily_usage': round(avg_daily_usage, 2),
        'estimated_savings': f"{round(estimated_savings, 2)} MUR",
        'total_cost': round(total_cost, 2),
        'tariff_rate': round(tariff_rate, 2),
        'trend_percentage': round(trend_percentage, 1),
        'energy_tips': energy_tips,
        'alerts': alerts,
        'has_profile': has_profile,
        'resident': resident,
        'resident_name': resident_name,
        'tuya_device_id': settings.TUYA_DEVICE_ID,
        'live_metrics': live_metrics,
        'live_error': live_error,
        'live_online': live_online,
        'monitored_mode': monitored_mode,
    }

    return render(request, 'dashboard/index.html', context)


@login_required
@require_GET
def tuya_live_metrics(request):
    """JSON endpoint for near real-time Tuya smart plug readings."""
    device_id = (request.GET.get('device_id') or settings.TUYA_DEVICE_ID or '').strip()
    if not device_id:
        return JsonResponse({'success': False, 'error': 'Tuya device ID is not configured.'}, status=400)

    try:
        user_residents = Resident.objects.filter(user=request.user)
        today = timezone.now().date()
        usage_records = UsageRecord.objects.filter(
            appliance__resident__in=user_residents,
            date__year=today.year,
            date__month=today.month,
        )
        current_month_kwh = sum(r.hours_used * r.appliance.power_rating / 1000 for r in usage_records)
        marginal_rate = get_marginal_rate(current_month_kwh)

        creds = TuyaCredentials(
            access_id=settings.TUYA_ACCESS_ID,
            access_secret=settings.TUYA_ACCESS_SECRET,
            base_url=settings.TUYA_BASE_URL,
        )
        client = TuyaCloudClient(creds)

        device_online = None
        try:
            info_response = client.get_device_info(device_id)
            info = info_response.get('result', {}) if isinstance(info_response, dict) else {}
            if 'online' in info:
                device_online = bool(info.get('online'))
            elif 'is_online' in info:
                device_online = bool(info.get('is_online'))
        except Exception:
            device_online = None

        status_response = client.get_device_status(device_id)
        metrics = extract_live_metrics(status_response.get('result', []))
        metrics['online'] = device_online
        power_w = metrics.get('power_w')
        total_energy_kwh = metrics.get('total_energy_kwh')
        metrics['estimated_cost_per_hour_mur'] = round((float(power_w) / 1000.0) * marginal_rate, 3) if power_w is not None else None
        metrics['estimated_total_cost_mur'] = calculate_tariff_cost(total_energy_kwh) if total_energy_kwh is not None else None
        metrics['current_tariff_rate_mur_per_kwh'] = round(marginal_rate, 2)

        return JsonResponse({
            'success': True,
            'device_id': device_id,
            'metrics': metrics,
            'current_month_kwh': round(current_month_kwh, 3),
            'fetched_at': timezone.now().isoformat(),
        })
    except Exception as exc:
        err = str(exc)
        blocked = 'code' in err and '1114' in err
        return JsonResponse({
            'success': False,
            'error': err,
            'error_code': 'TUYA_IP_NOT_ALLOWED' if blocked else 'TUYA_API_ERROR',
            'hint': 'Allow this server public IP in Tuya project API whitelist.' if blocked else 'Check Tuya project authorization and device linkage.'
        }, status=502)


# ========================
# RESIDENT PROFILE VIEWS
# ========================

@login_required
def resident_profiles(request):
    profiles = Resident.objects.filter(user=request.user)
    total_profiles = profiles.count()
    return render(request, 'dashboard/resident_profiles.html', {'profiles': profiles, 'total_profiles': total_profiles})

@login_required
def resident_profile(request, profile_id=None):
    """Handles viewing and creating/editing resident profiles.

    - If profile_id is provided: show or edit profile details
    - If no profile_id and method is POST: create a new profile
    """
    from .forms import ResidentForm

    # Create a new profile
    if profile_id is None:
        if request.method == 'POST':
            form = ResidentForm(request.POST)
            if form.is_valid():
                new_profile = form.save(commit=False)
                new_profile.user = request.user
                new_profile.save()

                # If user sets it as default (or if this is the first profile), mark as default
                if new_profile.is_default or Resident.objects.filter(user=request.user).count() == 1:
                    Resident.objects.filter(user=request.user, is_default=True).update(is_default=False)
                    new_profile.is_default = True
                    new_profile.save(update_fields=['is_default'])

                messages.success(request, 'Resident profile saved successfully.')
                return redirect('dashboard:resident_profiles')
        else:
            form = ResidentForm()

        return render(request, 'dashboard/resident_profile.html', {
            'form': form,
            'is_profile_created': False,
            'resident': None,
        })

    # Edit or view an existing profile
    profile = get_object_or_404(Resident, id=profile_id, user=request.user)

    if request.method == 'POST':
        form = ResidentForm(request.POST, instance=profile)
        if form.is_valid():
            updated = form.save()
            # handle default profile change
            if updated.is_default:
                Resident.objects.filter(user=request.user, is_default=True).exclude(id=updated.id).update(is_default=False)
            messages.success(request, 'Resident profile updated successfully.')
            return redirect('dashboard:resident_profiles')
    else:
        form = ResidentForm(instance=profile)

    # Monthly usage summary (aggregate via appliance -> usage records)
    today = timezone.now().date()

    month_records = UsageRecord.objects.filter(
        appliance__resident=profile,
        date__year=today.year,
        date__month=today.month
    ).select_related('appliance')

    appliance_breakdown = {}
    total_energy = 0
    total_cost = 0
    for record in month_records:
        energy = record.hours_used * record.appliance.power_rating / 1000
        cost = energy * 5
        total_energy += energy
        total_cost += cost
        appliance_breakdown.setdefault(record.appliance.name, {'energy':0,'cost':0,'hours':0})
        appliance_breakdown[record.appliance.name]['energy'] += energy
        appliance_breakdown[record.appliance.name]['cost'] += cost
        appliance_breakdown[record.appliance.name]['hours'] += record.hours_used

    monthly_usage = {
        'month_name': today.strftime('%B'),
        'year': today.year,
        'total_energy': round(total_energy,2),
        'total_cost': round(total_cost,2),
        'appliance_breakdown': appliance_breakdown
    }

    return render(request, 'dashboard/resident_profile.html', {
        'form': form,
        'is_profile_created': True,
        'resident': profile,
        'monthly_usage': monthly_usage,
    })

@login_required
def delete_resident_profile(request, profile_id):
    # Only allow POST to delete to avoid accidental deletions via GET links
    profile = get_object_or_404(Resident, id=profile_id, user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for delete operation.')
        return redirect('dashboard:resident_profiles')

    # Prevent deleting the last profile
    if Resident.objects.filter(user=request.user).count() <= 1:
        messages.error(request, 'Cannot delete the last resident profile.')
        return redirect('dashboard:resident_profiles')

    profile.delete()
    messages.success(request, 'Resident profile deleted.')
    return redirect('dashboard:resident_profiles')


# ========================
# APPLIANCE & USAGE VIEWS
# ========================

@login_required
def appliances(request):
    appliances_list = Appliance.objects.filter(resident__user=request.user)
    return render(request, 'dashboard/appliances.html', {'appliances': appliances_list})

@login_required
def usage_records(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from django.db.models import Q, Min, Max

    user_residents = Resident.objects.filter(user=request.user)
    q = (request.GET.get('q') or '').strip()
    profile_id = (request.GET.get('profile') or '').strip()
    try:
        per_page = int(request.GET.get('per_page') or 10)
    except ValueError:
        per_page = 10
    page = request.GET.get('page') or 1

    records_qs = UsageRecord.objects.filter(appliance__resident__in=user_residents).select_related('appliance').order_by('-date')

    if profile_id:
        records_qs = records_qs.filter(appliance__resident_id=profile_id)

    if q:
        # allow searching by appliance name or date string
        records_qs = records_qs.filter(Q(appliance__name__icontains=q) | Q(date__icontains=q))

    measured_range = records_qs.aggregate(start=Min('date'), end=Max('date'))

    paginator = Paginator(records_qs, per_page)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'usage_records': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'q': q,
        'profiles': user_residents.order_by('profile_name'),
        'selected_profile': int(profile_id) if profile_id.isdigit() else None,
        'per_page': per_page,
        'total_records': records_qs.count(),
        'measured_start': measured_range.get('start'),
        'measured_end': measured_range.get('end'),
        'options_per_page': [5, 10, 20, 50],
    }
    return render(request, 'dashboard/usage_records.html', context)


# ========================
# MISSING/UTILITY VIEWS
# ========================

@login_required
def set_default_resident_profile(request, profile_id):
    profile = get_object_or_404(Resident, id=profile_id, user=request.user)
    # unset previous default
    Resident.objects.filter(user=request.user, is_default=True).update(is_default=False)
    profile.is_default = True
    profile.save(update_fields=['is_default'])
    return redirect('dashboard:resident_profiles')


@login_required
def add_appliance(request):
    from .forms import ApplianceForm
    user_residents = Resident.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ApplianceForm(request.POST)
        if form.is_valid():
            appliance = form.save(commit=False)
            # Associate appliance with user's default resident if available
            default_resident = user_residents.filter(is_default=True).first() or user_residents.first()
            if default_resident:
                appliance.resident = default_resident
            appliance.save()
            messages.success(request, 'Appliance added successfully.')
            return redirect('dashboard:appliances')
    else:
        form = ApplianceForm()
    return render(request, 'dashboard/add_appliance.html', {'form': form, 'residents': user_residents})


@login_required
def charts(request):
    """Electricity usage visualization with real measured ranges and profile filter."""
    import json
    from collections import defaultdict
    from datetime import date, datetime, timedelta
    from django.db.models import Min, Max, Sum

    user_residents = Resident.objects.filter(user=request.user)
    profile_id = (request.GET.get('profile') or '').strip()

    records_all = UsageRecord.objects.filter(appliance__resident__in=user_residents).select_related('appliance').order_by('date')
    if profile_id:
        records_all = records_all.filter(appliance__resident_id=profile_id)

    period = (request.GET.get('period') or 'week').lower()
    if period not in ('week', 'month', 'day'):
        period = 'week'

    today = timezone.now().date()
    
    # Get first record date for historical context
    first_record_date = records_all.first().date if records_all.exists() else None
    measured_range = records_all.aggregate(start=Min('date'), end=Max('date'))
    measured_start = measured_range.get('start')
    measured_end = measured_range.get('end')

    if period == 'day':
        # Daily view: last 24 hours with hourly granularity
        start_date = today - timedelta(days=1)
        end_date = today
        
        # Get hourly data for the last 24 hours
        hourly_data = defaultdict(float)
        for hour in range(24):
            hour_date = today - timedelta(hours=23-hour)
            # Find records for this hour (approximate by date)
            hour_records = records_all.filter(date=hour_date.date())
            total_energy = sum(r.hours_used * r.appliance.power_rating / 1000 for r in hour_records)
            hourly_data[hour_date.strftime('%H:00')] = round(total_energy, 3)

        labels = list(hourly_data.keys())
        energy_series = list(hourly_data.values())
        chart_title = '24-Hour Usage'
        
    elif period == 'week':
        # Weekly view: last 7 days with daily granularity
        start_date = today - timedelta(days=6)
        end_date = today

        # Get daily data for the last 7 days
        daily_data = defaultdict(float)
        for day in range(7):
            day_date = start_date + timedelta(days=day)
            day_records = records_all.filter(date=day_date)
            total_energy = sum(r.hours_used * r.appliance.power_rating / 1000 for r in day_records)
            daily_data[day_date.strftime('%a %d %b')] = round(total_energy, 3)

        labels = list(daily_data.keys())
        energy_series = list(daily_data.values())
        chart_title = '7-Day Usage Trend'
        
    else:
        # Monthly view: current month with daily granularity
        start_month = today.replace(day=1)
        end_date = today
        
        # Get daily data for current month
        monthly_data = defaultdict(float)
        current_date = start_month
        while current_date <= end_date:
            day_records = records_all.filter(date=current_date)
            total_energy = sum(r.hours_used * r.appliance.power_rating / 1000 for r in day_records)
            monthly_data[current_date.strftime('%d %b')] = round(total_energy, 3)
            current_date += timedelta(days=1)

        labels = list(monthly_data.keys())
        energy_series = list(monthly_data.values())
        chart_title = f'{today.strftime("%B %Y")} Daily Usage'

    # If no data found for the requested period, try to show available data
    if not labels or not energy_series or sum(energy_series) == 0:
        if records_all.exists():
            # Fall back to showing the most recent available data
            recent_records = records_all.order_by('-date')[:30]  # Last 30 records
            if recent_records:
                # Group by date and sum energy
                fallback_data = defaultdict(float)
                for record in recent_records:
                    date_str = record.date.strftime('%Y-%m-%d')
                    energy = record.hours_used * record.appliance.power_rating / 1000
                    fallback_data[date_str] += energy
                
                # Sort by date and take last 7 days of available data
                sorted_dates = sorted(fallback_data.keys())[-7:]
                labels = [date_str for date_str in sorted_dates]
                energy_series = [round(fallback_data[date_str], 3) for date_str in sorted_dates]
                chart_title = f'Available Data (Last {len(labels)} Days)'

    total_energy = round(sum(energy_series), 3)

    # Calculate appliance distribution for pie chart
    appliance_breakdown = defaultdict(float)
    for record in records_all:
        energy = record.hours_used * record.appliance.power_rating / 1000
        appliance_breakdown[record.appliance.name] += energy
    
    # Prepare appliance data for pie chart
    appliance_names = list(appliance_breakdown.keys())
    appliance_energies = [round(val, 3) for val in appliance_breakdown.values()]

    return render(request, 'dashboard/charts.html', {
        'chart_title': chart_title,
        'labels_json': json.dumps(labels),
        'energy_series_json': json.dumps(energy_series),
        'appliance_names_json': json.dumps(appliance_names),
        'appliance_energies_json': json.dumps(appliance_energies),
        'period': period,
        'profiles': user_residents.order_by('profile_name'),
        'selected_profile': int(profile_id) if profile_id.isdigit() else None,
        'first_record_date': first_record_date,
        'measured_start': measured_start,
        'measured_end': measured_end,
        'total_energy': total_energy,
        'chart_period': period,
    })


@login_required
def alerts(request):
    alerts_qs = Alert.objects.filter(user=request.user).order_by('-date_created')
    return render(request, 'dashboard/alerts.html', {'alerts': alerts_qs})


@login_required
@login_required
def export(request):
    return render(request, 'dashboard/export.html')


@login_required
def export_csv(request):
    import csv
    from django.http import HttpResponse

    user_residents = Resident.objects.filter(user=request.user)
    records = UsageRecord.objects.filter(appliance__resident__in=user_residents).select_related('appliance').order_by('-date')

    q = (request.GET.get('q') or '').strip()
    appliance_id = request.GET.get('appliance') or ''
    date_from = request.GET.get('date_from') or ''
    date_to = request.GET.get('date_to') or ''

    from django.db.models import Q
    if q:
        records = records.filter(Q(appliance__name__icontains=q) | Q(date__icontains=q))

    if appliance_id:
        records = records.filter(appliance__id=appliance_id)
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usage_records.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Appliance', 'Hours Used', 'Energy (kWh)', 'Estimated Cost (MUR)'])

    for r in records:
        energy = r.hours_used * r.appliance.power_rating / 1000
        cost = energy * 5
        writer.writerow([r.date, r.appliance.name, r.hours_used, round(energy,2), round(cost,2)])

    return response


@login_required
def export_pdf(request):
    """Professional PDF export with attractive theme, charts, and comprehensive analysis."""
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.textlabels import Label
    from reportlab.graphics import renderPDF
    from django.http import HttpResponse
    import io
    from datetime import datetime
    from collections import defaultdict

    user_residents = Resident.objects.filter(user=request.user)
    records = UsageRecord.objects.filter(appliance__resident__in=user_residents).select_related('appliance').order_by('-date')

    # Get summary data for charts
    appliance_breakdown = defaultdict(float)
    total_energy = 0
    total_cost = 0
    
    for r in records:
        energy = r.hours_used * r.appliance.power_rating / 1000
        cost = energy * 5
        total_energy += energy
        total_cost += cost
        appliance_breakdown[r.appliance.name] += energy

    # Prepare data for charts
    appliance_names = list(appliance_breakdown.keys())
    appliance_energies = [round(val, 2) for val in appliance_breakdown.values()]
    
    # Get recent data for bar chart (last 7 days)
    recent_records = records[:7] if records.count() > 7 else records
    recent_dates = [str(r.date) for r in recent_records]
    recent_energies = [round(r.hours_used * r.appliance.power_rating / 1000, 2) for r in recent_records]

    # Create PDF with professional styling
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Professional color scheme
    PRIMARY_COLOR = colors.HexColor('#2563eb')  # Modern blue
    SECONDARY_COLOR = colors.HexColor('#1e40af')  # Darker blue
    ACCENT_COLOR = colors.HexColor('#f59e0b')   # Amber
    TEXT_COLOR = colors.HexColor('#1f2937')     # Dark gray
    LIGHT_TEXT = colors.HexColor('#6b7280')     # Medium gray

    # Hex strings for use in Paragraph markup (colors objects can't be used in HTML-like markup)
    HEX_COLORS = [
        '#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#a855f7',
        '#06b6d4', '#eab308', '#ec4899', '#14b8a6', '#f97316',
    ]
    
    # Custom styles for professional look — use unique names to avoid conflicts with defaults
    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontSize=24,
        leading=30,
        alignment=1,  # Center
        textColor=PRIMARY_COLOR,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='ReportHeading1',
        fontSize=16,
        leading=20,
        textColor=SECONDARY_COLOR,
        fontName='Helvetica-Bold',
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='ReportHeading2',
        fontSize=14,
        leading=18,
        textColor=TEXT_COLOR,
        fontName='Helvetica-Bold',
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='ReportBodyText',
        fontSize=11,
        leading=16,
        textColor=TEXT_COLOR,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='ReportHighlight',
        fontSize=12,
        leading=16,
        textColor=ACCENT_COLOR,
        fontName='Helvetica-Bold'
    ))

    # Document content
    story = []

    # Cover Page with Header
    story.append(Paragraph("HOUSEHOLD ELECTRICITY USAGE REPORT", styles['ReportTitle']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['ReportBodyText']))
    story.append(Paragraph(f"Generated for: {request.user.username}", styles['ReportBodyText']))
    story.append(Spacer(1, 30))
    
    # Executive Summary Section
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['ReportHeading1']))
    
    # Summary Statistics with Professional Styling
    summary_data = [
        ['Total Energy Consumption', f'{round(total_energy, 2)} kWh'],
        ['Total Cost', f'MUR {round(total_cost, 2)}'],
        ['Number of Appliances', str(len(appliance_breakdown))],
        ['Number of Records', str(records.count())],
        ['Report Period', 'All Time'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Key Metrics Highlight
    if total_energy > 0:
        avg_daily = total_energy / max(1, records.count())
        story.append(Paragraph("KEY METRICS", styles['ReportHeading2']))
        metrics_text = f"""
        <b>Average Daily Consumption:</b> {round(avg_daily, 2)} kWh<br/>
        <b>Cost per kWh:</b> MUR {round(total_cost/total_energy, 2) if total_energy > 0 else 0}<br/>
        <b>Most Used Appliance:</b> {max(appliance_breakdown, key=appliance_breakdown.get) if appliance_breakdown else 'N/A'}
        """
        story.append(Paragraph(metrics_text, styles['ReportBodyText']))
    story.append(Spacer(1, 20))

    # Charts Section - Energy Distribution Pie Chart (large and clear)
    story.append(Paragraph("ENERGY ANALYSIS", styles['ReportHeading1']))
    
    if appliance_names:
        # Create large, professional pie chart
        drawing = Drawing(450, 350)  # Reduced size to fit page
        
        # Large title for the chart
        title = String(10, 380, "Appliance Energy Distribution", fontSize=16, fontName='Helvetica-Bold', fillColor=TEXT_COLOR)
        drawing.add(title)
        
        # Large pie chart
        pie = Pie()
        pie.x = 80
        pie.y = 80
        pie.width = 250  # Increased from 200
        pie.height = 250  # Increased from 200
        pie.data = appliance_energies
        pie.labels = None  # Remove overlapping labels from pie slices
        pie.slices.strokeWidth = 2
        pie.slices.strokeColor = colors.white
        
        # Professional color palette
        colors_list = [
            colors.HexColor('#2563eb'),  # Blue
            colors.HexColor('#16a34a'),  # Green
            colors.HexColor('#f59e0b'),  # Amber
            colors.HexColor('#ef4444'),  # Red
            colors.HexColor('#a855f7'),  # Purple
            colors.HexColor('#06b6d4'),  # Cyan
            colors.HexColor('#eab308'),  # Yellow
            colors.HexColor('#ec4899'),  # Pink
            colors.HexColor('#14b8a6'),  # Teal
            colors.HexColor('#f97316'),  # Orange
        ]
        
        # Apply colors to slices
        for i in range(len(appliance_energies)):
            if i < len(colors_list):
                pie.slices[i].fillColor = colors_list[i]
        
        drawing.add(pie)
        
        # Create separate legend below the chart with better formatting
        legend_y = 50
        legend_title = String(10, legend_y + 25, "Energy Distribution by Appliance", fontSize=14, fontName='Helvetica-Bold', fillColor=TEXT_COLOR)
        drawing.add(legend_title)
        
        total = sum(appliance_energies) if appliance_energies else 1
        sorted_items = sorted(zip(appliance_names, appliance_energies), key=lambda x: x[1], reverse=True)
        
        # Create legend items with better spacing and formatting
        for i, (name, energy) in enumerate(sorted_items[:8]):  # Limit to top 8 for space
            percentage = (energy / total) * 100
            y_pos = legend_y - (i * 18)
            
            # Color box
            color_box = Rect(10, y_pos - 3, 12, 12, fillColor=colors_list[i % len(colors_list)], strokeColor=colors.black, strokeWidth=1)
            drawing.add(color_box)
            
            # Appliance name and data
            legend_text = String(28, y_pos, f"{name}", fontSize=11, fontName='Helvetica-Bold', fillColor=TEXT_COLOR)
            drawing.add(legend_text)
            
            # Energy and percentage on next line
            energy_text = String(28, y_pos - 12, f"{energy:.2f} kWh ({percentage:.1f}%)", fontSize=10, fontName='Helvetica', fillColor=TEXT_COLOR)
            drawing.add(energy_text)
        
        story.append(drawing)
        
        story.append(drawing)
    
    story.append(Spacer(1, 20))

    # Detailed Data Table with Professional Styling
    story.append(Paragraph("DETAILED USAGE RECORDS", styles['ReportHeading1']))
    
    # Prepare table data with headers
    table_data = [['Date', 'Appliance', 'Hours Used', 'Energy (kWh)', 'Cost (MUR)']]
    for r in records[:50]:  # Limit to first 50 records
        energy = r.hours_used * r.appliance.power_rating / 1000
        cost = energy * 5
        table_data.append([
            str(r.date),
            r.appliance.name,
            f"{r.hours_used}",
            f"{energy:.2f}",
            f"{cost:.2f}"
        ])
    
    # Add summary row with highlighting
    table_data.append(['', '', '', f"Total: {round(total_energy, 2)}", f"Total: {round(total_cost, 2)}"])
    
    # Create professional table
    col_widths = [1.2*inch, 1.8*inch, 1*inch, 1.2*inch, 1.2*inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ffffff')),
        ('TEXTCOLOR', (0, 1), (-1, -2), TEXT_COLOR),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
        
        # Summary row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, -1), (-1, -1), SECONDARY_COLOR),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # Professional Recommendations
    story.append(Paragraph("RECOMMENDATIONS", styles['ReportHeading1']))
    recommendations = []
    
    if total_energy > 100:
        recommendations.append("Consider energy-efficient appliances to reduce consumption.")
    if len(appliance_breakdown) > 5:
        recommendations.append("Monitor high-consumption appliances more closely.")
    if total_cost > 500:
        recommendations.append("Review usage patterns during peak hours.")
    
    # Add specific recommendations based on data
    if appliance_breakdown:
        max_appliance = max(appliance_breakdown, key=appliance_breakdown.get)
        recommendations.append(f"Consider optimizing usage of {max_appliance} which has the highest consumption.")
    
    if not recommendations:
        recommendations.append("Your energy usage is within normal ranges. Continue monitoring for optimal efficiency.")
    
    for i, rec in enumerate(recommendations, 1):
        story.append(Paragraph(f"{i}. {rec}", styles['ReportBodyText']))
    
    story.append(Spacer(1, 15))
    
    # Footer with contact information
    story.append(Paragraph("For more detailed analysis and real-time monitoring, visit your dashboard.", styles['ReportBodyText']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Report generated by Household Electricity Dashboard", styles['ReportHighlight']))

    # Build PDF
    doc.build(story)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="electricity_usage_report.pdf"'
    return response


@login_required
def delete_appliance(request, appliance_id):
    appliance = get_object_or_404(Appliance, id=appliance_id)
    appliance.delete()
    return redirect('dashboard:appliances')


@login_required
def critical_appliances(request):
    appliances_list = Appliance.objects.filter(is_critical=True)
    return render(request, 'dashboard/critical_appliances.html', {'appliances': appliances_list})


@login_required
def add_usage_record(request):
    from .forms import UsageRecordForm

    user_residents = Resident.objects.filter(user=request.user)
    default_resident = user_residents.filter(is_default=True).first() or user_residents.first()

    if request.method == 'POST':
        form = UsageRecordForm(request.POST, user=request.user)
        if form.is_valid():
            appliance = form.cleaned_data.get('appliance')
            appliance_name = (form.cleaned_data.get('appliance_name') or '').strip()

            # If appliance not selected but a name provided, try to find or create it
            if not appliance and appliance_name:
                # Case-insensitive match within this user's default resident profile
                appliance = Appliance.objects.filter(name__iexact=appliance_name, resident=default_resident).first()
                if not appliance:
                    if not default_resident:
                        messages.error(request, 'No resident profile to associate the new appliance with. Create a profile first.')
                        return render(request, 'dashboard/add_usage_record.html', {'form': form})
                    appliance = Appliance.objects.create(
                        resident=default_resident,
                        name=appliance_name,
                        power_rating=100.0,
                        threshold_hours=8.0,
                    )
                    messages.info(request, f"Created appliance '{appliance.name}' for profile '{default_resident.profile_name}'.")

            if not appliance:
                form.add_error('appliance', 'Select an appliance or provide a new appliance name.')
            else:
                usage = form.save(commit=False)
                usage.appliance = appliance
                usage.save()

                # Ensure newly-created appliance is mirrored immediately to MySQL (best-effort)
                from .models import mirror_appliance_to_mysql
                try:
                    mirror_appliance_to_mysql(sender=Appliance, instance=appliance, created=True)
                except Exception:
                    # ignore failures here; signal handles it too
                    pass

                messages.success(request, 'Usage record added successfully.')
                return redirect('dashboard:usage_records')
        else:
            messages.error(request, 'Please fix the errors in the form below.')
    else:
        form = UsageRecordForm(user=request.user)
    return render(request, 'dashboard/add_usage_record.html', {'form': form})


@login_required
def edit_usage_record(request, record_id):
    from .forms import UsageRecordForm

    usage = get_object_or_404(UsageRecord, id=record_id)
    # Ensure the record belongs to the current user via resident->appliance
    if usage.appliance.resident.user != request.user:
        return redirect('dashboard:usage_records')

    user_residents = Resident.objects.filter(user=request.user)
    default_resident = user_residents.filter(is_default=True).first() or user_residents.first()

    if request.method == 'POST':
        form = UsageRecordForm(request.POST, instance=usage, user=request.user)
        if form.is_valid():
            appliance = form.cleaned_data.get('appliance')
            appliance_name = (form.cleaned_data.get('appliance_name') or '').strip()

            # If appliance not selected but a name provided, try to find or create it
            if not appliance and appliance_name:
                appliance = Appliance.objects.filter(name__iexact=appliance_name, resident=default_resident).first()
                if not appliance:
                    if not default_resident:
                        messages.error(request, 'No resident profile to associate the new appliance with. Create a profile first.')
                        return render(request, 'dashboard/edit_usage_record.html', {'form': form, 'usage': usage})
                    appliance = Appliance.objects.create(
                        resident=default_resident,
                        name=appliance_name,
                        power_rating=100.0,
                        threshold_hours=8.0,
                    )
                    messages.info(request, f"Created appliance '{appliance.name}' for profile '{default_resident.profile_name}'.")

            if not appliance:
                form.add_error('appliance', 'Select an appliance or provide a new appliance name.')
            else:
                usage = form.save(commit=False)
                usage.appliance = appliance
                usage.save()
                messages.success(request, 'Usage record updated successfully.')
                return redirect('dashboard:usage_records')
        else:
            messages.error(request, 'Please fix the errors in the form below.')
    else:
        form = UsageRecordForm(instance=usage, user=request.user)

    return render(request, 'dashboard/edit_usage_record.html', {'form': form, 'usage': usage})


@login_required
def delete_usage_record(request, record_id):
    record = get_object_or_404(UsageRecord, id=record_id)
    record.delete()
    return redirect('dashboard:usage_records')


@login_required
def mark_alert_read(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    alert.is_read = True
    alert.save(update_fields=['is_read'])
    return redirect('dashboard:index')


@login_required
def send_manual_alert(request, profile_id):
    resident = get_object_or_404(Resident, id=profile_id, user=request.user)

    # Determine high-usage appliances for this resident over the past 24 hours
    from django.utils import timezone
    cutoff = timezone.now().date() - timedelta(days=1)

    appliances = Appliance.objects.filter(resident=resident)
    high_usage = []
    for appliance in appliances:
        recent_hours = UsageRecord.objects.filter(appliance=appliance, date__gte=cutoff).aggregate(total_hours=__import__('django.db.models').db.models.Sum('hours_used'))['total_hours'] or 0
        if recent_hours > appliance.threshold_hours:
            high_usage.append((appliance, recent_hours))

    if high_usage:
        message_lines = [f"High usage detected for the following appliances at profile '{resident.profile_name}':"]
        for app, hours in high_usage:
            energy = hours * app.power_rating / 1000
            message_lines.append(f"- {app.name}: {hours:.1f}h (approx {energy:.2f} kWh) - threshold {app.threshold_hours}h")
        message_lines.append("\nPlease review these appliances and consider reducing usage or checking for inefficiencies.")
        message = "\n".join(message_lines)
        alert_type = 'HIGH_USAGE'
    else:
        message = f"Manual alert: No appliances are exceeding thresholds for profile '{resident.profile_name}'."
        alert_type = 'MANUAL'

    # Record alert
    alert = Alert.objects.create(user=request.user, appliance=high_usage[0][0] if high_usage else None, message=message, alert_type=alert_type)

    # Prefer async dispatch: WhatsApp first, then email fallback
    subject = f"Electricity Alert - {alert_type.replace('_',' ').title()}"
    sent = False
    send_errors = []

    try:
        result = dispatch_alert_notification_task.delay(alert.id, resident.id)
        # In eager mode result is available immediately; otherwise task runs in worker.
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            payload = result.get(timeout=10)
            sent = bool(payload.get('success'))
        else:
            sent = True
    except Exception as e:
        send_errors.append(str(e))

    # Local synchronous fallback if async dispatch failed
    if not sent:
        try:
            from django.core.mail import EmailMessage
            email_msg = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[resident.email], reply_to=[resident.email])
            email_msg.send(fail_silently=False)
            sent = True
            alert.email_sent = True
            alert.save(update_fields=['email_sent'])
        except Exception as e:
            send_errors.append(str(e))

    # Try SMS as well (best-effort)
    try:
        if resident.phone and getattr(settings, 'TWILIO_ACCOUNT_SID', None):
            from .utils import send_sms
            sms_body = f"Alert: {alert_type.replace('_',' ').title()} - {message[:140]}"
            send_sms(resident.phone, sms_body)
    except Exception as e:
        print(f"SMS send failed: {e}")

    # Return JSON for AJAX calls, otherwise redirect
    if request.headers.get('Accept') == 'application/json' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        if sent:
            return JsonResponse({'success': True, 'message': 'Alert sent successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send alert. Errors: ' + '; '.join(send_errors)})

    if sent:
        messages.success(request, 'Alert sent successfully.')
    else:
        messages.error(request, 'Failed to send alert. Check server logs for details.')

    return redirect('dashboard:resident_profiles')


@login_required
def check_usage_alerts(request):
    """Check usage for all residents and send alerts to those exceeding thresholds."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    from django.utils import timezone
    import calendar

    threshold = float(request.POST.get('threshold', 100.0))
    current_year = timezone.now().year
    current_month = timezone.now().month

    residents = Resident.objects.filter(is_active=True, user=request.user)
    alerts_sent = 0
    high_usage_residents = []
    errors = []

    for resident in residents:
        try:
            monthly_usage = resident.get_monthly_usage(current_year, current_month)

            if monthly_usage['total_energy'] >= threshold:
                # Check if alert already exists for this month
                existing_alert = Alert.objects.filter(
                    user=resident.user,
                    alert_type='HIGH_USAGE',
                    date_created__year=current_year,
                    date_created__month=current_month
                ).exists()

                if not existing_alert:
                    # Create alert in database
                    alert = Alert.objects.create(
                        user=resident.user,
                        message=f'High Usage Alert - {monthly_usage["month_name"]} {current_year}: Your electricity usage has exceeded {threshold} kWh. '
                               f'Total usage: {monthly_usage["total_energy"]} kWh, '
                               f'Estimated cost: MUR {monthly_usage["total_cost"]}. '
                               f'Please review your consumption patterns.',
                        alert_type='HIGH_USAGE',
                        is_read=False
                    )

                    # Send alert via email/WhatsApp/SMS
                    try:
                        result = dispatch_alert_notification_task.delay(alert.id, resident.id)
                        # For immediate response, we assume success since it's async
                        alerts_sent += 1
                        high_usage_residents.append({
                            'name': resident.full_name,
                            'usage': round(monthly_usage['total_energy'], 2),
                            'cost': round(monthly_usage['total_cost'], 2),
                            'email_failed': False  # We'll assume success for now
                        })
                    except Exception as e:
                        errors.append(f'Failed to send alert to {resident.full_name}: {str(e)}')
                else:
                    # Alert already exists
                    high_usage_residents.append({
                        'name': resident.full_name,
                        'usage': round(monthly_usage['total_energy'], 2),
                        'cost': round(monthly_usage['total_cost'], 2),
                        'email_failed': False,
                        'already_alerted': True
                    })

        except Exception as e:
            errors.append(f'Error processing {resident.full_name}: {str(e)}')

    message = f'Checked {len(residents)} resident profiles for {calendar.month_name[current_month]} {current_year}.\n\n'
    message += f'Usage threshold: {threshold} kWh\n'
    message += f'Alerts sent: {alerts_sent}\n'
    message += f'Residents with high usage: {len([r for r in high_usage_residents if not r.get("already_alerted", False)])}'

    if errors:
        message += f'\n\nErrors: {"; ".join(errors)}'

    return JsonResponse({
        'success': True,
        'message': message,
        'alerts_sent': alerts_sent,
        'high_usage_residents': high_usage_residents,
        'errors': errors
    })


@login_required
def send_test_email(request, profile_id):
    """Send a simple test email using the resident's SMTP credentials (or fallback to project SMTP)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    resident = get_object_or_404(Resident, id=profile_id, user=request.user)

    subject = "Test email from Household Electricity Dashboard"
    message = f"This is a test email for resident profile: {resident.profile_name}. If you received this, SMTP configuration is valid."
    sent = False
    errors = []

    try:
        if resident.email and resident.email_password:
            sent = resident.send_alert(subject, message)
    except Exception as e:
        errors.append(str(e))

    if not sent:
        try:
            from django.core.mail import EmailMessage
            email_msg = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[resident.email], reply_to=[resident.email])
            email_msg.send(fail_silently=False)
            sent = True
        except Exception as e:
            errors.append(str(e))

    if sent:
        return JsonResponse({'success': True, 'message': 'Test email sent successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Failed to send test email. Errors: ' + '; '.join(errors)}, status=500)


@login_required
def send_sms_alert(request):
    """Send SMS alert to resident profile or hardcoded number. Supports profile_id param."""
    profile_id = request.GET.get('profile_id') or request.POST.get('profile_id')
    twilio_configured = all([
        getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
        getattr(settings, 'TWILIO_AUTH_TOKEN', ''),
        getattr(settings, 'TWILIO_FROM_NUMBER', '')
    ])
    
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        message = request.POST.get('message', '').strip()
        
        if profile_id:
            resident = get_object_or_404(Resident, id=profile_id, user=request.user)
            phone = resident.phone
            profile_name = resident.profile_name
            # Build high-usage message if not provided
            if not message:
                cutoff = timezone.now().date() - timedelta(days=1)
                appliances = Appliance.objects.filter(resident=resident)
                high_usage = []
                for appliance in appliances:
                    recent_hours = UsageRecord.objects.filter(
                        appliance=appliance, date__gte=cutoff
                    ).aggregate(total_hours=Sum('hours_used'))['total_hours'] or 0
                    if recent_hours > appliance.threshold_hours:
                        high_usage.append((appliance.name, recent_hours))
                
                if high_usage:
                    msg_lines = [f"🚨 HIGH USAGE ALERT - Profile: {profile_name}"]
                    for name, hours in high_usage[:3]:  # Top 3
                        msg_lines.append(f"• {name}: {hours:.1f}h (threshold exceeded)")
                    msg_lines.append("Review appliances to save energy!")
                    message = ' '.join(msg_lines)[:160]
                else:
                    message = f"Electricity alert for {profile_name}. All usage normal."
            phone = resident.phone
            
            if not phone:
                messages.error(request, f"No phone number for profile '{profile_name}'.")
                return redirect('dashboard:high_usage_sms')
        else:
            phone = request.POST.get('phone', '58068426')
        
        if not message:
            message = 'Electricity usage alert from dashboard.'
        
        sent = send_sms(phone, message)
        if sent:
            messages.success(request, f'✅ SMS sent to {phone}.')
        else:
            messages.error(request, f'❌ SMS failed to {phone}. Check Twilio config.')
        
        if profile_id:
            return redirect('dashboard:high_usage_sms')
        return redirect('dashboard:send_sms_alert')
    
    # GET: Show context for high-usage page or standalone
    residents = Resident.objects.filter(user=request.user).order_by('profile_name')
    context = {
        'residents': residents,
        'twilio_configured': twilio_configured,
        'twilio_account_sid': getattr(settings, 'TWILIO_ACCOUNT_SID', '')[:10] + '...' if getattr(settings, 'TWILIO_ACCOUNT_SID', '') else 'Not configured',
        'twilio_from_number': getattr(settings, 'TWILIO_FROM_NUMBER', ''),
    }
    if profile_id:
        resident = get_object_or_404(Resident, id=profile_id, user=request.user)
        context['resident'] = resident
        context['phone'] = resident.phone or ''
    
    return render(request, 'dashboard/send_sms_alert.html', context)


@login_required
def high_usage_sms_dashboard(request):
    """Dashboard showing high usage appliances grouped by resident profile + SMS buttons."""
    from django.db.models import Sum
    
    cutoff = timezone.now().date() - timedelta(days=1)
    user_residents = Resident.objects.filter(user=request.user).select_related().order_by('profile_name')
    
    profile_data = []
    twilio_configured = all([
        getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
        getattr(settings, 'TWILIO_AUTH_TOKEN', ''),
        getattr(settings, 'TWILIO_FROM_NUMBER', '')
    ])
    
    for resident in user_residents:
        appliances = Appliance.objects.filter(resident=resident).prefetch_related('usagerecord_set')
        high_usage = []
        
        for appliance in appliances:
            recent_hours = UsageRecord.objects.filter(
                appliance=appliance, date__gte=cutoff
            ).aggregate(total_hours=Sum('hours_used'))['total_hours'] or 0
            
            if recent_hours and recent_hours > appliance.threshold_hours:
                energy_kwh = (recent_hours * appliance.power_rating) / 1000
                high_usage.append({
                    'appliance': appliance,
                    'hours': round(recent_hours, 1),
                    'energy_kwh': round(energy_kwh, 2),
                    'threshold': appliance.threshold_hours
                })
        
        if high_usage:  # Only show profiles with high usage
            profile_data.append({
                'resident': resident,
                'high_usage': high_usage,
                'phone': resident.phone or None,
                'total_high_appliances': len(high_usage)
            })
    
    context = {
        'profile_data': profile_data,
        'cutoff_date': cutoff.strftime('%Y-%m-%d'),
        'twilio_configured': twilio_configured,
        'no_high_usage': len(profile_data) == 0,
        'twilio_status': 'Configured' if twilio_configured else 'Configure in .env',
    }
    return render(request, 'dashboard/high_usage_sms_dashboard.html', context)


# ========================
# APPLIANCE DETECTION VIEWS
# ========================

@login_required
def appliance_detection_view(request):
    """Display appliance detection interface."""
    appliance_info = get_current_appliance_info()
    
    context = {
        'appliance_info': appliance_info,
        'available_types': get_available_appliance_types(),
    }
    return render(request, 'dashboard/appliance_detection.html', context)

@login_required
def identify_appliance_view(request):
    """Manually identify the appliance plugged into the smart plug."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    appliance_type = request.POST.get('appliance_type')
    custom_name = request.POST.get('custom_name', '').strip()
    
    if not appliance_type:
        return JsonResponse({'success': False, 'message': 'Appliance type is required'}, status=400)

    result = identify_appliance_manually(appliance_type, custom_name if custom_name else None)
    
    if result['success']:
        messages.success(request, f"Appliance identified as: {result['appliance']['description']}")
    else:
        messages.error(request, f"Failed to identify appliance: {result.get('error', 'Unknown error')}")
    
    return JsonResponse(result)

@login_required
@require_GET
def get_appliance_info_api(request):
    """API endpoint to get current appliance information."""
    appliance_info = get_current_appliance_info()
    return JsonResponse({
        'success': True,
        'appliance_info': appliance_info
    })

# ========================
# ALERT CONFIRMATION VIEWS
# ========================

@login_required
def alert_confirmation_view(request, alert_id):
    """Display alert confirmation interface."""
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    
    # Create confirmation record if it doesn't exist
    confirmation, created = alert.confirmation.get_or_create(
        defaults={
            'user_confirmed': False,
            'confirmation_method': 'DASHBOARD'
        }
    )
    
    context = {
        'alert': alert,
        'confirmation': confirmation,
        'appliance_info': get_current_appliance_info() if alert.appliance else None,
    }
    return render(request, 'dashboard/alert_confirmation.html', context)

@login_required
def confirm_alert(request, alert_id):
    """Confirm an alert via dashboard."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    
    # Create or update confirmation
    confirmation, created = alert.confirmation.get_or_create(
        defaults={
            'user_confirmed': True,
            'confirmed_at': timezone.now(),
            'confirmation_method': 'DASHBOARD'
        }
    )
    
    if not created:
        confirmation.user_confirmed = True
        confirmation.confirmed_at = timezone.now()
        confirmation.confirmation_method = 'DASHBOARD'
        confirmation.save()
    
    # Update alert status
    alert.confirmed_at = timezone.now()
    alert.requires_confirmation = False
    alert.save()
    
    messages.success(request, 'Alert confirmed successfully.')
    return JsonResponse({'success': True, 'message': 'Alert confirmed successfully.'})

@login_required
def dismiss_alert(request, alert_id):
    """Dismiss an alert without confirmation."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    
    # Mark as read but don't require confirmation
    alert.is_read = True
    alert.requires_confirmation = False
    alert.save()
    
    messages.success(request, 'Alert dismissed.')
    return JsonResponse({'success': True, 'message': 'Alert dismissed.'})

@login_required
def send_alert_confirmation_sms(request, alert_id):
    """Send SMS with confirmation link for an alert."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    resident = Resident.objects.filter(user=request.user, is_default=True).first() or \
               Resident.objects.filter(user=request.user, is_active=True).first()
    
    if not resident or not resident.phone:
        return JsonResponse({'success': False, 'message': 'No phone number available for SMS confirmation'}, status=400)
    
    # Generate confirmation URL
    confirmation_url = request.build_absolute_uri(f'/alert-confirmation/{alert.id}/')
    
    sms_body = f"Electricity Alert: {alert.appliance.name if alert.appliance else 'Unknown'}\n{alert.message[:200]}...\n\nConfirm: {confirmation_url}\nDismiss: {confirmation_url}?action=dismiss"
    
    if send_sms(resident.phone, sms_body):
        alert.requires_confirmation = True
        alert.save()
        return JsonResponse({'success': True, 'message': 'SMS confirmation sent successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Failed to send SMS confirmation'}, status=500)

@login_required
def alerts_with_confirmation(request):
    """Display alerts that require confirmation."""
    alerts = Alert.objects.filter(
        user=request.user, 
        requires_confirmation=True,
        is_read=False
    ).select_related('appliance').order_by('-date_created')
    
    context = {
        'alerts': alerts,
        'pending_confirmations': True,
    }
    return render(request, 'dashboard/alerts_with_confirmation.html', context)
