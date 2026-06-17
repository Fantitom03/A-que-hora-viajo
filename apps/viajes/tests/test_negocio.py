import pytest
from rest_framework import status

@pytest.mark.django_db
def test_concurrencia_viaje_plataforma(api_client, empleado, viaje):

    api_client.force_authenticate(empleado.usuario)
    
    payload = {
        "empresa": str(empleado.empresa.id),
        "horario_embarcacion": "14:00:00",
        "duracion": "08:00:00",
        "dias_operativos": ["LUNES"],
        "plataformas_asignadas": [1]
    }
    
    # Intentamos crear otro viaje idéntico concurrente
    response = api_client.post("/api/viaje/", payload, format="json")
    
    # Verificamos que la API lo rechaza
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Verificamos el mensaje de error de validación personalizado
    assert "Ya existe un viaje usando esa plataforma, en el mismo horario y días" in str(response.data)

@pytest.mark.django_db
def test_modificar_perfil_pasajero(api_client, pasajero):
    api_client.force_authenticate(pasajero.usuario)
    
    payload = {
        "telefono": "999888777"
    }
    
    response = api_client.patch(f"/api/pasajero/{pasajero.id}/", payload, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    
    # Assert de identidad visual
    assert response.data['id'] == str(pasajero.id)
    assert response.data['telefono'] == "999888777"

@pytest.mark.django_db
def test_modificar_perfil_campos_bloqueados(api_client, pasajero):
    api_client.force_authenticate(pasajero.usuario)
    
    payload = {
        "dni": "12345678"
    }
    
    response = api_client.patch(f"/api/pasajero/{pasajero.id}/", payload, format="json")
    
    assert response.status_code == 400
    assert "error" in response.data
    assert "No tienes autorización para modificar 'dni'" in str(response.data)


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
