from rest_framework import permissions

class EsPersonalEmpresaOReadOnly(permissions.BasePermission):
    """
    Seguridad global: Los pasajeros solo leen. 
    Los empleados solo ven/modifican datos de SU propia empresa.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and hasattr(request.user, 'empleado')

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # El superusuario de la terminal tiene control total siempre
        if request.user.is_superuser:
            return True
        # Se verifica si el viaje o la parada pertenecen a la empresa del empleado
        if hasattr(obj, 'empresa'):
            return obj.empresa == request.user.empleado.empresa
        if hasattr(obj, 'viaje'):
            return obj.viaje.empresa == request.user.empleado.empresa
        return False

class EsEncargado(permissions.BasePermission):
    """Permiso exclusivo para acciones de gerencia/encargado."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated 
            and hasattr(request.user, 'empleado') 
            and request.user.empleado.rol == 'ENCARGADO'
        )