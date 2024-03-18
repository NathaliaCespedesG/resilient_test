from django.test import TestCase
from django.urls import reverse
from .models import Report


# Create your tests here.
class ReportAPITest(TestCase):
    def setUp(self):
        # Create sample data for testing
        self.report1 = Report.objects.create(title='Report 1', content='Sample content 1')
        self.report2 = Report.objects.create(title='Report 2', content='Sample content 2')

    def test_individual_report(self):
        # Test individual report endpoint
        response = self.client.get(reverse('individual_report', kwargs={'report_id': self.report1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['report']['title'], 'Report 1')

    def test_all_reports(self):
        # Test all reports endpoint
        response = self.client.get(reverse('all_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['reports']), 2)  # Assuming two reports are created in setUp()

    def test_invalid_report(self):
        # Test endpoint with invalid report ID
        response = self.client.get(reverse('individual_report', kwargs={'report_id': 999}))
        self.assertEqual(response.status_code, 404)