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

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse
)

from django.contrib.auth import get_user_model
UsuarioBase = get_user_model()

# --- Vistas Básicas ---

@extend_schema_view(
    list=extend_schema(summary="Listar terminales"),
    retrieve=extend_schema(summary="Obtener terminal"),
    create=extend_schema(summary="Crear terminal"),
    update=extend_schema(summary="Actualizar terminal"),
    partial_update=extend_schema(summary="Actualizar parcialmente viaje"),
    destroy=extend_schema(summary="Eliminar terminal")
)

class TerminalViewSet(viewsets.ModelViewSet):
    queryset = Terminal.objects.all()
    serializer_class = TerminalSerializer
    permission_classes = [IsAdminUser]


@extend_schema_view(
    list=extend_schema(summary="Listar empresas"),
    retrieve=extend_schema(summary="Obtener empresa"),
    create=extend_schema(summary="Crear empresa"),
    update=extend_schema(summary="Actualizar empresa"),
    partial_update=extend_schema(summary="Actualizar parcialmente viaje"),
    destroy=extend_schema(summary="Eliminar empresa")
)

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend]
    filterset_class = EmpresaFilter


@extend_schema_view(
    list=extend_schema(summary="Listar paradas"),
    retrieve=extend_schema(summary="Obtener paradas"),
    create=extend_schema(summary="Crear paradas"),
    update=extend_schema(summary="Actualizar paradas"),
    partial_update=extend_schema(summary="Actualizar parcialmente viaje"),
    destroy=extend_schema(summary="Eliminar paradas")
)

class ParadaViewSet(viewsets.ModelViewSet):
    queryset = Parada.objects.all()
    serializer_class = ParadaSerializer
    permission_classes = [EsPersonalEmpresaOReadOnly]

# --- Vistas Complejas ---

@extend_schema_view(
    list=extend_schema(summary="Listar pasajero"),
    retrieve=extend_schema(summary="Obtener pasajero"),
    create=extend_schema(summary="Crear pasajero"),
    update=extend_schema(summary="Actualizar pasajero"),
    partial_update=extend_schema(summary="Actualizar parcialmente pasajero"),
    destroy=extend_schema(summary="Eliminar pasajero")
)

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
        dni = request.data.get('dni')
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
            dni=dni,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        pasajero = Pasajero.objects.create(usuario=nuevo_usuario, telefono=telefono)
        
        serializer = self.get_serializer(pasajero)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    


