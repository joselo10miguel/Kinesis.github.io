from django.db import models
from django.contrib.auth.models import User



class Doctor(models.Model):
    usuario = models.OneToOneField(User,on_delete= models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    correo = models.EmailField()
    celular = models.CharField(max_length=20)
    genero = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def crear_paciente(self, **kwargs):
        kwargs['doctor'] = self  # Asigna al doctor actual como el doctor del paciente
        return Paciente.objects.create(**kwargs)

class Paciente(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    usuario = models.OneToOneField(User,on_delete= models.CASCADE)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField()
    cedula = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    celular = models.CharField(max_length=20)
    genero = models.CharField(max_length=10)
    edad = models.PositiveIntegerField()
    tipo_lesion = models.CharField(max_length=100, default="Sin lesión")
    rutinas_asignadas = models.PositiveIntegerField(default=0)  # Número de rutinas asignadas
    recomendacion = models.CharField(max_length=300, default="Ninguna")
    tiempo_descanso_entre_rutinas = models.PositiveIntegerField(default=0)  # Tiempo de descanso en minutos entre rutinas
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    

class Rutina(models.Model):
    numero_rutina = models.PositiveIntegerField()
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='rutinas')
    repeticiones_asignadas = models.PositiveIntegerField()
    tiempo_descanso_repeticiones = models.PositiveIntegerField()  # Tiempo de descanso en segundos entre repeticiones
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(null=True, blank=True)

    @classmethod
    def crear_rutina(cls, paciente, repeticiones_asignadas, tiempo_descanso):
        return cls.objects.create(paciente=paciente, repeticiones_asignadas=repeticiones_asignadas, tiempo_descanso=tiempo_descanso)


class Repeticiones(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='repeticiones')
    is_completed = models.BooleanField(default=False)
    numero_repeticion = models.PositiveIntegerField()

    
class Fase(models.Model):
    repeticion = models.ForeignKey(Repeticiones, on_delete=models.CASCADE, related_name='Fases')
    nombre_fase = models.CharField(max_length=100)
    angulo_brazo = models.DecimalField(max_digits=5, decimal_places=2)
    angulo_codo = models.DecimalField(max_digits=5, decimal_places=2)
    angulo_muneca = models.DecimalField(max_digits=5, decimal_places=2)
    velocidad_brazo = models.DecimalField(max_digits=5, decimal_places=2)
    velocidad_codo = models.DecimalField(max_digits=5, decimal_places=2)
    velocidad_muneca = models.DecimalField(max_digits=5, decimal_places=2) 

