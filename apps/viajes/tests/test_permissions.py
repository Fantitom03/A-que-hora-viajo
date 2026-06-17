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

@pytest.mark.django_db
def test_empleado_no_puede_acceder_a_viajes_de_otra_empresa(api_client, empleado_b, viaje, empresa):
    # empleado_b pertenece a empresa_b. viaje pertenece a empresa.
    api_client.force_authenticate(user=empleado_b.usuario)

    # Intenta ver el viaje de la otra empresa
    response_get = api_client.get(f"/api/viaje/{viaje.id}/")
    assert response_get.status_code == 404

@pytest.mark.django_db
def test_empleado_no_puede_modificar_viajes_de_otra_empresa(api_client, empleado_b, viaje, empresa):
    api_client.force_authenticate(user=empleado_b.usuario)

    # Intenta modificar el viaje de la otra empresa
    payload_patch = {"horario_embarcacion": "15:00:00"}
    response_patch = api_client.patch(f"/api/viaje/{viaje.id}/", payload_patch, format="json")
    assert response_patch.status_code == 404

@pytest.mark.django_db
def test_empleado_no_puede_crear_viajes_en_otra_empresa(api_client, empleado_b, empresa):
    api_client.force_authenticate(user=empleado_b.usuario)

    # Intenta crear un viaje asignándolo a la otra empresa
    payload_post = {
        "empresa": str(empresa.id),
        "horario_embarcacion": "10:00:00",
        "duracion": "05:00:00",
        "dias_operativos": ["LUNES"],
        "plataformas_asignadas": [1]
    }
    response_post = api_client.post("/api/viaje/", payload_post, format="json")
    assert response_post.status_code in [403, 400]

@pytest.mark.django_db
def test_pasajero_no_puede_acceder_otro_pasajero(api_client, pasajero, pasajero_b):
    # Autenticamos como el atacante (pasajero_b)
    api_client.force_authenticate(user=pasajero_b.usuario)

    # Intentamos ver el perfil del primer pasajero
    response_get = api_client.get(f"/api/pasajero/{pasajero.id}/")
    assert response_get.status_code == 404

@pytest.mark.django_db
def test_pasajero_no_puede_modificar_otro_pasajero(api_client, pasajero,pasajero_b):
    # Autenticamos como el atacante (pasajero_b)
    api_client.force_authenticate(user=pasajero_b.usuario)

    # Intentamos modificar el perfil del primer pasajero
    payload_patch = {"telefono": "999888777"}
    response_patch = api_client.patch(f"/api/pasajero/{pasajero.id}/", payload_patch, format="json")
    assert response_patch.status_code == 404
