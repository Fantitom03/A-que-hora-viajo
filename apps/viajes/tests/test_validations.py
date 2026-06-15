import pytest

from apps.viajes.models import Pasajero

@pytest.mark.django_db
def test_registro_pasajero_dni_duplicado(api_client, pasajero):

    response = api_client.post(
        "/api/pasajero/",
        {
            "username": "otro_usuario",
            "dni" : pasajero.usuario.dni,
            "password" : "000000000",
            "first_name": "Juan",
            "last_name" : "Perez",
            "telefono": "11111111"
        },
        format="json"
    )

    assert response.status_code == 400
    assert response.data["error"][0] == "Este usuario o DNI ya está registrado."
    assert not Pasajero.objects.filter(usuario__username="otro_usuario").exists()

@pytest.mark.django_db
def test_registro_pasajero_telefono_duplicado(api_client, pasajero):

    response = api_client.post(
        "/api/pasajero/",
        {
            "username": "jcarlos",
            "dni":"56889003",
            "password" : "12345678",
            "first_name" :"Juan",
            "last_name" : "Martinez",
            "telefono": pasajero.telefono
        },
        format = "json"
    )

    assert response.status_code == 400
    assert response.data["telefono"][0] == "Ya existe un/a pasajero con este/a telefono."
    assert not Pasajero.objects.filter(usuario__username="jcarlos").exists()

@pytest.mark.django_db
def test_registro_pasajero_correcto(api_client):

    response = api_client.post(
        "/api/pasajero/",
        {
            "username": "joaquinnn",
            "dni": "43155464",
            "password": "87654321",
            "first_name": "Joaquin",
            "last_name": "Centeno",
            "telefono": "4728494212"
        },
        format = "json"
    )


    assert response.status_code == 201

    assert Pasajero.objects.filter(usuario__username="joaquinnn").exists()