from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

# Create your models here.
class PersonalTrainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=200)
    experience_years = models.IntegerField()
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    bio = models.TextField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.specialization}"



class UserHealthMetrics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wakeup_datetime = models.DateTimeField()
    sleeping_datetime = models.DateTimeField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    thigh_length = models.DecimalField(max_digits=5, decimal_places=2, help_text="Thigh length in cm")
    hip_length = models.DecimalField(max_digits=5, decimal_places=2, help_text="Hip length in cm")
    image = models.ImageField(upload_to='health_metrics/', blank=True, null=True, help_text="Progress photo")
    recorded_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def sleeped_time(self):
        """
        Calculate the duration of sleep between sleeping_datetime and wakeup_datetime.
        Returns a timedelta object representing the sleep duration.
        Handles cases where wakeup time is the next day.
        """
        if not self.sleeping_datetime or not self.wakeup_datetime:
            return None
        
        # If wakeup time is before sleep time, assume wakeup is the next day
        if self.wakeup_datetime <= self.sleeping_datetime:
            # Add 24 hours to wakeup time to account for next day
            from datetime import timedelta
            next_day_wakeup = self.wakeup_datetime + timedelta(days=1)
            sleep_duration = next_day_wakeup - self.sleeping_datetime
        else:
            # Same day scenario (rare but possible for naps)
            sleep_duration = self.wakeup_datetime - self.sleeping_datetime
        
        return sleep_duration
    
    @property
    def sleeped_time_hours(self):
        """
        Return sleep duration in hours as a decimal.
        Example: 7.5 hours for 7 hours and 30 minutes.
        """
        duration = self.sleeped_time
        if duration is None:
            return None
        
        total_seconds = duration.total_seconds()
        hours = total_seconds / 3600
        return round(hours, 2)
    
    @property
    def sleeped_time_formatted(self):
        """
        Return sleep duration in a human-readable format.
        Example: "7h 30m" for 7 hours and 30 minutes.
        """
        duration = self.sleeped_time
        if duration is None:
            return "N/A"
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"

    def compress_image(self, image_field, quality=85, max_width=800, max_height=800):
        """
        Compress and resize image before saving.
        Args:
            image_field: The image field to compress
            quality: JPEG quality (1-100, default 85)
            max_width: Maximum width in pixels (default 800)
            max_height: Maximum height in pixels (default 800)
        """
        if not image_field:
            return None
            
        # Open the image
        img = Image.open(image_field)
        
        # Convert to RGB if necessary (for PNG with transparency, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Calculate new dimensions while maintaining aspect ratio
        original_width, original_height = img.size
        
        # Only resize if image is larger than max dimensions
        if original_width > max_width or original_height > max_height:
            # Calculate scaling factor
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_factor = min(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize with high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress the image
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Generate new filename with .jpg extension
        original_name = os.path.splitext(image_field.name)[0]
        compressed_name = f"{original_name}_compressed.jpg"
        
        # Return compressed image as ContentFile
        return ContentFile(output.read(), name=compressed_name)

    def save(self, *args, **kwargs):
        """Override save method to compress image before saving."""
        # Compress image if it exists and is being updated
        if self.image and hasattr(self.image, 'file'):
            # Check if this is a new image or if the image has changed
            if not self.pk or (self.pk and self._state.adding):
                # New record or new image
                compressed_image = self.compress_image(self.image)
                if compressed_image:
                    self.image.save(compressed_image.name, compressed_image, save=False)
            else:
                # Check if image has changed
                try:
                    old_instance = UserHealthMetrics.objects.get(pk=self.pk)
                    if old_instance.image != self.image:
                        compressed_image = self.compress_image(self.image)
                        if compressed_image:
                            self.image.save(compressed_image.name, compressed_image, save=False)
                except UserHealthMetrics.DoesNotExist:
                    pass
        
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'recorded_date']  # One record per user per day
        ordering = ['-recorded_date']

    def __str__(self):
        return f"{self.user.username} - {self.recorded_date} (Weight: {self.weight}kg)"
