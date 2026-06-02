import requests
from django.conf import settings
from datetime import datetime, timedelta

dias_semana = {
    'LUNES': 0,
    'MARTES': 1,
    'MIERCOLES': 2,
    'JUEVES': 3,
    'VIERNES': 4,
    'SABADO': 5,
    'DOMINGO': 6  
}

def obtener_fecha_proxima(dia_buscado):
    hoy = datetime.now().date()

    objetivo = dias_semana[dia_buscado]

    dias_restantes = (objetivo - hoy.weekday()) % 7

    return hoy + timedelta(days=dias_restantes)


def calcular_llegada(viaje, parada, dia, demora):
    fecha_viaje = obtener_fecha_proxima(dia)

    salida = datetime.combine(fecha_viaje, viaje.horario_embarcacion)

    llegada = salida + parada.tiempo_desde_salida + demora

    return llegada


def obtener_pronostico(lat,lon, llegada_estimada):
    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        'lat': lat,
        'lon': lon,
        'appid': settings.OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'es'
    }

    try:
        response = requests.get(url, params = params, timeout=5)

        if response.status_code != 200:
            return None
        
        data = response.json()

        forecasts = data['list']

        forecast_cercano = min(
            forecasts,
            key= lambda f: abs(
                datetime.strptime(
                    f['dt_txt'],
                    "%Y-%m-%d %H:%M:%S"
                ) - llegada_estimada
            )
        )

        return {
            "temperatura" : f"{forecast_cercano['main']['temp']} °C",
            "descripcion" : forecast_cercano['weather'][0]['description']
        } 
    
    except requests.exceptions.RequestException:
        return {"error" : "Servidor climñatico no disponible"}