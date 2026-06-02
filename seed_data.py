import os
import django
import sys
from datetime import timedelta, date, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.viajes.models import Empresa, Terminal, Ubicacion, Viaje, Parada, EstadoViajeDiario

def seed_data():
    print("Iniciando seed de datos...")

    terminal, _ = Terminal.objects.get_or_create(nombre="Terminal Central Mza", defaults={"cantidad_plataformas": 30})
    
    empresa, _ = Empresa.objects.get_or_create(
        nombre="Cata Internacional",
        defaults={"ventanilla": 5, "terminal": terminal}
    )

    ubicaciones_data = [
        {"nombre_oficial": "Terminal Mendoza", "latitud": -32.890840, "longitud": -68.827170},
        {"nombre_oficial": "San Rafael", "latitud": -34.617550, "longitud": -68.330070},
        {"nombre_oficial": "General Alvear", "latitud": -34.978580, "longitud": -67.697470},
        {"nombre_oficial": "Malargüe", "latitud": -35.475210, "longitud": -69.585570},
    ]

    ubicaciones = []
    for ud in ubicaciones_data:
        ub, _ = Ubicacion.objects.get_or_create(nombre_oficial=ud["nombre_oficial"], defaults={"latitud": ud["latitud"], "longitud": ud["longitud"]})
        ubicaciones.append(ub)

    viajes_data = [
        {
            "horario": time(10, 0),
            "duracion": timedelta(hours=3),
            "dias": ["LUNES", "MIERCOLES", "VIERNES"],
            "plataformas": [1, 2],
            "demora_min": 0,
            "estado": "A_TIEMPO",
            "motivo": None
        },
        {
            "horario": time(14, 30),
            "duracion": timedelta(hours=4),
            "dias": ["MARTES", "JUEVES", "SABADO"],
            "plataformas": [3],
            "demora_min": 45,
            "estado": "DEMORADO",
            "motivo": "Corte de ruta nacional"
        },
        {
            "horario": time(18, 0),
            "duracion": timedelta(hours=5),
            "dias": ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"],
            "plataformas": [5, 6],
            "demora_min": 15,
            "estado": "DEMORADO",
            "motivo": "Problemas mecanicos menores"
        },
    ]

    hoy = date.today()

    for idx, vd in enumerate(viajes_data):
        viaje, created = Viaje.objects.get_or_create(
            empresa=empresa,
            horario_embarcacion=vd["horario"],
            defaults={
                "duracion": vd["duracion"],
                "dias_operativos": vd["dias"],
                "plataformas_asignadas": vd["plataformas"]
            }
        )

        if created:
            Parada.objects.create(viaje=viaje, ubicacion=ubicaciones[0], orden=1, tiempo_desde_salida=timedelta(hours=0), precio=0)
            Parada.objects.create(viaje=viaje, ubicacion=ubicaciones[1], orden=2, tiempo_desde_salida=timedelta(hours=2), precio=1500)
            Parada.objects.create(viaje=viaje, ubicacion=ubicaciones[2], orden=3, tiempo_desde_salida=timedelta(hours=3, minutes=30), precio=2500)

        if vd["demora_min"] > 0:
            EstadoViajeDiario.objects.update_or_create(
                viaje=viaje,
                fecha=hoy,
                defaults={
                    "estado": vd["estado"],
                    "tiempo_demora": timedelta(minutes=vd["demora_min"]),
                    "motivo_demora": vd["motivo"]
                }
            )

    print("Datos de ejemplo (Viajes y Demoras) creados exitosamente.")

if __name__ == "__main__":
    seed_data()
