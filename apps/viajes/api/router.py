from rest_framework import routers
from rest_framework import routers
from .api import (TerminalViewSet, EmpresaViewSet, EmpleadoViewSet, 
                    PasajeroViewSet, ViajeViewSet, ParadaViewSet, UbicacionViewSet)

router = routers.DefaultRouter()

router.register(prefix='terminal', viewset=TerminalViewSet, basename='terminal')
router.register(prefix='empresa', viewset=EmpresaViewSet, basename='empresa')
router.register(prefix='empleado', viewset=EmpleadoViewSet, basename='empleado')
router.register(prefix='pasajero', viewset=PasajeroViewSet, basename='pasajero')
router.register(prefix='viaje', viewset=ViajeViewSet, basename='viaje')
router.register(prefix='parada', viewset=ParadaViewSet, basename='parada')
router.register(prefix='ubicacion', viewset=UbicacionViewSet, basename='ubicacion')

urlpatterns = router.urls