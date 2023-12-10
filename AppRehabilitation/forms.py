from django.forms import ModelForm
from .models import Doctor, Paciente, Rutina, Repeticiones,Fase
from django import forms


class DoctorForm(ModelForm):
    class Meta:
        model = Doctor
        fields = [ 'nombre', 'apellido', 'edad', 'correo', 'celular', 'genero']


class PacienteForm(ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True) 

    class Meta:
        model = Paciente
        fields = ['nombres', 'apellidos', 'correo', 'cedula', 'direccion', 'celular', 'genero', 'edad', 'tipo_lesion','rutinas_asignadas','tiempo_descanso_entre_rutinas', 'recomendacion', 'username', 'password']
   
class RutinaForm(ModelForm):
    class Meta:
        model = Rutina
        fields = '__all__' 

class RepeticionesForm(forms.ModelForm): 
    class Meta:
        model = Repeticiones
        fields = ['numero_repeticion']


class FaseForm(forms.ModelForm):
    class Meta:
        model = Fase
        fields = ['nombre_fase','angulo_brazo', 'angulo_codo', 'angulo_muneca', 'velocidad_brazo', 'velocidad_codo', 'velocidad_muneca']