@extend_schema_view(
    list=extend_schema(summary="Listar empleado"),
    retrieve=extend_schema(summary="Obtener empleado"),
    create=extend_schema(summary="Crear empleado"),
    update=extend_schema(summary="Actualizar empleado"),
    partial_update=extend_schema(summary="Actualizar parcialmente empleado"),
    destroy=extend_schema(summary="Eliminar empleado")
)

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

    # Registro plano para el encargado
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')  
        dni = request.data.get('dni')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        rol = request.data.get('rol', 'VENTANILLA')

        # Exigimos también el DNI
        if not username or not password or not dni:
            return Response({"error": "DNI, username y password son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        # Validación extra para superusuarios (requieren mandar el ID de la empresa)
        if request.user.is_superuser:
            empresa_id = request.data.get('empresa')
            if not empresa_id:
                return Response({"error": "Como superusuario, debe especificar el ID de la 'empresa' a la que pertenecerá el empleado."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                empresa_asignada = Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                return Response({"error": "La empresa especificada no existe."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Si es encargado, lo asignamos a su misma empresa
            empresa_asignada = request.user.empleado.empresa

        UsuarioBase = get_user_model()

        # Chequeamos si el DNI o el Username ya existen
        if UsuarioBase.objects.filter(username=username).exists() or UsuarioBase.objects.filter(dni=dni).exists():
            return Response({"error": "Este DNI o username ya está registrado como usuario en el sistema."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Creamos el usuario base de Django pasándole el DNI
        nuevo_usuario = UsuarioBase.objects.create_user(
            username=username,
            dni=dni,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 3. Creamos el perfil de Empleado
        nuevo_empleado = Empleado.objects.create(
            usuario=nuevo_usuario,
            empresa=empresa_asignada,
            rol=rol
        )

        serializer = self.get_serializer(nuevo_empleado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    

@extend_schema_view(
    list=extend_schema(
        summary="Listar ubicaciones"
    ),
    retrieve=extend_schema(
        summary="Obtener ubicación"
    ),
    create=extend_schema(
        summary="Crear ubicación",
        description="Valida automáticamente la ubicación mediante OpenStreetMap Nominatim."
    ),
    update=extend_schema(
        summary="Actualizar ubicación"
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente ubicación"
    ),
    destroy=extend_schema(
        summary="Eliminar ubicación"
    )
)

class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    # Empleados o superusuarios pueden crear ubicaciones.
    # Pasajeros solo pueden leerlas para no alterar la información.
    permission_classes = [EsEmpleadoOSuperuserOReadOnly]


    def create(self, request, *args, **kwargs):
        # Integración con Nominatim para validar y corregir la ubicación ingresada por el usuario. Si el lugar no se encuentra, se devuelve un error.
        nombre_buscado = request.data.get('nombre_oficial')
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': nombre_buscado, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'API_Terminal_Omnibus_v1'}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=3)
            response.raise_for_status() # Aseguramos que la respuesta HTTP sea exitosa
            
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
                return Response({'error': 'La ubicación no pudo ser encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.HTTPError:
            return Response({'error': 'Error comunicándose con el servidor de mapas.'}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.RequestException:
            return Response({'error': 'Fallo la conexión con el servidor de mapas.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError:
            return Response({'error': 'Respuesta inválida del servidor de mapas.'}, status=status.HTTP_502_BAD_GATEWAY)


@extend_schema_view(
    list=extend_schema(
        summary="Listar viajes"
    ),
    retrieve=extend_schema(
        summary="Obtener viaje"
    ),
    create=extend_schema(
        summary="Crear viaje"
    ),
    update=extend_schema(
        summary="Actualizar viaje"
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente viaje"
    ),
    destroy=extend_schema(
        summary="Eliminar viaje"
    )
)

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


    @extend_schema(
        summary="Actualizar estado diario",
        description="""
        Permite registrar el estado de un viaje
        para una fecha determinada.

        Puede indicarse:
        - estado
        - demora_minutos
        - motivo
        - fecha
        """
    )
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
    
    @extend_schema(
    summary="Pantalla de terminal",
    description="""
    Muestra los últimos viajes que partieron
    y los próximos viajes programados para hoy.
    """,
    parameters=[
        OpenApiParameter(
            name="terminal_id",
            type=str,
            required=False,
            description="UUID de la terminal"
        )
    ]
    )
    @action(detail=False, methods=['get'])
    def pantalla_terminal(self, request):
        qs = self.get_queryset()

        terminal_id = request.query_params.get('terminal_id')
        if terminal_id:
            qs = qs.filter(empresa__terminal__id=terminal_id)
            
        # Solo mostrar los viajes que operan el día de HOY
        dias_validos = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
        hoy_dia = dias_validos[datetime.now().weekday()]
        qs = qs.filter(dias_operativos__contains=[hoy_dia])

        ahora = datetime.now().time()
        ya_partieron = qs.filter(horario_embarcacion__lt=ahora).order_by('-horario_embarcacion')[:2]
        proximos = qs.filter(horario_embarcacion__gte=ahora).order_by('horario_embarcacion')
        return Response({
            'recientemente_partidos': ViajeSerializer(ya_partieron, many=True, context={'request': request}).data,
            'proximos_arribos': ViajeSerializer(proximos, many=True, context={'request': request}).data
        })

    @extend_schema(
    summary="Buscar viajes",
    description="""
    Busca viajes por destino y día de la semana.

    También puede filtrarse por terminal.
    """,
    parameters=[
        OpenApiParameter(
            name="destino",
            type=str,
            required=True,
            description="Nombre del destino"
        ),
        OpenApiParameter(
            name="dia",
            type=str,
            required=True,
            description="LUNES, MARTES, MIERCOLES, etc."
        ),
        OpenApiParameter(
            name="terminal_id",
            type=str,
            required=False,
            description="UUID de la terminal"
        ),
    ],
    responses={
        200: OpenApiResponse(description="Viajes encontrados"),
        404: OpenApiResponse(description="No se encontraron viajes")
    }
    )
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

        if not viajes.exists():
            return Response(
                {"error": "No se encontraron viajes para el destino y día seleccionados."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        resultado = []

        # Respuesta detallada de cada viaje encontrado, con cálculo exacto de la hora estimada de llegada a la parada solicitada, 
        # considerando el horario de embarque, el tiempo desde la salida a esa parada y cualquier demora informada.
        for viaje in viajes:
            parada = viaje.paradas.filter(ubicacion__nombre_oficial__icontains=destino).first()
            
            fecha_viaje = obtener_fecha_proxima(dia)
            registro = viaje.estados_diarios.filter(fecha=fecha_viaje).first()
            
            demora = registro.tiempo_demora if registro else timezone.timedelta(minutes=0)

            # --- Lógica Lazy FINALIZADO / EN_VIAJE ---
            if not registro or registro.estado not in ['FINALIZADO', 'CANCELADO']:
                from datetime import datetime, timedelta
                base_datetime = datetime.combine(fecha_viaje, viaje.horario_embarcacion)
                llegada_final_viaje = base_datetime + viaje.duracion + demora
                ahora = datetime.now()
                
                nuevo_estado = None
                if ahora > llegada_final_viaje + timedelta(hours=1):
                    nuevo_estado = 'FINALIZADO'
                elif ahora >= base_datetime + demora and (not registro or registro.estado == 'A_TIEMPO'):
                    nuevo_estado = 'EN_VIAJE'

                if nuevo_estado:
                    if not registro:
                        registro = EstadoViajeDiario.objects.create(
                            viaje=viaje,
                            fecha=fecha_viaje,
                            estado=nuevo_estado,
                            tiempo_demora=demora
                        )
                    else:
                        registro.estado = nuevo_estado
                        registro.save()
            # ----------------------------------------
            
            estado = registro.estado if registro else 'A_TIEMPO'
            motivo_demora = registro.motivo_demora if registro else None
            demora = registro.tiempo_demora if registro else timezone.timedelta(minutes=0)

            llegada = calcular_llegada(viaje, parada, dia, demora)

            clima = obtener_pronostico(parada.ubicacion.latitud, parada.ubicacion.longitud, llegada)

            resultado.append({
                "empresa": viaje.empresa.nombre,
                "terminal_nombre": viaje.empresa.terminal.nombre if viaje.empresa.terminal else None,
                "terminal_id": str(viaje.empresa.terminal.id) if viaje.empresa.terminal else None,
                "destino_solicitado": parada.ubicacion.nombre_oficial,
                "hora_salida": viaje.horario_embarcacion.strftime("%H:%M"),
                "hora_arribo_estimada": llegada.time().strftime("%H:%M"),
                "precio": parada.precio,
                "clima_estimado" : clima,
                "estado": estado,
                "motivo_demora": motivo_demora,
                "demora_minutos": int(demora.total_seconds() / 60)
            })

        return Response(resultado)

@extend_schema_view(
    list=extend_schema(
        summary="Listar estados diarios"
    ),
    retrieve=extend_schema(
        summary="Obtener estado diario"
    ),
    create=extend_schema(
        summary="Crear estado diario"
    ),
    update=extend_schema(
        summary="Actualizar estado diario"
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente estado diario"
    ),
    destroy=extend_schema(
        summary="Eliminar estado diario"
    )
)

class EstadoViajeDiarioViewSet(viewsets.ModelViewSet):
    queryset = EstadoViajeDiario.objects.all()
    serializer_class = EstadoViajeDiarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['viaje', 'fecha', 'estado']
