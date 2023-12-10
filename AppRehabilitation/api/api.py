from rest_framework import viewsets
from AppRehabilitation.models import *
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions
from .serializers import DoctorSerializer, PacienteSerializer, RutinaSerializer, RepeticionesSerializer, FaseSerializer,UserSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserAPIView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class RutinaViewSet(viewsets.ModelViewSet):
    queryset = Rutina.objects.all()
    serializer_class = RutinaSerializer
    permission_classes = [permissions.IsAuthenticated]

class RepeticionesViewSet(viewsets.ModelViewSet):
    queryset = Repeticiones.objects.all()
    serializer_class = RepeticionesSerializer
    permission_classes = [permissions.IsAuthenticated]

class FaseViewSet(viewsets.ModelViewSet):
    queryset = Fase.objects.all()
    serializer_class = FaseSerializer
    permission_classes = [permissions.IsAuthenticated]

