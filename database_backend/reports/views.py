from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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