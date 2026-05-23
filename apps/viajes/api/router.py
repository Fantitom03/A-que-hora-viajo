from rest_framework import routers
from .api import TerminalViewSet, EmpresaViewSet, EmpleadoViewSet, PasajeroViewSet, ViajeViewSet, ParadaViewSet, UbicacionViewSet

router = routers.DefaultRouter()

router.register(prefix='terminal', viewset=TerminalViewSet)
router.register(prefix='empresa', viewset=EmpresaViewSet)
router.register(prefix='empleado', viewset=EmpleadoViewSet)
router.register(prefix='pasajero', viewset=PasajeroViewSet)
router.register(prefix='viaje', viewset=ViajeViewSet)
router.register(prefix='parada', viewset=ParadaViewSet)
router.register(prefix='ubicacion', viewset=UbicacionViewSet)


urlpatterns = router.urls