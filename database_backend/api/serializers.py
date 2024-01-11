from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate_username(self, value):
        """
        Validate that the username is not already in use.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use. Please choose a different one.")
        return value
    
    def to_representation(self, instance):
        """
        Customize the representation of the serialized data.
        """
        # Only include specific fields in the response
        return {
            'id': instance.id,
            'username': instance.username,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at
        }

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

    def validate_device_hash(self, value):
        """
        Validate that the device_hash is not already in use.
        """
        if Device.objects.filter(device_hash=value).exists():
            raise serializers.ValidationError("This device_hash is already in use. Please choose a different one.")
        return value
    
    def validate_device_type(self, value):
        valid_device_types = ['scale', 'scan_watch', 'sleep_mat']

        if value in valid_device_types:
            return value
        raise serializers.ValidationError("{0} is not an accepted type: {1}".format(value, ", ".join(valid_device_types)))
    
class ScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scale
        fields = '__all__'

class ScanWatch_IntraActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanWatch_IntraActivity
        fields = '__all__'

class ScanWatch_SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanWatch_Summary
        fields = '__all__'

class SleepmatIntraActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sleepmat_IntraActivity
        fields = '__all__'

class SleepmatSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sleepmat_Summary
        fields = '__all__'