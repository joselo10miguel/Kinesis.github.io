from django.contrib import admin
from .models import Doctor,Paciente, Rutina, Repeticiones,Fase

class PacienteAdmin(admin.ModelAdmin):
    readonly_fields = ("created", )
# Register your models here.
admin.site.register(Doctor)
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Rutina)
admin.site.register(Repeticiones)
admin.site.register(Fase)






