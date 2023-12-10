from .models import Paciente, Doctor, Rutina, Repeticiones,Fase
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from datetime import datetime
from .forms import PacienteForm
from xhtml2pdf import pisa
from django.shortcuts import render
from django.template.loader import get_template
from django.http import HttpResponse
from django.db.models import Count
from django.contrib.auth.models import User
from django.core import serializers
from django.template.context_processors import static
import json
import pytz
import json
import cv2
import mediapipe as mp
import numpy as np
import time



@login_required(login_url='signin') 
def dashboard(request):
    usuario = request.user
    
    if hasattr(usuario, 'doctor'):
        doctor = Doctor.objects.get(usuario=usuario)
        ## Numero de pacientes en total
        pacientes = Paciente.objects.filter(doctor=doctor)
        num_Pacientes = pacientes.count()
        
        ## Numero de pacientes Femeninos
        pacientesFemeninos = pacientes.filter(genero='Femenino')
        num_Pacientes_F = pacientesFemeninos.count()
        
        ## Numero de pacientes Masculinos
        pacientesMasculinos = pacientes.filter(genero='Masculino')
        num_Pacientes_M = pacientesMasculinos.count()
        
        ## Numero de pacientes por mes
        pacientes_por_mes = pacientes.annotate(month=TruncMonth('created')).values('month').annotate(count=Count('id')).order_by('month')

        # Convierte los objetos datetime en cadenas de texto
        pacientes_por_mes = [
            {
                'month': item['month'].strftime('%Y-%m-%d'),
                'count': item['count'],
            }
            for item in pacientes_por_mes
        ]

        # Serializa los datos como JSON para pasarlos a la plantilla
        pacientes_por_mes_json = json.dumps(list(pacientes_por_mes), default=str)

        context = {
            'usuario': usuario,
            'num_Pacientes': num_Pacientes,
            'num_Pacientes_F': num_Pacientes_F,
            'num_Pacientes_M': num_Pacientes_M,
            'pacientes_por_mes': pacientes_por_mes_json
        }

        return render(request, 'index.html', context)

    elif hasattr(usuario, 'paciente'):

        paciente = Paciente.objects.get(usuario=usuario)

        rutinas_completas = Rutina.objects.filter(paciente=paciente, is_completed=True).count()

        rutinas_asignadas = paciente.rutinas_asignadas

        progreso = (rutinas_completas / rutinas_asignadas) * 100

        rutinas = Rutina.objects.filter(paciente=paciente).exclude(fecha_inicio__isnull=True)

        rutinas_json = serializers.serialize("json", rutinas)
        
        context = {
            'usuario': usuario,
            'paciente': paciente,
            'progreso':progreso,
            'rutinas_completas':rutinas_completas,
            'rutinas':rutinas_json
        }
        
        return render(request,[ 'index_Paciente.html', 'progress_paciente.html',], context)


@login_required  
def paciente_rutina(request): 
    paciente = Paciente.objects.get(usuario=request.user)
    
    rutinas = Rutina.objects.filter(paciente=paciente)

    ec_timezone = pytz.timezone('America/Guayaquil')

    fecha_actual = datetime.now(ec_timezone).date()

    context = {
        'fecha_actual': fecha_actual,
        'rutinas': rutinas,
        'paciente':paciente,
    }

    return render(request, 'paciente_rutina.html', context)



@login_required  
def pacientes(request): 
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes.html', {'pacientes': pacientes})

