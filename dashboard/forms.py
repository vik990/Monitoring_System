from django import forms
from django.utils import timezone
from .models import Appliance, UsageRecord, Resident

class ApplianceForm(forms.ModelForm):
    class Meta:
        model = Appliance
        fields = ['name', 'power_rating', 'threshold_hours', 'is_critical', 'priority_level']

class UsageRecordForm(forms.ModelForm):
    # Allow entering a free-text appliance name; if provided and the appliance doesn't exist,
    # we'll auto-create it associated with the user's default resident profile.
    appliance_name = forms.CharField(
        required=False,
        label='New Appliance (optional)',
        help_text='Enter a new appliance name to auto-create it and associate with the default profile.'
    )

    class Meta:
        model = UsageRecord
        fields = ['appliance', 'appliance_name', 'date', 'hours_used']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept an optional `user` kwarg to limit the appliance queryset to the user's appliances
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Default date to today for new measurement entries
        if not self.is_bound and not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        if user is not None:
            # Limit appliances to those belonging to this user's residents
            self.fields['appliance'].queryset = Appliance.objects.filter(resident__user=user).order_by('name')

class ResidentForm(forms.ModelForm):
    email_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter email password for alerts'}),
        required=False,
        help_text="Password for your email account (used to send usage alerts)"
    )

    class Meta:
        model = Resident
        fields = ['profile_name', 'full_name', 'email', 'email_password', 'phone', 'address', 'household_size', 'is_default']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
