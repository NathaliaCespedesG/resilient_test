import django_filters
from .models import User, Device, Scale, ScanWatch_IntraActivity, ScanWatch_Summary

class UserFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name='id', lookup_expr='exact')
    username = django_filters.CharFilter(field_name='username', lookup_expr='exact') 
    created_at_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    updated_at_from = django_filters.DateFilter(field_name='updated_at', lookup_expr='gte')
    updated_at_to = django_filters.DateFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        model = User
        fields = []

class DeviceFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name='id', lookup_expr='exact')
    user_id = django_filters.UUIDFilter(field_name='user_id', lookup_expr='exact')
    device_hash = django_filters.CharFilter(field_name='device_hash', lookup_expr='exact')
    device_type = django_filters.CharFilter(field_name='device_type', lookup_expr='exact')
    mac_address = django_filters.CharFilter(field_name='mac_address', lookup_expr='exact')
    is_active = django_filters.BooleanFilter(field_name='is_active', lookup_expr='exact')
    username = django_filters.CharFilter(field_name='user__username', lookup_expr='exact')

    class Meta:
        model = Device
        fields = []

class ScaleFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name='id', lookup_expr='exact')
    device_id = django_filters.UUIDFilter(field_name='device_id', lookup_expr='exact')
    date = django_filters.DateFilter(field_name='date', lookup_expr='exact')
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    user_id = django_filters.UUIDFilter(field_name='device__user_id', lookup_expr='exact')
    username = django_filters.CharFilter(method='filter_by_username')

    def filter_by_username(self, queryset, name, value):
        return queryset.filter(device__user__username=value)

    class Meta:
        model = Scale
        fields = []

class ScanWatch_IntraActivityFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name='id', lookup_expr='exact')
    device_id = django_filters.UUIDFilter(field_name='device_id', lookup_expr='exact')
    heart_rate = django_filters.RangeFilter(field_name='heart_rate')
    date_heart_rate = django_filters.RangeFilter(field_name='date_heart_rate')
    steps = django_filters.RangeFilter(field_name='steps')
    date_steps = django_filters.RangeFilter(field_name='date_steps')
    calories = django_filters.RangeFilter(field_name='calories')
    date_calories = django_filters.RangeFilter(field_name='date_calories')
    user_id = django_filters.UUIDFilter(field_name='device__user_id', lookup_expr='exact')
    username = django_filters.CharFilter(method='filter_by_username')

    def filter_by_username(self, queryset, name, value):
        return queryset.filter(device__user__username=value)

    class Meta:
        model = ScanWatch_IntraActivity
        fields = []

class ScanWatch_SummaryFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name='id', lookup_expr='exact')
    device_id = django_filters.UUIDFilter(field_name='device_id', lookup_expr='exact')
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    average_heart_rate = django_filters.RangeFilter(field_name='average_heart_rate')
    calories = django_filters.RangeFilter(field_name='calories')
    steps = django_filters.RangeFilter(field_name='steps')
    user_id = django_filters.UUIDFilter(field_name='device__user_id', lookup_expr='exact')
    username = django_filters.CharFilter(method='filter_by_username')

    def filter_by_username(self, queryset, name, value):
        return queryset.filter(device__user__username=value)

    class Meta:
        model = ScanWatch_Summary
        fields = []