import pytest
from datetime import time, timedelta
from unittest.mock import patch
from apps.viajes.models import Ubicacion, Viaje, Parada

@pytest.mark.django_db
@patch('apps.viajes.api.api.obtener_pronostico')
def test_filtrar_viajes_por_destino(mock_pronostico, api_client, empresa):
    mock_pronostico.return_value = "Despejado"
    
    # Creamos ubicaciones
    ubicacion_belen = Ubicacion.objects.create(nombre_oficial="Belen", latitud=-27.65, longitud=-67.02)
    ubicacion_salta = Ubicacion.objects.create(nombre_oficial="Salta", latitud=-24.78, longitud=-65.41)
    
    # Creamos 3 viajes con destino a Belén
    viajes_belen = []
    for i in range(3):
        v = Viaje.objects.create(
            empresa=empresa, 
            horario_embarcacion=time(14, i), # Diferentes minutos para que no de error de concurrencia
            duracion=timedelta(hours=8), 
            dias_operativos=["LUNES"], 
            plataformas_asignadas=[i+1]
        )
        Parada.objects.create(viaje=v, ubicacion=ubicacion_belen, orden=1, tiempo_desde_salida=timedelta(hours=2), precio=1000)
        viajes_belen.append(v)
        
    # Creamos 2 viajes con destino a Salta
    viajes_salta = []
    for i in range(2):
        v = Viaje.objects.create(
            empresa=empresa, 
            horario_embarcacion=time(16, i), 
            duracion=timedelta(hours=5), 
            dias_operativos=["LUNES"], 
            plataformas_asignadas=[i+10]
        )
        Parada.objects.create(viaje=v, ubicacion=ubicacion_salta, orden=1, tiempo_desde_salida=timedelta(hours=1), precio=500)
        viajes_salta.append(v)

    # Ejecutamos la búsqueda filtrando por Belén el día LUNES
    response = api_client.post(
        "/api/viaje/buscar_viajes/",
        {
            "destino": "Belen",
            "dia": "LUNES"
        },
        format="json"
    )
    
    # Validaciones
    assert response.status_code == 200
    
    # Verificar cantidad (deben ser exactamente 3)
    assert len(response.data) == 3
    
    # Extraer los horarios de salida para verificar identidad (ya que la respuesta usa horas de salida formateadas)
    horarios_devueltos = [item['hora_salida_original'] for item in response.data]
    
    # Confirmar que los 3 viajes a Belén están en la respuesta
    for v in viajes_belen:
        assert v.horario_embarcacion.strftime("%H:%M") in horarios_devueltos
        
    # Confirmar que los viajes a Salta NO están en la respuesta
    for v in viajes_salta:
        assert v.horario_embarcacion.strftime("%H:%M") not in horarios_devueltos

@pytest.mark.django_db
def test_buscar_viajes_faltan_parametros(api_client):
    # Faltan ambos parámetros
    response = api_client.post("/api/viaje/buscar_viajes/", {}, format="json")
    assert response.status_code == 400
    assert "Debe enviar destino y dia de semana" in str(response.data)

    # Falta el día
    response2 = api_client.post("/api/viaje/buscar_viajes/", {"destino": "Belen"}, format="json")
    assert response2.status_code == 400

@pytest.mark.django_db
def test_buscar_viajes_dia_invalido(api_client):
    response = api_client.post(
        "/api/viaje/buscar_viajes/",
        {"destino": "Belen", "dia": "DOMINGOS"},
        format="json"
    )
    assert response.status_code == 400
    assert "Dia invalido" in str(response.data)