@login_required  
def create_paciente(request):
    error_message = ''

    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            try:
                
                doctor = Doctor.objects.get(usuario=request.user)
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                rutinas_asignadas = form.cleaned_data['rutinas_asignadas']
                data_fechas = request.POST.get('fechas')

                existing_user = User.objects.filter(username=username).first()
                if existing_user:
                    error_message = 'El nombre de usuario ya pertenece a otra persona.'
                else:

                # Crea un nuevo usuario para el paciente
                    user = User.objects.create_user(
                        username=username,
                        password=password
                    )

                        
                    # Obtén el ID del usuario recién creado
                    usuario_id = user.id

                    new_paciente = form.save(commit=False)
                    new_paciente.doctor = doctor
                    new_paciente.usuario_id = usuario_id  # Asigna el ID del usuario al paciente
                    new_paciente.save()

                    fechas = data_fechas.split(",")  
                    
                    #Crear Rutinas
                    repeticiones_por_rutina = request.POST.get('repeticiones_por_rutina')
                    descanso_entre_repeticiones = request.POST.get('tiempo_repeticiones')

                    for i in range(rutinas_asignadas):
                        fecha_parts = fechas[i].split("/")
                        mes, dia, anio = map(int, fecha_parts)
                        fecha_inicio = datetime(anio, mes, dia, 10, 0, 0, tzinfo=pytz.UTC)
                        Rutina.objects.create(
                            numero_rutina=i,
                            paciente=new_paciente,
                            repeticiones_asignadas=repeticiones_por_rutina,
                            tiempo_descanso_repeticiones=descanso_entre_repeticiones,
                            fecha_inicio=fecha_inicio
                        )
                
                    if user.id:
                        return redirect('pacientes')
                    else:
                        error_message = 'Hubo un problema al crear las credenciales de usuario.'
            except Doctor.DoesNotExist:
                error_message = 'El doctor no existe.'
            except ValueError:
                error_message = 'Hubo un problema al crear el paciente.'
        else:
            return render(request, 'create_task.html', {
                'form': PacienteForm(),
                'error': 'Ingrese datos válidos'
            })
    else:
        form = PacienteForm()

    # Renderiza la página de creación de pacientes con el formulario y el mensaje de error
    return render(request, 'create_task.html', {
        'form': form,
        'error': error_message
    })

@login_required  
def paciente_detail(request, paciente_id):

    paciente = get_object_or_404(Paciente, pk=paciente_id)  

    rutinas_totales_completas = Rutina.objects.filter(paciente=paciente, is_completed=True).count()

    rutinas_completas = 0

    rutina =  Rutina.objects.filter(paciente=paciente).first()
    
    rutinas_asignadas = paciente.rutinas_asignadas

    progreso = (rutinas_totales_completas / rutinas_asignadas) * 100

    data_por_dia = {}

    for rutina in paciente.rutinas.all():
        dia = rutina.fecha_inicio.date()
        if dia not in data_por_dia:
            data_por_dia[dia] = {'rutinas': [], 'progreso': 0.0}
        
        data_por_dia[dia]['rutinas'].append(rutina)

    for dia, dia_data in data_por_dia.items():
        rutinas = dia_data['rutinas']
        rutinas_completas = sum(1 for rutina in rutinas if rutina.is_completed)
        rutinas_totales = len(rutinas)
        dia_data['progreso'] = (rutinas_completas / rutinas_totales) * 100 if rutinas_totales > 0 else 0
    
    context = {
        'paciente': paciente,
        'progreso': progreso,
        'rutina': rutina,
        'data_por_dia': data_por_dia.items()     
    }

    return render(request, 'datos_paciente.html',context)


@login_required
def paciente_update(request, paciente_id):
    error_message = ''
    paciente = Paciente.objects.get(id=paciente_id)
    user = User.objects.get(id=paciente.usuario_id)
    rutinas = paciente.rutinas.all()
    form = PacienteForm(request.POST, instance=paciente)
    if request.method == 'POST':
       
        try:

            nuevos_nombres = request.POST.get('nombres')
            nuevos_apellidos = request.POST.get('apellidos')
            nuevo_correo = request.POST.get('correo')
            nueva_cedula = request.POST.get('cedula')
            nueva_direccion = request.POST.get('direccion')
            nuevo_celular = request.POST.get('celular')
            nuevo_genero = request.POST.get('genero')
            nueva_edad = request.POST.get('edad')
            nuevo_tipo_lesion = request.POST.get('tipo_lesion')
            nuevo_tiempo = request.POST.get('tiempo_descanso_entre_rutinas')

            if nuevos_nombres:
                paciente.nombres = nuevos_nombres
            if nuevos_apellidos:
                paciente.apellidos = nuevos_apellidos
            if nuevo_correo:
                paciente.correo = nuevo_correo
            if nueva_cedula:
                paciente.cedula = nueva_cedula
            if nueva_direccion:
                paciente.direccion = nueva_direccion
            if nuevo_celular:
                paciente.celular = nuevo_celular
            if nuevo_genero:
                paciente.genero = nuevo_genero
            if nueva_edad:
                paciente.edad = nueva_edad
            if nuevo_tipo_lesion:
                paciente.tipo_lesion = nuevo_tipo_lesion
            if nuevo_tiempo:
                paciente.tiempo_descanso_entre_rutinas = nuevo_tiempo

            paciente.save()

            new_username = request.POST.get('username')
            new_password = request.POST.get('password')

            existing_user = User.objects.filter(username=new_username).exclude(id=user.id).first()
            if existing_user:
                error_message = 'El nombre de usuario ya pertenece a otra persona.'
            else:
                if new_username:
                    user.username = new_username
                    user.save()

                if new_password:
                    user.set_password(new_password)
                    user.save()

                return redirect('pacientes')
        except Exception as e:
            print("Error al actualizar el paciente:", str(e))
            error_message = 'Hubo un problema al actualizar el paciente.'
    
    return render(request, 'actualizar_Paciente.html', {
        'paciente': paciente,
        'rutinas': rutinas,
        'username': user.username,
        'error': error_message,
        'form':form,
    })


