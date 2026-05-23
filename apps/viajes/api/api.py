from rest_framework import viewsets, filters
from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion
from .serializers import TerminalSerializer, EmpresaSerializer, EmpleadoSerializer, PasajeroSerializer, ViajeSerializer, ParadaSerializer, UbicacionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime

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

class ViajeViewSet(viewsets.ModelViewSet):
    queryset = Viaje.objects.all()
    serializer_class = ViajeSerializer

    @action(detail=False, methods=['post', 'get'])
    def consultar(self, request):
        destino = request.data.get('destino')
        fecha = request.data.get('fecha')

        if not destino or not fecha:
            return Response({"error": "Debe enviar destino y fecha"}, status = 400)
        
        fecha_obj = datetime.strptime(fecha,"%Y-%m-%d").date()

        dias = {
            0: 'LUNES',
            1: 'MARTES',
            2: 'MIERCOLES',
            3: 'JUEVES',
            4: 'VIERNES',
            5: 'SABADO',
            6: 'DOMINGO'
        }

        dia_semana = dias[fecha_obj.weekday()]

        viajes = Viaje.objects.filter(
            dias_operativos__icontains=dia_semana,
            paradas__ubicacion__nombre_oficial__icontains = destino
        ).distinct()

        resultado = []

        for viaje in viajes:

            parada = viaje.paradas.filter(
                ubicacion__nombre_oficial__icontains=destino
            ).first()

            salida = datetime.combine(
                fecha_obj,
                viaje.horario_embarcacion
            )

            llegada = salida + parada.tiempo_desde_salida

            resultado.append({
                "empresa": viaje.empresa.nombre,
                "destino": parada.ubicacion.nombre_oficial,
                "hora_salida": viaje.horario_embarcacion,
                "hora_arribo": llegada.time(),
                "precio": parada.precio,
                "estado": viaje.estado
            })

        return Response(resultado)

class ParadaViewSet(viewsets.ModelViewSet):
    queryset = Parada.objects.all()
    serializer_class = ParadaSerializer

class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer