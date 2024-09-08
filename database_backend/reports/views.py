from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from Withings_ScanWatch.Resilient import Resilient

import json

@method_decorator(csrf_exempt, name='dispatch')
class WithingsCredentials(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            # Process the data here
            # For demonstration, we'll just print it and send it back in the response
            print(data)
            return JsonResponse({'status': 'success', 'data': data})
        #HERE SHOULD BE THE CODE TO UNDERSTAND THE CALLBACK URL
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class ReportGeneration(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)  # Parse JSON from request body
            report_type = data.get('report_type', 'all')  # Get report type from the payload
            
            #Trigger the report generation based on report_type
            if report_type not in ['all', 'single']:
                return JsonResponse({'status': 'error', 'message': 'Invalid report type'}, status=400)

            #Answer from Resilient generation
            report_generator = Resilient(report_type = report_type)
            report = report_generator.individual_report_generation()

            return JsonResponse({'status': 'success', 'report': report})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)

    def get(self, request, *args, **kwargs):
        # Handle a callback URL or another case for a GET request
        callback_param = request.GET.get('callback', None)
        
        if callback_param:
            # Perform the necessary actions for the callback
            return JsonResponse({'status': 'success', 'callback': callback_param})
        
        return JsonResponse({'status': 'error', 'message': 'Invalid request method or missing callback'}, status=405)