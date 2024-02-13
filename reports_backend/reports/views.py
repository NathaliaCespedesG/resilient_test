from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from Withings_ScanWatch.Main import Resilient

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
        # Assuming reports is a list of dictionaries or any serializable objects
        return JsonResponse({'reports': reports})

