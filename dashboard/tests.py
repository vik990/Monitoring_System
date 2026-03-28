from django.test import TestCase
from .models import Appliance, UsageRecord
from django.urls import reverse

class ApplianceModelTest(TestCase):
    def setUp(self):
        self.appliance = Appliance.objects.create(name="Washing Machine", power_rating=500)

    def test_appliance_creation(self):
        self.assertEqual(self.appliance.name, "Washing Machine")
        self.assertEqual(self.appliance.power_rating, 500)

class UsageRecordModelTest(TestCase):
    def setUp(self):
        self.appliance = Appliance.objects.create(name="Washing Machine", power_rating=500)
        self.usage_record = UsageRecord.objects.create(date="2023-01-01", hours_used=2, appliance=self.appliance)

    def test_usage_record_creation(self):
        self.assertEqual(self.usage_record.date, "2023-01-01")
        self.assertEqual(self.usage_record.hours_used, 2)
        self.assertEqual(self.usage_record.appliance, self.appliance)

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.appliance = Appliance.objects.create(name="Washing Machine", power_rating=500)
        self.usage_record = UsageRecord.objects.create(date="2023-01-01", hours_used=2, appliance=self.appliance)

    def test_index_view(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_appliances_view(self):
        response = self.client.get(reverse('dashboard:appliances'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/appliances.html')

    def test_usage_records_view(self):
        response = self.client.get(reverse('dashboard:usage_records'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/usage_records.html')