from django.urls import path
from .views import *

app_name  = 'reports'

urlpatterns = [
    #Endpoint for the individual reports
    path('individual_report/<int:report_id>', IndividualReportView.as_view(), name='individual-report'),

    #Endpoint for multiple reports
    path('all_reports/', AllReportsView.as_view(), name = 'all-reports' )
]