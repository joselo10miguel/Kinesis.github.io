from rest_framework import serializers
from AppRehabilitation.models import *
from django.contrib.auth.models import User

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = 'username','password','email'

class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'

class RutinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rutina
        fields = '__all__'

class RepeticionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repeticiones
        fields = '__all__'

class FaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fase
        fields = '__all__'

