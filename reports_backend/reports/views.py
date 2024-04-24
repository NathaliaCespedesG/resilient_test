from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from Withings_ScanWatch.Resilient import Resilient

# Create your views here.
# request -- response (reuest handler)
resilient_generator = Resilient()

@api_view(['GET'])

class IndividualReportView:
    
    def get(self, request, user_id):

        report = resilient_generator.individual_report_generation()

        return JsonResponse(report)
    
@api_view(['GET'])
class AllReportsView: 

    def get(self, request):

        reports = resilient_generator.individual_report_generation()
        # Urls
        return JsonResponse(reports)

