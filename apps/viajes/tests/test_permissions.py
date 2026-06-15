import pytest
from apps.viajes.models import Empresa


@pytest.mark.django_db
def test_admin_puede_crear_empresa(api_client, superuser, terminal):
    api_client.force_authenticate(user=superuser)

    response = api_client.post(
        "/api/empresa/",
        {
            "nombre": "Flecha Bus",
            "ventanilla": 15,
            "terminal" : str(terminal.id)
        },
        format="json"
    )

    assert response.status_code == 201

    assert Empresa.objects.filter(nombre="Flecha Bus").exists()

@pytest.mark.django_db
def test_pasajero_no_puede_crear_empresa(api_client, pasajero, terminal):
    api_client.force_authenticate(user=pasajero.usuario)

    response = api_client.post(
        "/api/empresa/",
        {
            "nombre": "Flecha Bus",
            "ventanilla": 15,
            "terminal" : str(terminal.id)
        },
        format="json"
    )

    assert response.status_code == 403