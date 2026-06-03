from datetime import datetime, timedelta
from apps.viajes.models import EstadoViajeDiario

def actualizar_estado_viaje_lazy(viaje, fecha_consulta):
    """
    Evaluación perezosa ("Lazy Update"): 
    Calcula y actualiza el estado de un viaje a 'EN_VIAJE' o 'FINALIZADO' según la 
    hora actual y la hora de embarcación estimada.
    Evita tener un trabajo en segundo plano para actualizar viajes, haciéndolo bajo demanda.
    """
    registro = viaje.estados_diarios.filter(fecha=fecha_consulta).first()
    
    # Si el viaje no tiene registro, o su estado actual permite una actualización (no está cancelado/finalizado)
    if not registro or registro.estado not in ['FINALIZADO', 'CANCELADO']:
        base_datetime = datetime.combine(fecha_consulta, viaje.horario_embarcacion)
        demora = registro.tiempo_demora if registro else timedelta(minutes=0)
        llegada = base_datetime + viaje.duracion + demora
        ahora = datetime.now()

        nuevo_estado = None
        # Si ya pasó la hora estimada de llegada + 1 hora de margen, se marca finalizado
        if ahora > llegada + timedelta(hours=1):
            nuevo_estado = 'FINALIZADO'
        # Si ya pasó la hora de embarcación (+ demora + 30 minutos de tolerancia), está en viaje
        elif ahora >= base_datetime + demora + timedelta(minutes=30) and (not registro or registro.estado == 'A_TIEMPO'):
            nuevo_estado = 'EN_VIAJE'

        if nuevo_estado:
            if not registro:
                registro = EstadoViajeDiario.objects.create(
                    viaje=viaje,
                    fecha=fecha_consulta,
                    estado=nuevo_estado,
                    tiempo_demora=demora
                )
            else:
                registro.estado = nuevo_estado
                registro.save()
                
    return registro
