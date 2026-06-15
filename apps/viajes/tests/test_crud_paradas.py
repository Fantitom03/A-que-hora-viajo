import pytest

from apps.viajes.models import Parada


@pytest.mark.django_db
def test_crear_parada(api_client, empleado, viaje, ubicacion):
    api_client.force_authenticate(user=empleado.usuario)
    
    response = api_client.post(
        "/api/parada/",
        {
            "viaje": str(viaje.id),
            "ubicacion" : str(ubicacion.id),
            "orden" : 2,
            "tiempo_desde_salida" : "03:00:00",
            "precio" : "1500"
        },
        fromat="json"
    )

    assert response.status_code == 201

    assert Parada.objects.filter(viaje=viaje, ubicacion=ubicacion, orden=2).exists()


@pytest.mark.django_db
def test_listar_paradas(api_client, empleado, parada):
    api_client.force_authenticate(user=empleado.usuario)

    response = api_client.get("/api/parada/")

    assert response.status_code == 200

    assert len(response.data) >= 1

@pytest.mark.django_db
def test_obtener_parada(api_client, empleado, parada):
    api_client.force_authenticate(user=empleado.usuario)

    response = api_client.get(f"/api/parada/{parada.id}/")

    assert response.status_code == 200

    assert str(response.data["id"]) == str(parada.id)


@pytest.mark.django_db
def test_actualizar_parada(api_client, empleado, parada):
    api_client.force_authenticate(user=empleado.usuario)

    response = api_client.put(
        f"/api/parada/{parada.id}/",
        {
            "viaje": str(parada.viaje.id),
            "ubicacion": str(parada.ubicacion.id),
            "orden": parada.orden,
            "tiempo_desde_salida": "02:00:00",
            "precio": "2000.00"
        },
        format="json"
    )

    print(response.data)
    assert response.status_code == 200

    parada.refresh_from_db()

    assert float(parada.precio) == 2000


@pytest.mark.django_db
def test_eliminar_parada(api_client, empleado, parada):
    api_client.force_authenticate(user=empleado.usuario)

    response = api_client.delete(f"/api/parada/{parada.id}/")

    assert response.status_code == 204

    assert not Parada.objects.filter(id=parada.id).exists()