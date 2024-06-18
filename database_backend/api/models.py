from django.db import models
from django.utils import timezone
import uuid

# Create your models here.
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50)
    role = models.CharField(max_length=100)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    password_hash = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Update the `updated_at` field before saving the record
        self.updated_at = timezone.now()
        super(User, self).save(*args, **kwargs)

class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_hash = models.CharField(max_length=100)
    device_type = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update the `updated_at` field before saving the record
        self.updated_at = timezone.now()
        super(Device, self).save(*args, **kwargs)

class Scale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='scales')
    date = models.DateTimeField()
    weight = models.FloatField()
    muscle_mass = models.FloatField()
    bone_mass = models.FloatField()
    fat_mass = models.FloatField()

class ScanWatchIntraActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='scanwatch_intraactivity')
    heart_rate = models.FloatField()
    date_heart_rate = models.FloatField()
    steps = models.FloatField()
    date_steps = models.FloatField()
    calories = models.FloatField()
    date_calories = models.FloatField()

class ScanWatchSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='scanwatch_summary')
    date = models.DateField()
    average_heart_rate = models.FloatField()
    calories = models.FloatField()
    steps = models.FloatField()
    hr_max = models.FloatField(null=True, blank=True)
    hr_min = models.FloatField(null=True, blank=True)

class SleepmatIntraActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sleepmat_intraactivity')
    start_date = models.FloatField() 
    end_date = models.FloatField()
    sleep_state = models.IntegerField() 
    date_heart_rate = models.FloatField()
    heart_rate = models.FloatField()
    date_respiration_rate = models.FloatField()
    respiration_rate = models.FloatField()
    date_snoring = models.FloatField()
    snoring = models.FloatField()
    date_sdnn_1 = models.FloatField()
    sdnn_1 = models.FloatField()

class SleepmatSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sleepmat_summary')
    date = models.DateField()
    breathing_disturbances = models.IntegerField()
    deep_sleep_duration = models.FloatField()
    duration_to_sleep = models.FloatField()
    duration_to_wakeup = models.FloatField()
    average_heart_rate = models.FloatField()
    light_sleep_duration = models.FloatField()
    rem_sleep_duration = models.FloatField()
    average_rr = models.IntegerField()
    sleep_score = models.FloatField()
    wakeup_count = models.FloatField()
    wakeup_duration = models.FloatField()
    total_sleep_time = models.FloatField(null=True, blank=True)
    total_time_in_bed = models.FloatField(null=True, blank=True)
    awake_in_bed = models.FloatField(null=True, blank=True)
    apnea = models.FloatField(null=True, blank=True)
    out_of_bed_count = models.FloatField(null=True, blank=True)

class Report(models.Model):
    id =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    path = models.CharField(max_length=300)
    type = models.CharField(max_length=20, default='aggegated') # e.g., 'weekly', 'global'
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update the `updated_at` field before saving the record
        self.updated_at = timezone.now()
        super(Report, self).save(*args, **kwargs)

class Usage(models.Model):
    id =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usages')
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='report_usages')
    scanwatch_usage_level = models.CharField(max_length=10)
    scanwatch_battery = models.CharField(max_length=10)
    scanwatch_last_date = models.DateField()
    sleepmat_usage_level = models.CharField(max_length=10)
    sleepmat_battery = models.CharField(max_length=10)
    sleepmat_last_date = models.DateField()
    scale_usage_level = models.CharField(max_length=10)
    scale_battery = models.CharField(max_length=10)
    scale_last_date = models.DateField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update the `updated_at` field before saving the record
        self.updated_at = timezone.now()
        super(Usage, self).save(*args, **kwargs)
    