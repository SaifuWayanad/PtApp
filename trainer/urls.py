from django.urls import path
from . import views

app_name = 'trainer'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('health-metrics/', views.health_metrics, name='health_metrics'),
    path('add-health-metrics/', views.add_health_metrics, name='add_health_metrics'),
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainer/<int:trainer_id>/', views.trainer_profile, name='trainer_profile'),
]