from django.urls import path
from .views import *

app_name  = 'reports'

urlpatterns = [
    path('example/<str:param>', example_view, name='example-view'),
]