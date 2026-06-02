from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.utils import timezone
from datetime import datetime, date
import requests

from django_filters.rest_framework import DjangoFilterBackend
from .filters import ViajeFilter, EmpresaFilter

from apps.viajes.api.services.weather_service import obtener_pronostico, calcular_llegada, obtener_fecha_proxima

from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion, EstadoViajeDiario
from .serializers import (TerminalSerializer, EmpresaSerializer, EmpleadoSerializer, 
                          PasajeroSerializer, ViajeSerializer, ParadaSerializer, UbicacionSerializer, EstadoViajeDiarioSerializer)
from .permissions import EsPersonalEmpresaOReadOnly, EsEncargadoOSuperuser, EsEmpleadoOSuperuserOReadOnly, EsPasajeroOInvitado

from django.contrib.auth import get_user_model
UsuarioBase = get_user_model()

# --- Vistas Básicas ---

class TerminalViewSet(viewsets.ModelViewSet):
    queryset = Terminal.objects.all()
    serializer_class = TerminalSerializer
    permission_classes = [IsAdminUser]

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend]
    filterset_class = EmpresaFilter


class ParadaViewSet(viewsets.ModelViewSet):
    queryset = Parada.objects.all()
    serializer_class = ParadaSerializer
    permission_classes = [EsPersonalEmpresaOReadOnly]

# --- Vistas Complejas ---

