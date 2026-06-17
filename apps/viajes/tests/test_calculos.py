import pytest
from django.utils import timezone
from apps.viajes.models import Viaje

@pytest.mark.django_db
def test_registrar_demora_viaje(api_client, empleado, viaje):
    # Autenticamos como empleado de la empresa a la que pertenece el viaje
    api_client.force_authenticate(empleado.usuario)
    
    # Hacemos la petición para registrar 30 minutos de demora
    response = api_client.post(
        f"/api/viaje/{viaje.id}/actualizar_estado_diario/",
        {"demora_minutos": 30},
        format="json"
    )
    
    assert response.status_code == 200
    
    # refrescamos la instancia del viaje para que se reflejen los cambios en la base de datos
    viaje.refresh_from_db()
    
    fecha_hoy = timezone.localdate()
    registro = viaje.estados_diarios.filter(fecha=fecha_hoy).first()
    
    assert registro is not None
    assert registro.estado == "DEMORADO"
    assert registro.tiempo_demora == timezone.timedelta(minutes=30)

@pytest.mark.django_db
def test_registrar_demora_sin_autenticacion(api_client, viaje):
    # Intentamos registrar demora sin estar autenticados
    response = api_client.post(
        f"/api/viaje/{viaje.id}/actualizar_estado_diario/",
        {"demora_minutos": 30},
        format="json"
    )
    assert response.status_code == 401

@pytest.mark.django_db
def test_registrar_demora_empleado_equivocado(api_client, viaje, empleado_b):
    # Utilizamos el fixture empleado_b (que pertenece a empresa_b)
    api_client.force_authenticate(empleado_b.usuario)
    
    # Intentamos registrar demora en un viaje de la primera empresa
    response = api_client.post(
        f"/api/viaje/{viaje.id}/actualizar_estado_diario/",
        {"demora_minutos": 30},
        format="json"
    )
    # Debería dar 404 porque el queryset lo filtra para empleados que no son de la misma empresa
    assert response.status_code == 404
