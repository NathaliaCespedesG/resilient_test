from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from .filters import *
import uuid

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"users": serializer.data})

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class DeviceListCreateView(generics.ListCreateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filterset_class = DeviceFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"devices": serializer.data})

class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

class ScaleListCreateView(generics.ListCreateAPIView):
    queryset = Scale.objects.all()
    serializer_class = ScaleSerializer
    filterset_class = ScaleFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"scales": serializer.data})
    
class ScaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Scale.objects.all()
    serializer_class = ScaleSerializer
    
class ScanWatchIntraActivityListCreateView(generics.ListCreateAPIView):
    queryset = ScanWatch_IntraActivity.objects.all()
    serializer_class = ScanWatch_IntraActivitySerializer
    filterset_class = ScanWatch_IntraActivityFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"scanwatches_intraactivity": serializer.data})
    
class ScanWatchIntraActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Scale.objects.all()
    serializer_class = ScanWatch_IntraActivitySerializer

class ScanWatchSummaryListCreateView(generics.ListCreateAPIView):
    queryset = ScanWatch_Summary.objects.all()
    serializer_class = ScanWatch_SummarySerializer
    filterset_class = ScanWatch_SummaryFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"scanwatches_summary": serializer.data})
    
class ScanWatchSummaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Scale.objects.all()
    serializer_class = ScanWatch_IntraActivitySerializer

class SleepmatIntraActivityListCreateView(generics.ListCreateAPIView):
    queryset = Sleepmat_IntraActivity.objects.all()
    serializer_class = SleepmatIntraActivitySerializer

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"sleepmats_intraactivity": serializer.data})

class SleepmatIntraActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sleepmat_IntraActivity.objects.all()
    serializer_class = SleepmatIntraActivitySerializer

class SleepmatSummaryListCreateView(generics.ListCreateAPIView):
    queryset = Sleepmat_Summary.objects.all()
    serializer_class = SleepmatSummarySerializer

    def perform_create(self, serializer):
        # Generate a new UUID before saving the instance
        serializer.save(id=uuid.uuid4())

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"sleepmats_summary": serializer.data})

class SleepmatSummaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sleepmat_Summary.objects.all()
    serializer_class = SleepmatSummarySerializer