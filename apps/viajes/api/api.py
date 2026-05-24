from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, date
import requests

from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion
from .serializers import (TerminalSerializer, EmpresaSerializer, EmpleadoSerializer, 
                          PasajeroSerializer, ViajeSerializer, ParadaSerializer, UbicacionSerializer)
from .permissions import EsPersonalEmpresaOReadOnly

# --- Vistas Básicas ---

class TerminalViewSet(viewsets.ModelViewSet):
    queryset = Terminal.objects.all()
    serializer_class = TerminalSerializer

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer

class PasajeroViewSet(viewsets.ModelViewSet):
    queryset = Pasajero.objects.all()
    serializer_class = PasajeroSerializer

class ParadaViewSet(viewsets.ModelViewSet):
    queryset = Parada.objects.all()
    serializer_class = ParadaSerializer

# --- Vistas Complejas ---

class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    
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
    def registrar_demora(self, request, pk=None):
        # Permite a ventanilla registrar una demora en minutos para un viaje específico, junto con un motivo opcional.
        viaje = self.get_object()
        minutos = request.data.get('demora_minutos')
        motivo = request.data.get('motivo')
        
        if minutos is None: return Response({'error': 'Debe ingresar minutos'}, status=400)

        viaje.demora = timezone.timedelta(minutes=int(minutos))
        viaje.motivo_demora = motivo
        viaje.estado = 'DEMORADO' if int(minutos) > 0 else 'A_TIEMPO'
        viaje.save()
        return Response({'status': 'Demora actualizada correctamente'})

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

    @action(detail=False, methods=['post', 'get'])
    def buscar_pasajeros(self, request):
        # Obtenemos los datos (soporta tanto GET params como POST body para ser flexibles)
        destino = request.data.get('destino') or request.query_params.get('destino')
        fecha = request.data.get('fecha') or request.query_params.get('fecha')
        
        if not destino or not fecha:
            return Response({"error": "Debe enviar destino y fecha (YYYY-MM-DD)"}, status=400)

        # Lógica para determinar el día de la semana a partir de la fecha ingresada
        fecha_obj = datetime.strptime(fecha,"%Y-%m-%d").date()
        dias = {0: 'LUNES', 1: 'MARTES', 2: 'MIERCOLES', 3: 'JUEVES', 4: 'VIERNES', 5: 'SABADO', 6: 'DOMINGO'}
        dia_semana = dias[fecha_obj.weekday()]

        # Filtramos por día operativo y destino solicitado, usando el campo ArrayField para los días operativos y buscando coincidencias en las paradas del viaje.
        viajes = Viaje.objects.filter(
            dias_operativos__contains=[dia_semana], # Usamos contains para ArrayField
            paradas__ubicacion__nombre_oficial__icontains=destino
        ).distinct()

        resultado = []

        # Respuesta detallada de cada viaje encontrado, con cálculo exacto de la hora estimada de llegada a la parada solicitada, 
        # considerando el horario de embarque, el tiempo desde la salida a esa parada y cualquier demora informada.
        for viaje in viajes:
            parada = viaje.paradas.filter(ubicacion__nombre_oficial__icontains=destino).first()
            salida = datetime.combine(fecha_obj, viaje.horario_embarcacion)
            
            # Cálculo matemático exacto de la llegada
            llegada = salida + parada.tiempo_desde_salida + viaje.demora

            resultado.append({
                "empresa": viaje.empresa.nombre,
                "destino_solicitado": parada.ubicacion.nombre_oficial,
                "hora_salida": viaje.horario_embarcacion.strftime("%H:%M"),
                "hora_arribo_estimada": llegada.time().strftime("%H:%M"),
                "precio": parada.precio,
                "estado": viaje.estado,
                "motivo_demora": viaje.motivo_demora if viaje.estado == 'DEMORADO' else None
            })

        return Response(resultado)