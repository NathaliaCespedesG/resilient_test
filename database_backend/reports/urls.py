from django.urls import path
from .views import *

app_name = 'reports'

urlpatterns = [
    path('withings-credentials/', WithingsCredentials.as_view(), name='report-list-create'),
]
