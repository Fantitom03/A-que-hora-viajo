import pytest
from datetime import time, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.viajes.models import (Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion)

Usuario = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    return Usuario.objects.create_superuser(
        username="admin",
        password="admin",
        dni="11111222222"
    )

@pytest.fixture
def terminal(db):
    return Terminal.objects.create(
        nombre = "Terminal Test",
        cantidad_plataformas=20
    )

@pytest.fixture
def empresa(terminal):
    return Empresa.objects.create(
        nombre = "Empresa Test",
        ventanilla = 1,
        terminal = terminal
    )

@pytest.fixture
def empleado(empresa):
    usuario = Usuario.objects.create_user(
        username="empleado",
        dni="2222233333",
        password="123"
    )

    return Empleado.objects.create(
        usuario=usuario,
        empresa=empresa,
        rol="VENTANILLA"
    )

@pytest.fixture
def pasajero():
    usuario = Usuario.objects.create_user(
        username="pasajero",
        dni="2333323223",
        password="321"
    )

    return Pasajero.objects.create(
        usuario = usuario,
        telefono = "33232342433"
    )

@pytest.fixture
def ubicacion():
    return Ubicacion.objects.create(
        nombre_oficial="Belen",
        latitud=-27.65,
        longitud =-67.02
    )

@pytest.fixture
def viaje(empresa):
    return Viaje.objects.create(
        empresa = empresa,
        horario_embarcacion=time(14,0),
        duracion = timedelta(hours=8),
        dias_operativos = ["LUNES"],
        plataformas_asignadas=[1]
    )

@pytest.fixture
def parada(viaje,ubicacion):
    return Parada.objects.create(
        viaje=viaje,
        ubicacion = ubicacion,
        orden=1,
        tiempo_desde_salida=timedelta(hours=2),
        precio=1000
    )