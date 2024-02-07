from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view

# Create your views here.
@api_view(['GET'])
def example_view(request, param):
    response  = {
        'response': 'You called /example_view with param: ' + param
    }
    return JsonResponse(response)