from django.urls import path
from .views import *

app_name  = 'reports'

urlpatterns = [
    #Endpoint for the url receiver
    path('receive-url/', ReceiveUrlView.as_view(), name='receive_url'),   
]