class PasajeroViewSet(viewsets.ModelViewSet):
    serializer_class = PasajeroSerializer
    permission_classes = [EsPasajeroOInvitado]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Pasajero.objects.none()
        if user.is_superuser:
            return Pasajero.objects.all() 
        return Pasajero.objects.filter(usuario=user)

    def create(self, request, *args, **kwargs):
        # 1. Atrapamos el DNI también
        username = request.data.get('username')
        dni = request.data.get('dni')  # <--- ¡NUEVO! Atrapamos el DNI
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        telefono = request.data.get('telefono')

        # Exigimos el DNI en la validación
        if not username or not password or not telefono or not dni:
            return Response({"error": "username, dni, password y telefono son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        UsuarioBase = get_user_model()
        
        # Chequeamos si el Username O el DNI ya existen
        if UsuarioBase.objects.filter(username=username).exists() or UsuarioBase.objects.filter(dni=dni).exists():
            return Response({"error": "Este usuario o DNI ya está registrado."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Pasamos el DNI a la creación del usuario base
        nuevo_usuario = UsuarioBase.objects.create_user(
            username=username,
            dni=dni,       # <--- ¡NUEVO! Lo guardamos en la BD
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        pasajero = Pasajero.objects.create(usuario=nuevo_usuario, telefono=telefono)
        
        serializer = self.get_serializer(pasajero)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    



class EmpleadoViewSet(viewsets.ModelViewSet):
    serializer_class = EmpleadoSerializer
    permission_classes = [EsEncargadoOSuperuser]

    def get_queryset(self):
        # El Superadmin ve todo. El Encargado solo ve a la gente de su empresa.

        user = self.request.user
        if user.is_superuser:
            return Empleado.objects.all()
        if hasattr(user, 'empleado'):
            return Empleado.objects.filter(empresa=user.empleado.empresa)
        return Empleado.objects.none()

    # 🔥 CONFIGURAMOS EL REGISTRO PLANO PARA EL ENCARGADO
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')  
        dni = request.data.get('dni')  # <--- ¡Atrapamos el DNI!
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        rol = request.data.get('rol', 'VENTANILLA')

        # Exigimos también el DNI
        if not username or not password or not dni:
            return Response({"error": "DNI, username y password son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        UsuarioBase = get_user_model()

        # Chequeamos si el DNI o el Username ya existen
        if UsuarioBase.objects.filter(username=username).exists() or UsuarioBase.objects.filter(dni=dni).exists():
            return Response({"error": "Este DNI o username ya está registrado como usuario en el sistema."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Creamos el usuario base de Django pasándole el DNI
        nuevo_usuario = UsuarioBase.objects.create_user(
            username=username,
            dni=dni,             # <--- ¡Lo guardamos en la base de datos!
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 2. Tomamos la empresa del Encargado logueado
        empresa_encargado = request.user.empleado.empresa

        # 3. Creamos el perfil de Empleado
        nuevo_empleado = Empleado.objects.create(
            usuario=nuevo_usuario,
            empresa=empresa_encargado,
            rol=rol
        )

        serializer = self.get_serializer(nuevo_empleado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    


class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    # Los empleados pueden crear ubicaciones o los superusuarios, pero los pasajeros solo pueden leerlas. 
    # Esto es para asegurar que solo el personal autorizado pueda agregar o modificar ubicaciones, mientras que los pasajeros pueden consultar la información sin riesgo de alterarla.
    permission_classes = [EsEmpleadoOSuperuserOReadOnly]


    def create(self, request, *args, **kwargs):
        # Integración con Nominatim para validar y corregir la ubicación ingresada por el usuario. Si el lugar no se encuentra, se devuelve un error.
        nombre_buscado = request.data.get('nombre_oficial')
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': nombre_buscado, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'API_Terminal_Omnibus_v1'}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=3)
            resultados = response.json()
            if resultados:
                lugar = resultados[0]

                lat_redondeada = round(float(lugar['lat']), 6)
                lon_redondeada = round(float(lugar['lon']), 6)
                
                #Datos Sanitizados y corregidos para guardar en la base de datos, asegurando que la latitud y longitud tengan el formato correcto.
                data_corregida = {
                    'nombre_oficial': lugar['display_name'],
                    'latitud': lat_redondeada,
                    'longitud': lon_redondeada,
                }
                
                serializer = self.get_serializer(data=data_corregida)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'La ubicación no pudo ser encontrada.'}, status=400)
        except requests.exceptions.RequestException:
            return Response({'error': 'Fallo la conexión con el servidor de mapas.'}, status=503)




class ViajeViewSet(viewsets.ModelViewSet):
    queryset = Viaje.objects.all()
    serializer_class = ViajeSerializer
    permission_classes = [EsPersonalEmpresaOReadOnly]

    filter_backends = [DjangoFilterBackend]
    filterset_class = ViajeFilter

    def get_queryset(self):
        ''' 
        Filtrado de viajes según el rol del usuario: 
        - Superusuarios ven todo
        - Empleados ven solo su empresa
        - Otros usuarios no autenticados ven todo (o podrían no ver nada dependiendo de la lógica de permisos).
        '''
        user = self.request.user
        if user.is_superuser: return Viaje.objects.all()
        if hasattr(user, 'empleado'): return Viaje.objects.filter(empresa=user.empleado.empresa)
        return Viaje.objects.all()

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empleado.empresa)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def actualizar_estado_diario(self, request, pk=None):
        viaje = self.get_object()
        minutos = request.data.get('demora_minutos')
        motivo = request.data.get('motivo')
        estado = request.data.get('estado')
        
        fecha_str = request.data.get('fecha')
        if fecha_str:
            fecha_registro = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        else:
            fecha_registro = date.today()

        registro, created = EstadoViajeDiario.objects.get_or_create(viaje=viaje, fecha=fecha_registro)
        
        if minutos is not None:
            registro.tiempo_demora = timezone.timedelta(minutes=int(minutos))
        if motivo is not None:
            registro.motivo_demora = motivo
        if estado is not None:
            registro.estado = estado
        elif minutos is not None and int(minutos) > 0:
            registro.estado = 'DEMORADO'
        
        registro.save()

        return Response({'status': 'Estado diario actualizado correctamente', 'estado': registro.estado})

    @action(detail=False, methods=['get'])
    def pantalla_terminal(self, request):
        # Lógica para las pantallas de la terminal: Mostrar los últimos 2 viajes que partieron (ordenados por hora de embarque descendente) y 
        # los próximos viajes que están por partir (ordenados por hora de embarque ascendente).
        ahora = datetime.now().time()
        ya_partieron = self.get_queryset().filter(horario_embarcacion__lt=ahora).order_by('-horario_embarcacion')[:2]
        proximos = self.get_queryset().filter(horario_embarcacion__gte=ahora).order_by('horario_embarcacion')
        return Response({
            'recientemente_partidos': ViajeSerializer(ya_partieron, many=True).data,
            'proximos_arribos': ViajeSerializer(proximos, many=True).data
        })

    @action(detail=False, methods=['post', 'get'], permission_classes=[AllowAny])
    def buscar_viajes(self, request):
        # Obtenemos los datos (soporta tanto GET params como POST body para ser flexibles)
        destino = request.data.get('destino') or request.query_params.get('destino')
        dia = request.data.get('dia') or request.query_params.get('dia')
        terminal_id = request.data.get('terminal_id') or request.query_params.get('terminal_id')
        
        if not destino or not dia:
            return Response({"error": "Debe enviar destino y dia de semana"}, status=400)

        # Lógica para determinar el día de la semana a partir de la fecha ingresada
        dia = dia.upper()

        dias_validos = [
            'LUNES',
            'MARTES',
            'MIERCOLES',
            'JUEVES',
            'VIERNES',
            'SABADO',
            'DOMINGO'            
        ]

        if dia not in dias_validos:
            return Response({"error": "Dia invalido"}, status=400)

        # Filtramos por día operativo y destino solicitado, usando el campo ArrayField para los días operativos y buscando coincidencias en las paradas del viaje.
        filtros = {
            'dias_operativos__contains': [dia],
            'paradas__ubicacion__nombre_oficial__icontains': destino
        }
        
        if terminal_id:
            filtros['empresa__terminal__id'] = terminal_id

        viajes = Viaje.objects.filter(**filtros).distinct()

        resultado = []

        # Respuesta detallada de cada viaje encontrado, con cálculo exacto de la hora estimada de llegada a la parada solicitada, 
        # considerando el horario de embarque, el tiempo desde la salida a esa parada y cualquier demora informada.
        for viaje in viajes:
            parada = viaje.paradas.filter(ubicacion__nombre_oficial__icontains=destino).first()
            
            fecha_viaje = obtener_fecha_proxima(dia)
            registro = viaje.estados_diarios.filter(fecha=fecha_viaje).first()
            
            estado = registro.estado if registro else 'A_TIEMPO'
            motivo_demora = registro.motivo_demora if registro else None
            demora = registro.tiempo_demora if registro else timezone.timedelta(minutes=0)

            llegada = calcular_llegada(viaje, parada, dia, demora)

            clima = obtener_pronostico(parada.ubicacion.latitud, parada.ubicacion.longitud, llegada)

            resultado.append({
                "empresa": viaje.empresa.nombre,
                "destino_solicitado": parada.ubicacion.nombre_oficial,
                "hora_salida": viaje.horario_embarcacion.strftime("%H:%M"),
                "hora_arribo_estimada": llegada.time().strftime("%H:%M"),
                "precio": parada.precio,
                "clima_estimado" : clima,
                "estado": estado,
                "motivo_demora": motivo_demora
            })

        return Response(resultado)

class EstadoViajeDiarioViewSet(viewsets.ModelViewSet):
    queryset = EstadoViajeDiario.objects.all()
    serializer_class = EstadoViajeDiarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['viaje', 'fecha', 'estado']