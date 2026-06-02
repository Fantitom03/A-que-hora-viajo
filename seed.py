import os
import django
import sys
from datetime import timedelta, date, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.viajes.models import Empresa, Terminal, Ubicacion, Viaje, Parada
from apps.usuarios.models import Usuario

def seed_data():
    print("Iniciando seed de datos...")

    # 1. Crear Terminales
    terminal_cata, _ = Terminal.objects.get_or_create(nombre="Terminal de Ómnibus de Catamarca", defaults={"cantidad_plataformas": 25})
    terminal_mza, _ = Terminal.objects.get_or_create(nombre="Terminal Central Mza", defaults={"cantidad_plataformas": 30})
    terminal_cba, _ = Terminal.objects.get_or_create(nombre="Terminal de Ómnibus de Córdoba", defaults={"cantidad_plataformas": 40})
    
    # 2. Crear Empresas
    empresa_flecha, _ = Empresa.objects.get_or_create(nombre="Flecha Bus", defaults={"ventanilla": 5, "terminal": terminal_cata})
    empresa_chevallier, _ = Empresa.objects.get_or_create(nombre="Chevallier", defaults={"ventanilla": 3, "terminal": terminal_cata})
    empresa_tesa, _ = Empresa.objects.get_or_create(nombre="TESA", defaults={"ventanilla": 2, "terminal": terminal_cata})
    empresa_cata, _ = Empresa.objects.get_or_create(nombre="Cata Internacional", defaults={"ventanilla": 5, "terminal": terminal_cba})

    # 3. Crear Ubicaciones (Paradas)
    ubicaciones_data = [
        {"nombre_oficial": "Belén, Municipio de Belén, Departamento Belén, Catamarca, K4750, Argentina", "latitud": -27.649596, "longitud": -67.026362},
        {"nombre_oficial": "Chumbicha, Municipio de Chumbicha, Departamento Capayán, Catamarca, K4726, Argentina", "latitud": -28.853208, "longitud": -66.237627},
        {"nombre_oficial": "Terminal de Ómnibus, Los Diaguitas, Santa Bárbara, Fiambala, Municipio de Fiambalá, Departamento Tinogasta, Catamarca, K5340, Argentina", "latitud": -27.694054, "longitud": -67.624960},
        {"nombre_oficial": "Terminal Catamarca, 856, Avenida Güemes, Centro, San Fernando del Valle de Catamarca, Municipio de San Fernando del Valle de Catamarca, Departamento Capital, Catamarca, K4700CLV, Argentina", "latitud": -28.475565, "longitud": -65.774472},
        {"nombre_oficial": "San Miguel de Tucumán, Departamento Capital, Tucumán, T4000, Argentina", "latitud": -26.830370, "longitud": -65.203813},
        {"nombre_oficial": "Municipio de Concepción, Departamento Chicligasta, Tucumán, T4174, Argentina", "latitud": -27.345925, "longitud": -65.592722},
        {"nombre_oficial": "Municipio de Aguilares, Aguilares, Departamento Río Chico, Tucumán, T4153, Argentina", "latitud": -27.431480, "longitud": -65.614663},
        {"nombre_oficial": "Municipio de Monteros, Departamento Monteros, Tucumán, T4142, Argentina", "latitud": -27.165325, "longitud": -65.497220},
        {"nombre_oficial": "Terminal Mendoza", "latitud": -32.890840, "longitud": -68.827170},
        {"nombre_oficial": "San Rafael", "latitud": -34.617550, "longitud": -68.330070},
        {"nombre_oficial": "General Alvear", "latitud": -34.978580, "longitud": -67.697470},
        {"nombre_oficial": "Malargüe", "latitud": -35.475210, "longitud": -69.585570},
    ]

    ubicaciones = []
    for ud in ubicaciones_data:
        ub, _ = Ubicacion.objects.get_or_create(nombre_oficial=ud["nombre_oficial"], defaults={"latitud": ud["latitud"], "longitud": ud["longitud"]})
        ubicaciones.append(ub)

    # 4. Crear Viajes
    viajes_data = [
        # Viaje de Cata Internacional
        {
            "empresa": empresa_cata,
            "horario": time(10, 0),
            "duracion": timedelta(hours=3),
            "dias": ["LUNES", "MIERCOLES", "VIERNES"],
            "plataformas": [1, 2],
            "demora_min": 0,
            "estado": "A_TIEMPO",
            "motivo": None,
            "paradas": [
                {"ubicacion": 8, "tiempo": 0, "precio": 0},
                {"ubicacion": 9, "tiempo": 120, "precio": 1500},
                {"ubicacion": 10, "tiempo": 210, "precio": 2500},
            ]
        },
        # Viaje de TESA (el del ejemplo del JSON del usuario)
        {
            "empresa": empresa_tesa,
            "horario": time(15, 0),
            "duracion": timedelta(hours=3, minutes=30),
            "dias": ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"],
            "plataformas": [1, 2, 3, 4, 5],
            "demora_min": 0,
            "estado": "A_TIEMPO",
            "motivo": None,
            "paradas": [
                {"ubicacion": 6, "tiempo": 140, "precio": 12000}, # Aguilares
                {"ubicacion": 5, "tiempo": 160, "precio": 14000}, # Concepción
                {"ubicacion": 7, "tiempo": 180, "precio": 14500}, # Monteros
                {"ubicacion": 4, "tiempo": 220, "precio": 16000}, # SM Tucumán
            ]
        },
        # Viaje con demora de Flecha Bus
        {
            "empresa": empresa_flecha,
            "horario": time(14, 30),
            "duracion": timedelta(hours=4),
            "dias": ["MARTES", "JUEVES", "SABADO"],
            "plataformas": [3],
            "demora_min": 45,
            "estado": "DEMORADO",
            "motivo": "Corte de ruta nacional",
            "paradas": [
                {"ubicacion": 3, "tiempo": 0, "precio": 0}, # Catamarca
                {"ubicacion": 1, "tiempo": 90, "precio": 8000}, # Chumbicha
                {"ubicacion": 0, "tiempo": 240, "precio": 15000}, # Belén
            ]
        },
        # Viaje ya partido de Chevallier
        {
            "empresa": empresa_chevallier,
            "horario": time(8, 0),
            "duracion": timedelta(hours=5),
            "dias": ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"],
            "plataformas": [5, 6],
            "demora_min": 0,
            "estado": "FINALIZADO",
            "motivo": None,
            "paradas": [
                {"ubicacion": 3, "tiempo": 0, "precio": 0}, # Catamarca
                {"ubicacion": 2, "tiempo": 300, "precio": 18000}, # Fiambalá
            ]
        },
    ]

    for vd in viajes_data:
        viaje, created = Viaje.objects.get_or_create(
            empresa=vd["empresa"],
            horario_embarcacion=vd["horario"],
            defaults={
                "duracion": vd["duracion"],
                "dias_operativos": vd["dias"],
                "plataformas_asignadas": vd["plataformas"],
                "estado": vd["estado"],
                "demora": timedelta(minutes=vd["demora_min"]),
                "motivo_demora": vd["motivo"]
            }
        )

        if created:
            for idx, pd in enumerate(vd["paradas"]):
                Parada.objects.create(
                    viaje=viaje,
                    ubicacion=ubicaciones[pd["ubicacion"]],
                    orden=idx + 1,
                    tiempo_desde_salida=timedelta(minutes=pd["tiempo"]),
                    precio=pd["precio"]
                )

    print("✅ Datos de ejemplo (Terminales, Empresas, Viajes y Paradas) creados exitosamente.")

if __name__ == "__main__":
    seed_data()
