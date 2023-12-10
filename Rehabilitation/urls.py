"""
URL configuration for AppRehabilitation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from rest_framework.authtoken import views

from django.contrib.auth.views import LoginView,LogoutView
from AppRehabilitation.views import *
from AppRehabilitation.api import api
from rest_framework.routers import DefaultRouter
from AppRehabilitation.api.api import DoctorViewSet, PacienteViewSet, RutinaViewSet, RepeticionesViewSet,UserAPIView, FaseViewSet

 
router = DefaultRouter()
router.register(r'doctores', DoctorViewSet)
router.register(r'pacientes', PacienteViewSet)
router.register(r'rutinas', RutinaViewSet)
router.register(r'repeticiones', RepeticionesViewSet)
router.register(r'usuarios', UserAPIView)
router.register(r'fases', FaseViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', views.obtain_auth_token),
    path('',LoginView.as_view(template_name='signin.html' ), name='signin'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pacientes/', pacientes, name='pacientes'),
    path('pacientes/reporte/<int:paciente_id>', pdf_generation, name='generar_reporte'),
    path('pacientes/create/', create_paciente, name='create_paciente'),
    path('pacientes/<int:paciente_id>/', paciente_detail, name='paciente_detail'),
    path('update/<int:paciente_id>/', paciente_update, name='paciente_update'),
    path('delete/<int:paciente_id>/', delete_paciente, name='delete_paciente'),
    path('ejercicios/rutina/', paciente_rutina, name='paciente_rutina'),
    path('ejercicios/rutina/<int:numero_rutina>', rutina, name='rutina'),
    path('ejercicios/rutina/lesion/media/<int:numero_rutina>', rutina_lesion_media, name='rutina_lesion_media'),
    path('logout/',LogoutView.as_view(),name = 'logout'),
    path('paciente/progress/',get_progress_paciente, name='progress_paciente'),
    path('dashboard/get/pacientes/month/', get_data_by_month, name='get_pacientes_month'),
    path('dashboard/get/pacientes/day/', get_data_by_day, name='get_pacientes_day'),
    path('add/rutina/<int:paciente_id>/', add_rutina, name='add_rutina'),
    path('update/rutina/<int:rutina_id>/', edit_rutina, name='edit_rutina'),
    path('delete/rutina/<int:rutina_id>/', delete_rutina, name='delete_rutina'),
]
