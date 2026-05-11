from rest_framework import routers
from .api import TerminalViewSet, EmpresaViewSet, EmpleadoViewSet, PasajeroViewSet, ViajeViewSet

router = routers.DefaultRouter()

router.register(prefix='terminal', viewset=TerminalViewSet)
router.register(prefix='empresa', viewset=EmpresaViewSet)
router.register(prefix='empleado', viewset=EmpleadoViewSet)
router.register(prefix='pasajero', viewset=PasajeroViewSet)
router.register(prefix='viaje', viewset=ViajeViewSet)


urlpatterns = router.urls