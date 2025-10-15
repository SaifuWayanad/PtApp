from django.contrib import admin
from .models import PersonalTrainer, UserHealthMetrics

# Register your models here.
@admin.register(PersonalTrainer)
class PersonalTrainerAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'experience_years', 'hourly_rate', 'is_available']
    list_filter = ['specialization', 'is_available', 'experience_years']
    search_fields = ['user__first_name', 'user__last_name', 'specialization']



@admin.register(UserHealthMetrics)
class UserHealthMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'recorded_date', 'weight', 'thigh_length', 'hip_length', 'has_image', 'wakeup_datetime', 'sleeping_datetime']
    list_filter = ['recorded_date', 'user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'recorded_date'
    readonly_fields = ['created_at', 'updated_at']
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Image'
