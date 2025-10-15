from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from datetime import datetime, time, date, timedelta
import random
from trainer.models import UserHealthMetrics

class Command(BaseCommand):
    help = 'Populate database with sample health metrics data from Oct 15-30, 2025'

    def handle(self, *args, **options):
        # Get or create user1
        try:
            user = User.objects.get(username='user1')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='user1',
                password='123',
                first_name='John',
                last_name='Doe',
                email='john.doe@example.com'
            )
            self.stdout.write(self.style.SUCCESS('Created user: user1'))

        # Clear existing data for this user in the date range
        start_date = date(2025, 10, 15)
        end_date = date(2025, 10, 30)
        
        UserHealthMetrics.objects.filter(
            user=user,
            recorded_date__range=[start_date, end_date]
        ).delete()

        # Sample data with realistic variations
        base_weight = 75.0  # Starting weight in kg
        base_thigh = 58.0   # Starting thigh length in cm
        base_hip = 95.0     # Starting hip length in cm
        
        # Create entries for each day
        current_date = start_date
        entries_created = 0
        
        while current_date <= end_date:
            # Calculate realistic weight progression (slight fluctuations with overall trend)
            days_passed = (current_date - start_date).days
            weight_trend = -0.1 * days_passed  # Losing 0.1kg per day on average
            weight_variation = random.uniform(-0.5, 0.5)  # Daily fluctuation
            weight = round(base_weight + weight_trend + weight_variation, 2)
            
            # Thigh measurements with slight variations
            thigh_variation = random.uniform(-0.5, 0.5)
            thigh_length = round(base_thigh + (weight_trend * 0.2) + thigh_variation, 2)
            
            # Hip measurements with slight variations
            hip_variation = random.uniform(-1.0, 1.0)
            hip_length = round(base_hip + (weight_trend * 0.3) + hip_variation, 2)
            
            # Generate realistic sleep and wake times
            sleep_times = [
                (21, 30), (22, 0), (22, 15), (22, 30), (22, 45),
                (23, 0), (23, 15), (23, 30)
            ]
            wake_times = [
                (6, 0), (6, 30), (7, 0), (7, 15), (7, 30),
                (8, 0), (8, 15)
            ]
            
            # Random sleep and wake times
            sleep_hour, sleep_minute = random.choice(sleep_times)
            wake_hour, wake_minute = random.choice(wake_times)
            
            # Create datetime objects
            sleep_datetime = timezone.make_aware(
                datetime.combine(current_date, time(sleep_hour, sleep_minute))
            )
            wake_datetime = timezone.make_aware(
                datetime.combine(current_date + timedelta(days=1), time(wake_hour, wake_minute))
            )
            
            # Create the health metrics entry
            health_metric = UserHealthMetrics(
                user=user,
                wakeup_datetime=wake_datetime,
                sleeping_datetime=sleep_datetime,
                weight=weight,
                thigh_length=thigh_length,
                hip_length=hip_length,
                recorded_date=current_date
            )
            health_metric.save()
            
            entries_created += 1
            self.stdout.write(
                f'Created entry for {current_date}: Weight={weight}kg, '
                f'Sleep={sleep_hour:02d}:{sleep_minute:02d}, '
                f'Wake={wake_hour:02d}:{wake_minute:02d}, '
                f'Sleep Duration={health_metric.sleeped_time_formatted}'
            )
            
            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {entries_created} health metric entries '
                f'from {start_date} to {end_date}'
            )
        )
        
        # Display summary statistics
        total_entries = UserHealthMetrics.objects.filter(user=user).count()
        avg_weight = UserHealthMetrics.objects.filter(user=user).aggregate(
            avg_weight=models.Avg('weight')
        )['avg_weight']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary for user1:'
                f'\n- Total entries: {total_entries}'
                f'\n- Average weight: {avg_weight:.2f}kg'
                f'\n- Date range: {start_date} to {end_date}'
            )
        )