@login_required    
def delete_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)  # Obtiene el paciente por su ID
    if request.method == 'POST':
        # Verificar que se haya enviado una solicitud POST 
        user = User.objects.get(id=paciente.usuario_id)  # Obtiene el usuario asociado al paciente
        user.delete()  # Elimina el usuario
        paciente.delete()  # Elimina el paciente
        return redirect('pacientes')  # Redirige a la página de pacientes o a donde desees después de eliminar
 


@login_required
def rutina(request, numero_rutina):

    if request.method == 'POST':

        def calculate_angle(a, b, c):
            a = np.array(a)
            b = np.array(b)
            c = np.array(c)
        
            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians * 180.0 / np.pi)
        
            if angle > 180.0:
                angle = 360 - angle
            return angle

    # Función para calcular la velocidad
        def calculate_velocity(curr_pos, prev_pos, elapsed_time):
            # Cálculo de la distancia entre las posiciones actual y anterior
            distance = np.linalg.norm(np.array(curr_pos) - np.array(prev_pos))
        # Cálculo de la velocidad como distancia dividida por tiempo
            velocity = distance / elapsed_time
            return velocity


        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


        cap = cv2.VideoCapture(0)
        counter = 0
        stage = None
        stage2 = None
        prev_hombro = None
        prev_time = None
        velocity = 0
        pantalla_ancho = 950
        pantalla_alto = 750
        fase_1_completada = False
        repeticiones_completadas = 0
        mensaje = None
        paciente = Paciente.objects.get(usuario=request.user)
        rutina = Rutina.objects.get(paciente=paciente, numero_rutina=numero_rutina)
        repeticiones = rutina.repeticiones_asignadas

        repeticion = Repeticiones.objects.create(rutina=rutina, numero_repeticion=0)

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                results = pose.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    lado = paciente.tipo_lesion
                    landmarks = results.pose_landmarks.landmark
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    hombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    codo = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]

                    muneca = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    indice = [landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].x if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].y if lado == 'Luxación del hombro izquierdo' else landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].y]

                    dedo_medio_mcp_punto_medio = [(indice[0] + muneca[0]) / 2, (indice[1] + muneca[1]) / 2]

                    angle_hombro = calculate_angle(hip, hombro, codo)
                    angle_codo = calculate_angle(hombro, codo, muneca)
                    angle_muneca = calculate_angle(codo, muneca, dedo_medio_mcp_punto_medio)


                    cv2.putText(image, "{:.2f}".format(angle_hombro),
                                tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.putText(image, "{:.2f}".format(angle_codo),
                                tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.putText(image, "{:.2f}".format(angle_muneca),
                                tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    if prev_hombro is not None:
                        curr_time = time.time()
                        elapsed_time = curr_time - prev_time
                        velocity = calculate_velocity(hombro, prev_hombro, elapsed_time)
                        prev_hombro = hombro
                        prev_time = curr_time
                    else:
                        prev_hombro = hombro
                        prev_time = time.time()

                    if stage is None:
                        if 5 <= angle_hombro <= 15 and 165 <= angle_codo <= 180:

                            stage = "Inicial"
                            mensaje = "Levante el brazo"
                            fase_realizada = Fase.objects.create(
                                repeticion=repeticion,
                                nombre_fase='Inicial',
                                angulo_brazo=angle_hombro,
                                angulo_codo=angle_codo,
                                angulo_muneca=angle_muneca,
                                velocidad_brazo=velocity,
                                velocidad_codo=0.0,
                                velocidad_muneca=0.0
                            )
                            fase_realizada.save()
                            print("Fase Inicial Realizada y Guardada con Exito")
                            stage2 = None      

                            
                    if stage == "Inicial":
                        if 75 <= angle_hombro <= 90 and 75 <= angle_codo <= 90:
                            stage = "Fase 1"
                            mensaje = " Levante un poco mas"
                            fase_1_completada = False
                            stage2 = None
                            fase_realizada = Fase.objects.create(
                                repeticion=repeticion,
                                nombre_fase='Fase 1',
                                angulo_brazo=angle_hombro,
                                angulo_codo=angle_codo,
                                angulo_muneca=angle_muneca,
                                velocidad_brazo=velocity,
                                velocidad_codo=0.0,
                                velocidad_muneca=0.0
                            )
                            fase_realizada.save()
                            print("Fase Inicial Realizada y Guardada con Exito")
                            

                    if stage == "Fase 1" and not fase_1_completada:
                        if 165 <= angle_hombro <= 180 and 165 <= angle_codo <= 180:
                            fase_1_completada = True
                            stage = "Fase 2"
                            stage2 = "Fase 2"
                            mensaje = "Baje el brazo"

                    if stage == "Fase 2":
                        if angle_hombro > 90:
                            stage = None
                            if repeticiones_completadas < repeticiones:
                                repeticiones_completadas += 1
                                counter += 1
                                fase_realizada = Fase.objects.create(
                                    repeticion=repeticion,
                                    nombre_fase='Fase 2',
                                    angulo_brazo=angle_hombro,
                                    angulo_codo=angle_codo,
                                    angulo_muneca=angle_muneca,
                                    velocidad_brazo=velocity,
                                    velocidad_codo=0.0,
                                    velocidad_muneca=0.0
                                )
                                fase_realizada.save()
                                print("Fase Inicial Realizada y Guardada con Exito")

                            if counter == repeticiones:
                                fase_1_completada = False
                                rutina.is_completed = True
                                rutina.fecha_fin = datetime.now(tz=pytz.UTC)
                                rutina.save()
                                cv2.rectangle(image, (200, 160), (400, 220), (0, 0, 0), -1)
                                cv2.putText(image, " Bien hecho!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
                                cv2.imshow('Mediapipe Feed', image)
                                cv2.waitKey(3000)
                                break
                            else:
                                repeticion = Repeticiones.objects.create(rutina=rutina, numero_repeticion=repeticiones_completadas)

                    shoulder_pt = tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int))
                    elbow_pt = tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int))
                    wrist_pt = tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int))
                    hip_pt = tuple(np.multiply(hip, [image.shape[1], image.shape[0]]).astype(int))
                    thumb_pt = tuple(np.multiply(dedo_medio_mcp_punto_medio, [image.shape[1], image.shape[0]]).astype(int))

                    A_hombro = image.copy()
                    cv2.fillPoly(A_hombro, [np.array([shoulder_pt, elbow_pt, hip_pt])], (0, 255, 0))
                    opacity = 0.3
                    cv2.addWeighted(A_hombro, opacity, image, 1 - opacity, 0, image)

                    A_codo = image.copy()
                    cv2.fillPoly(A_codo, [np.array([shoulder_pt, elbow_pt, wrist_pt])], (255, 0, 255))
                    opacity = 0.3
                    cv2.addWeighted(A_codo, opacity, image, 1 - opacity, 0, image)

                    A_muneca = image.copy()
                    cv2.fillPoly(A_muneca, [np.array([elbow_pt, wrist_pt, thumb_pt])], (255, 255, 0))
                    opacity = 0.3
                    cv2.addWeighted(A_muneca, opacity, image, 1 - opacity, 0, image)

                    cv2.circle(image, shoulder_pt, 5, (255, 0, 255), -1)
                    cv2.circle(image, elbow_pt, 5, (0, 255, 0), -1)
                    cv2.circle(image, hip_pt, 5, (255, 0, 0), -1)
                    cv2.circle(image, wrist_pt, 5, (255, 0, 255), -1)
                    cv2.circle(image, thumb_pt, 5, (0, 0, 255), -1)
                    
                    cv2.putText(image, '', tuple(np.subtract(hip_pt, (0, 10)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.subtract(shoulder_pt, (0, 16)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(elbow_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(wrist_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(thumb_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.line(image, tuple(np.multiply(hip, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(dedo_medio_mcp_punto_medio, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)
                except Exception as e:
                    print("Error al crear y guardar el objeto Repeticiones:", str(e))
                pass

                cv2.rectangle(image, (0, 0), (200, 80), (225, 225, 0), -1)
                cv2.putText(image, ' Numero de Repeticiones', (10, 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, str(counter),
                            (80, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                cv2.rectangle(image, (700, 0), (200, 80), (255, 255, 255), -1)
                cv2.putText(image, 'Posicion:', (250, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, stage,
                            (250, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (102, 0, 102), 1, cv2.LINE_AA)
                cv2.putText(image, stage2,
                            (250, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (102, 0, 102), 1, cv2.LINE_AA)

                cv2.rectangle(image, (700, 0), (400, 80), (204, 255, 153), -1)
                cv2.putText(image, 'Por favor', (470, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, mensaje,
                            (420, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)

                resized_image = cv2.resize(image, (pantalla_ancho, pantalla_alto))
                cv2.imshow('Mediapipe Feed', resized_image)
                
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

        return redirect('paciente_rutina')
       
    return render(request, 'abduccion_brazo_Iz.html')




@login_required
def rutina_lesion_media(request, numero_rutina):

    if request.method == 'POST':
        # Función para calcular el ángulo entre tres puntos
        def calculate_angle(a, b, c):
            a = np.array(a)
            b = np.array(b)
            c = np.array(c)
            
            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians * 180.0 / np.pi)
            
            if angle > 180.0:
                angle = 360 - angle
            return angle

        # Función para calcular la velocidad
        def calculate_velocity(curr_pos, prev_pos, elapsed_time):
            # Cálculo de la distancia entre las posiciones actual y anterior
            distance = np.linalg.norm(np.array(curr_pos) - np.array(prev_pos))
            # Cálculo de la velocidad como distancia dividida por tiempo
            velocity = distance / elapsed_time
            return velocity

        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


        cap = cv2.VideoCapture(0)
        counter = 0
        stage = None
        stage2 = None
        prev_hombro = None
        prev_codo = None
        prev_muneca = None
        prev_time = None
        repeticiones = 5
        velocity = 0
        pantalla_ancho = 950
        pantalla_alto = 750
        fase_anterior = None
        contador_fases = 0
        fase_1_completada = False
        fase_2_completada = False
        repeticiones_completadas = 0
        mensaje = None

        paciente = Paciente.objects.get(usuario=request.user)
        rutina = Rutina.objects.get(paciente=paciente, numero_rutina=numero_rutina)
        repeticiones = rutina.repeticiones_asignadas

        repeticion = Repeticiones.objects.create(rutina=rutina, numero_repeticion=0)


        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                results = pose.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    lado = paciente.tipo_lesion
                    landmarks = results.pose_landmarks.landmark

                    hip_index = mp_pose.PoseLandmark.LEFT_HIP.value if lado == 'Lesión media en el hombro izquierdo' else mp_pose.PoseLandmark.RIGHT_HIP.value
                    hombro_index = mp_pose.PoseLandmark.LEFT_SHOULDER.value if lado == 'Lesión media en el hombro izquierdo' else mp_pose.PoseLandmark.RIGHT_SHOULDER.value
                    codo_index = mp_pose.PoseLandmark.LEFT_ELBOW.value if lado == 'Lesión media en el hombro izquierdo' else mp_pose.PoseLandmark.RIGHT_ELBOW.value
                    muneca_index = mp_pose.PoseLandmark.LEFT_WRIST.value if lado == 'Lesión media en el hombro izquierdo' else mp_pose.PoseLandmark.RIGHT_WRIST.value
                    indice_index = mp_pose.PoseLandmark.LEFT_INDEX.value if lado == 'Lesión media en el hombro izquierdo' else mp_pose.PoseLandmark.RIGHT_INDEX.value


                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    hombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    codo = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    muneca = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    indice = [landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].y]
                    
                    dedo_medio_mcp_punto_medio = [(indice[0] + muneca[0]) / 2, (indice[1] + muneca[1]) / 2]

                    angle_hombro = calculate_angle(hip, hombro, codo)
                    angle_codo = calculate_angle(hombro, codo, muneca)
                    angle_muneca = calculate_angle(codo, muneca, dedo_medio_mcp_punto_medio)

                    cv2.putText(image, "{:.2f}".format(angle_hombro),
                                tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.putText(image, "{:.2f}".format(angle_codo),
                                tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.putText(image, "{:.2f}".format(angle_muneca),
                                tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    if prev_hombro is not None:
                        curr_time = time.time()
                        elapsed_time = curr_time - prev_time
                        velocity = calculate_velocity(hombro, prev_hombro, elapsed_time)
                        prev_hombro = hombro
                        prev_time = curr_time
                    else:
                        prev_hombro = hombro
                        prev_time = time.time()

                    if stage is None:
                        if 5 <= angle_hombro <= 15 and 165 <= angle_codo <= 180:
                            stage = "Inicial"
                            mensaje = "Levante el brazo"
                            print("____________Estado Inicial________")
                            print("Angulo de Hombro Inicial: {:.2f}".format(angle_hombro), "°")
                            print("Angulo de Codo Inicial: {:.2f}".format(angle_codo), "°")
                            print("Angulo de muñeca Inicial: {:.2f}".format(angle_muneca), "°")
                            print("Velocidad Inicial: {:.2f} ".format(velocity), "m/s")
                            
                            fase_realizada = Fase.objects.create(
                                repeticion=repeticion,
                                nombre_fase='Inicial',
                                angulo_brazo=angle_hombro,
                                angulo_codo=angle_codo,
                                angulo_muneca=angle_muneca,
                                velocidad_brazo=velocity,
                                velocidad_codo=0.0,
                                velocidad_muneca=0.0
                            )
                            fase_realizada.save()
                            print("Fase Inicial Realizada y Guardada con Exito")
                            stage2 = None 

                    # Transition from "inicial" state to "Fase 1"
                    if stage == "Inicial":
                        if 75 <= angle_hombro <= 90 and 165 <= angle_codo <= 180:
                            stage = "Final"
                            mensaje = " Baje el brazo"
                            fase_1_completada = False
                            stage2 = None  # Here, we clear "Fase 2" when entering "Fase 1"
                            print("____________Estado Final________")
                            print("Angulo de Hombro Final: {:.2f}".format(angle_hombro), "°")
                            print("Angulo de Codo Final: {:.2f}".format(angle_codo), "°")
                            print("Angulo de muñeca Final: {:.2f}".format(angle_muneca), "°")
                            print("Velocidad Final: {:.2f} ".format(velocity), "m/s")
                              
                            fase_realizada = Fase.objects.create(
                                repeticion=repeticion,
                                nombre_fase='Final',
                                angulo_brazo=angle_hombro,
                                angulo_codo=angle_codo,
                                angulo_muneca=angle_muneca,
                                velocidad_brazo=velocity,
                                velocidad_codo=0.0,
                                velocidad_muneca=0.0
                            )
                            fase_realizada.save()
                            print("Fase Inicial Realizada y Guardada con Exito")
                
                    # Check if "Fase 2" is active to increase the counter
                    if stage == "Final" and not fase_1_completada:
                        if 75 <= angle_hombro <= 90 and 165 <= angle_codo <= 180:
                            fase_1_completada = True
                            stage = "Final"
                            stage2 = "Final"
                            
                    # Check if "Fase 2" is active to increase the counter
                    if stage == "Final":
                        if 75 <= angle_hombro <= 90 and 165 <= angle_codo <= 180:
                            stage = None
                            
                            if repeticiones_completadas < repeticiones:
                                repeticiones_completadas += 1
                                counter += 1
                                
                                print("_____________________")
                                print("REPETICION: ", counter)
                                print("____________________")
                                
                            
                            if counter == repeticiones:
                                fase_1_completada = False
                                rutina.is_completed = True
                                rutina.fecha_fin = datetime.now(tz=pytz.UTC)
                                rutina.save()
                                cv2.rectangle(image, (200, 160), (400, 220), (0, 0, 0), -1)
                                cv2.putText(image, " Bien hecho!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
                                cv2.imshow('Mediapipe Feed', image)
                                cv2.waitKey(3000)
                                break
                            else:
                                repeticion = Repeticiones.objects.create(rutina=rutina, numero_repeticion=repeticiones_completadas)     

                    shoulder_pt = tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int))
                    elbow_pt = tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int))
                    wrist_pt = tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int))
                    hip_pt = tuple(np.multiply(hip, [image.shape[1], image.shape[0]]).astype(int))
                    thumb_pt = tuple(np.multiply(dedo_medio_mcp_punto_medio, [image.shape[1], image.shape[0]]).astype(int))

                    A_hombro = image.copy()
                    cv2.fillPoly(A_hombro, [np.array([shoulder_pt, elbow_pt, hip_pt])], (0, 255, 0))
                    opacity = 0.3
                    cv2.addWeighted(A_hombro, opacity, image, 1 - opacity, 0, image)

                    A_codo = image.copy()
                    cv2.fillPoly(A_codo, [np.array([shoulder_pt, elbow_pt, wrist_pt])], (255, 0, 255))
                    opacity = 0.3
                    cv2.addWeighted(A_codo, opacity, image, 1 - opacity, 0, image)

                    A_muneca = image.copy()
                    cv2.fillPoly(A_muneca, [np.array([elbow_pt, wrist_pt, thumb_pt])], (255, 255, 0))
                    opacity = 0.3
                    cv2.addWeighted(A_muneca, opacity, image, 1 - opacity, 0, image)

                    cv2.circle(image, shoulder_pt, 5, (255, 0, 255), -1)
                    cv2.circle(image, elbow_pt, 5, (0, 255, 0), -1)
                    cv2.circle(image, hip_pt, 5, (255, 0, 0), -1)
                    cv2.circle(image, wrist_pt, 5, (255, 0, 255), -1)
                    cv2.circle(image, thumb_pt, 5, (0, 0, 255), -1)
                    
                    cv2.putText(image, '', tuple(np.subtract(hip_pt, (0, 10)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.subtract(shoulder_pt, (0, 16)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(elbow_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(wrist_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, '', tuple(np.add(thumb_pt, (0, 20)).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

                    cv2.line(image, tuple(np.multiply(hip, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(hombro, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(codo, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)

                    cv2.line(image, tuple(np.multiply(muneca, [image.shape[1], image.shape[0]]).astype(int)),
                            tuple(np.multiply(dedo_medio_mcp_punto_medio, [image.shape[1], image.shape[0]]).astype(int)), (0, 0, 0), 1)
                except:
                    pass

                cv2.rectangle(image, (0, 0), (200, 80), (225, 225, 0), -1)
                cv2.putText(image, ' Numero de Repeticiones', (10, 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, str(counter),
                            (80, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                cv2.rectangle(image, (700, 0), (200, 80), (255, 255, 255), -1)
                cv2.putText(image, 'Posicion:', (250, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, stage,
                            (250, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (102, 0, 102), 1, cv2.LINE_AA)
                cv2.putText(image, stage2,
                            (250, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (102, 0, 102), 1, cv2.LINE_AA)

                cv2.rectangle(image, (700, 0), (400, 80), (204, 255, 153), -1)
                cv2.putText(image, 'Por favor', (470, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, mensaje,
                            (420, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)

                resized_image = cv2.resize(image, (pantalla_ancho, pantalla_alto))
                cv2.imshow('Mediapipe Feed', resized_image)
                
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

        return redirect('paciente_rutina')
       
    return render(request, 'abduccion_brazo_Iz.html')


@login_required
def get_data_by_month(request):
    usuario = request.user

    doctor = Doctor.objects.get(usuario=usuario)

    fecha = request.GET.get('fecha')

    fecha_obj = datetime.strptime(fecha, '%m/%Y').date()

    ## numero de pacientes por mes 

    pacientes_masculinos = Paciente.objects.filter(doctor=doctor, genero='Masculino', created__month=fecha_obj.month, created__year=fecha_obj.year).count()
    
    pacientes_femeninos = Paciente.objects.filter(doctor=doctor, genero='Femenino', created__month=fecha_obj.month, created__year=fecha_obj.year).count()

    pacientes_por_mes = Paciente.objects.filter(doctor=doctor, created__month=fecha_obj.month, created__year=fecha_obj.year).values('created__year', 'created__month').annotate(cantidad=Count('id')).order_by('created__year', 'created__month').count()

    nombre_mes = fecha_obj.strftime('%B')


    data = {
        'pacientes_masculinos': pacientes_masculinos,
        'pacientes_femeninos': pacientes_femeninos,
        'pacientes_por_mes': pacientes_por_mes,
        'nombre_mes': nombre_mes
    }

    return JsonResponse(data)

@login_required
def get_data_by_day(request):

    usuario = request.user

    doctor = Doctor.objects.get(usuario=usuario)

    fecha = request.GET.get('fecha')

    fecha_obj = datetime.strptime(fecha, '%d/%m/%Y').date()

    ## numero de pacientes por dia
    pacientes_masculinos = Paciente.objects.filter(doctor=doctor, genero='Masculino', created__day=fecha_obj.day, created__month=fecha_obj.month, created__year=fecha_obj.year).count()
    
    pacientes_femeninos = Paciente.objects.filter(doctor=doctor, genero='Femenino', created__day=fecha_obj.day, created__month=fecha_obj.month, created__year=fecha_obj.year).count()

    pacientes_por_dia = Paciente.objects.filter(doctor=doctor, created__day=fecha_obj.day, created__month=fecha_obj.month, created__year=fecha_obj.year).count()

    nombre_dia = fecha_obj.strftime('%A')

    data = {
        'pacientes_masculinos': pacientes_masculinos,
        'pacientes_femeninos': pacientes_femeninos,
        'pacientes_por_dia': pacientes_por_dia,
        'nombre_dia': nombre_dia
    }

    return JsonResponse(data)


@login_required
def get_progress_paciente(request):
    paciente = Paciente.objects.get(usuario=request.user)

    rutinas_completas = Rutina.objects.filter(paciente=paciente, is_completed=True).count()

    rutinas_asignadas = paciente.rutinas_asignadas

    progreso = (rutinas_completas / rutinas_asignadas) * 100
    
    context = { 
        'progreso': progreso,
    }
    return render(request, 'progress_paciente.html',context)


@login_required
def pdf_generation(request,paciente_id):

    paciente = Paciente.objects.get(id=paciente_id)
   

    fecha_actual = datetime.now(tz=pytz.UTC).date()

    rutinas_totales_completas = Rutina.objects.filter(paciente=paciente, is_completed=True).count()

    rutinas_completas = 0

    rutina =  Rutina.objects.filter(paciente=paciente).first()
    
    rutinas_asignadas = paciente.rutinas_asignadas
    repeticiones_asignadas = Rutina.repeticiones_asignadas
    doctor = Paciente.doctor

    progreso = (rutinas_totales_completas / rutinas_asignadas) * 100

    data_por_dia = []

    for rutina in paciente.rutinas.all():
        dia = rutina.fecha_inicio.date()
        dia_data = {'fecha': dia, 'rutinas': [], 'progreso': 0.0}
        data_por_dia.append(dia_data)
        dia_data['rutinas'].append(rutina)

    for dia_data in data_por_dia:
        rutinas = dia_data['rutinas']
        rutinas_completas = sum(1 for rutina in rutinas if rutina.is_completed)
        rutinas_totales = len(rutinas)
        dia_data['progreso'] = (rutinas_completas / rutinas_totales) * 100 if rutinas_totales > 0 else 0


    context = {
        'doctor': doctor,
        'paciente': paciente,
        'fecha_actual': fecha_actual,
        'rutinas_completas': rutinas_totales_completas,
        'repeticiones': repeticiones_asignadas,
        'progreso': progreso,
        'rutina': rutina,
        'data_por_dia': data_por_dia,
        'imagen': 'img/logo.png'
    }
    


    html_template = get_template('reporte_paciente.html')
    html_content = html_template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paciente.apellidos}_{paciente.nombres}_reporte.pdf"'
    pisa.CreatePDF(html_content, dest=response)
    
    return response


@login_required
def add_rutina(request, paciente_id):
    paciente = Paciente.objects.get(id=paciente_id)
    rutinas = paciente.rutinas.all().count()
    rutina = Rutina.objects.filter(paciente=paciente).first()
    repeticiones_rutina = rutina.repeticiones_asignadas
    tiempo_descanso = rutina.tiempo_descanso_repeticiones


    try:
        fecha = request.POST.get('fecha_rutina')
        rutina = Rutina.objects.create(
            numero_rutina=rutinas + 1,
            paciente=paciente,
            repeticiones_asignadas= repeticiones_rutina,
            tiempo_descanso_repeticiones=tiempo_descanso,
            fecha_inicio=fecha)

        paciente.rutinas_asignadas += 1
        paciente.save()

        response_data = {'success': True}
        print('Rutina creada con exito')
        return JsonResponse(response_data)

    except Exception as e:
        print("Error al crear la rutina:", str(e))

    return JsonResponse({'success': False})

@login_required
def edit_rutina(request, rutina_id):
    paciente_id = request.POST.get('paciente_id')
    paciente = Paciente.objects.get(id=paciente_id)
    rutina = Rutina.objects.get( paciente = paciente, numero_rutina=rutina_id)

    try:
        fecha = request.POST.get('fecha_rutina')
        print('Fecha',fecha)
        rutina.fecha_inicio = datetime.strptime(fecha, '%Y-%m-%d')
        rutina.save()
        response_data = {'success': True}
        print('Rutina editada con exito')
        return JsonResponse(response_data)

    except Exception as e:
        print("Error al crear la rutina:", str(e))

    return JsonResponse({'success': False})
    



@login_required
def delete_rutina(request, rutina_id):
    paciente_id = request.POST.get('paciente_id')
    paciente = Paciente.objects.get(id=paciente_id)
    rutina = Rutina.objects.get( paciente = paciente, numero_rutina=rutina_id)
    rutina.delete()
    paciente.rutinas_asignadas -= 1
    paciente.save()
    print("Rutina eliminada con exito")
    response_data = {'success': True}
    return JsonResponse(response_data)