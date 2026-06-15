import pytest
from unittest.mock import patch
from apps.viajes.models import Ubicacion

@pytest.mark.django_db
@patch('apps.viajes.api.api.requests.get')
def test_crear_ubicacion_con_mock_nominatim(mock_get, api_client, superuser):
    api_client.force_authenticate(superuser)
    
    # Configuramos el mock de la respuesta de Nominatim
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{
        'lat': '-27.65',
        'lon': '-67.02',
        'display_name': 'Belén, Catamarca, Argentina'
    }]
    
    response = api_client.post(
        "/api/ubicacion/",
        {"nombre_oficial": "Belen"},
        format="json"
    )
    
    assert response.status_code == 201
    assert mock_get.called
    assert response.data['nombre_oficial'] == 'Belén, Catamarca, Argentina'
    assert float(response.data['latitud']) == -27.65
    assert float(response.data['longitud']) == -67.02
    assert Ubicacion.objects.filter(nombre_oficial='Belén, Catamarca, Argentina').exists()


@pytest.mark.django_db
@patch('apps.viajes.api.api.obtener_pronostico')
def test_buscar_viajes_con_mock_clima(mock_pronostico, api_client, viaje, parada):
    # 'viaje' y 'parada' son fixtures de conftest.py
    # La vista buscar_viajes permite AllowAny, por lo que no es necesario autenticarse
    
    mock_pronostico.return_value = "Soleado Mock, 25°C"
    
    response = api_client.post(
        "/api/viaje/buscar_viajes/",
        {
            "destino": "Belen",
            "dia": "LUNES"
        },
        format="json"
    )
    
    assert response.status_code == 200
    assert len(response.data) > 0
    assert mock_pronostico.called
    assert response.data[0]['clima_estimado'] == "Soleado Mock, 25°C"

@pytest.mark.django_db
@patch('apps.viajes.api.api.requests.get')
def test_crear_ubicacion_no_encontrada(mock_get, api_client, superuser):
    api_client.force_authenticate(superuser)
    
    # Simulamos que Nominatim no encontró resultados
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = []
    
    response = api_client.post(
        "/api/ubicacion/",
        {"nombre_oficial": "Ciudad Inexistente XYZ"},
        format="json"
    )
    
    assert response.status_code == 404
    assert response.data['error'] == 'La ubicación no pudo ser encontrada.'
