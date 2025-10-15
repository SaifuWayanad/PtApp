from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PersonalTrainer, UserHealthMetrics
from .forms import HealthMetricsForm

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect('trainer:dashboard')
    return redirect('trainer:login')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('trainer:dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('trainer:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'trainer/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('trainer:login')

@login_required
def dashboard(request):
    context = {}
    
    # Check if user is admin (superuser or staff)
    is_admin = request.user.is_superuser or request.user.is_staff
    context['is_admin'] = is_admin
    
    # Determine which user's data to display
    if is_admin and request.GET.get('user_id'):
        try:
            selected_user_id = int(request.GET.get('user_id'))
            selected_user = User.objects.get(id=selected_user_id)
            viewing_user = selected_user
            context['selected_user'] = selected_user
        except (ValueError, User.DoesNotExist):
            viewing_user = request.user
            messages.error(request, 'Invalid user selected. Showing your own data.')
    else:
        viewing_user = request.user
    
    # Get user's health metrics for the graph (last 10 entries)
    health_metrics = UserHealthMetrics.objects.filter(user=viewing_user).order_by('-recorded_date')[:10]
    context['health_metrics'] = health_metrics
    context['viewing_user'] = viewing_user
    
    # Get last 5 images based on date (only entries with images)
    recent_images = UserHealthMetrics.objects.filter(
        user=viewing_user,
        image__isnull=False
    ).exclude(image='').order_by('-recorded_date')[:5]
    context['recent_images'] = recent_images
    
    # If admin, get all users for the dropdown
    if is_admin:
        all_users = User.objects.filter(is_active=True).order_by('username')
        context['all_users'] = all_users
    
    # Check if user is a personal trainer
    try:
        trainer_profile = PersonalTrainer.objects.get(user=request.user)
        context['is_trainer'] = True
        context['trainer_profile'] = trainer_profile
    except PersonalTrainer.DoesNotExist:
        context['is_trainer'] = False
    
    return render(request, 'trainer/dashboard.html', context)

@login_required
def health_metrics(request):
    metrics = UserHealthMetrics.objects.filter(user=request.user).order_by('-recorded_date')[:10]
    return render(request, 'trainer/health_metrics.html', {'health_metrics': metrics})

def trainer_list(request):
    trainers = PersonalTrainer.objects.filter(is_available=True)
    return render(request, 'trainer/trainer_list.html', {'trainers': trainers})

def trainer_profile(request, trainer_id):
    try:
        trainer = PersonalTrainer.objects.get(id=trainer_id)
        return render(request, 'trainer/trainer_profile.html', {'trainer': trainer})
    except PersonalTrainer.DoesNotExist:
        return HttpResponse("Trainer not found.", status=404)

@login_required
def add_health_metrics(request):
    if request.method == 'POST':
        form = HealthMetricsForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the form data
            health_metric = form.save(commit=False)
            health_metric.user = request.user
            selected_date = form.cleaned_data['date']
            
            # Use update_or_create to handle both new and existing entries
            defaults = {
                'wakeup_datetime': health_metric.wakeup_datetime,
                'sleeping_datetime': health_metric.sleeping_datetime,
                'weight': health_metric.weight,
                'thigh_length': health_metric.thigh_length,
                'hip_length': health_metric.hip_length,
                'image': health_metric.image,
            }
            
            obj, created = UserHealthMetrics.objects.update_or_create(
                user=request.user,
                recorded_date=selected_date,
                defaults=defaults
            )
            
            if created:
                messages.success(request, f'Health metrics for {selected_date} added successfully!')
            else:
                messages.success(request, f'Health metrics for {selected_date} updated successfully!')
                
            return redirect('trainer:dashboard')
    else:
        form = HealthMetricsForm()
    
    return render(request, 'trainer/add_health_metrics.html', {'form': form})
