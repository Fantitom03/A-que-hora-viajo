import pytest
from apps.viajes.models import Empresa

@pytest.mark.django_db
def test_crear_empresa(api_client, superuser, terminal):
    api_client.force_authenticate(superuser)

    response = api_client.post(
        "/api/empresa/",
        {
            "nombre": "Flecha Bus",
            "ventanilla" : 1,
            "terminal" : str(terminal.id)                           
        },
        format="json"
    )

    assert response.status_code == 201

    assert Empresa.objects.filter(nombre="Flecha Bus").exists()