from django import forms
from django.utils import timezone
from datetime import datetime, time
from .models import UserHealthMetrics

class HealthMetricsForm(forms.ModelForm):
    # Date field with calendar widget
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control date-calendar',
            'required': True,
            'data-bs-toggle': 'datepicker'
        }),
        label='Date',
        initial=timezone.now().date(),
        required=True
    )
    
    # Sleep time hour dropdown (12-hour format)
    sleep_hour = forms.ChoiceField(
        choices=[(str(h), str(h)) for h in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Sleep Hour',
        initial='10',
        required=True
    )
    
    # Sleep time minute dropdown
    sleep_minute = forms.ChoiceField(
        choices=[(f'{m:02d}', f'{m:02d}') for m in range(0, 60, 5)],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Sleep Minute',
        initial='00',
        required=True
    )
    
    # Sleep time AM/PM dropdown
    sleep_ampm = forms.ChoiceField(
        choices=[('AM', 'AM'), ('PM', 'PM')],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Sleep AM/PM',
        initial='PM',
        required=True
    )
    
    # Wake up time hour dropdown (12-hour format)
    wakeup_hour = forms.ChoiceField(
        choices=[(str(h), str(h)) for h in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Wake Up Hour',
        initial='7',
        required=True
    )
    
    # Wake up time minute dropdown
    wakeup_minute = forms.ChoiceField(
        choices=[(f'{m:02d}', f'{m:02d}') for m in range(0, 60, 5)],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Wake Up Minute',
        initial='00',
        required=True
    )
    
    # Wake up time AM/PM dropdown
    wakeup_ampm = forms.ChoiceField(
        choices=[('AM', 'AM'), ('PM', 'PM')],
        widget=forms.Select(attrs={'class': 'form-control time-dropdown', 'required': True}),
        label='Wake Up AM/PM',
        initial='AM',
        required=True
    )

    class Meta:
        model = UserHealthMetrics
        fields = ['weight', 'thigh_length', 'hip_length', 'image']
        widgets = {
            'weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 70.5', 'required': True}
            ),
            'thigh_length': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 58.0', 'required': True}
            ),
            'hip_length': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 95.0', 'required': True}
            ),
            'image': forms.FileInput(
                attrs={
                    'class': 'form-control', 
                    'accept': 'image/*',
                    'data-max-size': '5242880',  # 5MB max size
                    'title': 'Select an image (will be automatically compressed)'
                }
            ),
        }
        labels = {
            'weight': 'Weight (kg)',
            'thigh_length': 'Thigh Length (cm)',
            'hip_length': 'Hip Length (cm)',
            'image': 'Progress Photo (Optional)',
        }
    
    def clean_image(self):
        """Validate uploaded image file."""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check file size (5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            if image.size > max_size:
                raise forms.ValidationError(
                    f'Image file too large. Maximum size is 5MB. '
                    f'Your file is {image.size / (1024*1024):.1f}MB.'
                )
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise forms.ValidationError(
                    'Invalid image format. Please upload JPEG, PNG, GIF, or WebP images only.'
                )
        
        return image
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Get the date
        date = self.cleaned_data['date']
        
        # Convert sleep time from 12-hour to 24-hour format
        sleep_hour_12 = int(self.cleaned_data['sleep_hour'])
        sleep_minute = int(self.cleaned_data['sleep_minute'])
        sleep_ampm = self.cleaned_data['sleep_ampm']
        
        if sleep_ampm == 'PM' and sleep_hour_12 != 12:
            sleep_hour_24 = sleep_hour_12 + 12
        elif sleep_ampm == 'AM' and sleep_hour_12 == 12:
            sleep_hour_24 = 0
        else:
            sleep_hour_24 = sleep_hour_12
            
        # Convert wakeup time from 12-hour to 24-hour format
        wakeup_hour_12 = int(self.cleaned_data['wakeup_hour'])
        wakeup_minute = int(self.cleaned_data['wakeup_minute'])
        wakeup_ampm = self.cleaned_data['wakeup_ampm']
        
        if wakeup_ampm == 'PM' and wakeup_hour_12 != 12:
            wakeup_hour_24 = wakeup_hour_12 + 12
        elif wakeup_ampm == 'AM' and wakeup_hour_12 == 12:
            wakeup_hour_24 = 0
        else:
            wakeup_hour_24 = wakeup_hour_12
        
        # Create time objects
        sleep_time = time(sleep_hour_24, sleep_minute)
        wakeup_time = time(wakeup_hour_24, wakeup_minute)
        
        # Create datetime objects
        instance.sleeping_datetime = timezone.make_aware(
            datetime.combine(date, sleep_time)
        )
        instance.wakeup_datetime = timezone.make_aware(
            datetime.combine(date, wakeup_time)
        )
        
        # Set the recorded_date to the selected date
        instance.recorded_date = date
        
        if commit:
            instance.save()
        return instance