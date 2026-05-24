from rest_framework import permissions

class EsEmpleadoOSuperuserOReadOnly(permissions.BasePermission):
    """
    Las ubicaciones pueden ser leídas por cualquiera (pasajeros incluidos).
    Pero solo pueden ser creadas o modificadas por Empleados (Ventanilla/Encargado) o Superusuarios.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        # Si es superusuario o si tiene el perfil de empleado, pasa.
        return request.user.is_superuser or hasattr(request.user, 'empleado')

class EsEncargadoOSuperuser(permissions.BasePermission):
    """
    Permiso estricto para el CRUD de Empleados.
    Solo Superusuarios o Encargados pueden acceder.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'empleado') and request.user.empleado.rol == 'ENCARGADO'

    def has_object_permission(self, request, view, obj):
        # El superusuario de la terminal tiene control total siempre
        if request.user.is_superuser:
            return True
        # Si es encargado, comprobamos que el empleado que quiere editar/borrar sea de SU empresa
        if hasattr(request.user, 'empleado'):
            return obj.empresa == request.user.empleado.empresa
        return False

class EsPersonalEmpresaOReadOnly(permissions.BasePermission):
    '''
    Los pasajeros solo leen. 
    Los empleados solo ven/modifican datos de SU propia empresa.
    '''
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Solo los usuarios autenticados con perfil de Empleado pueden hacer modificaciones
        return request.user.is_authenticated and hasattr(request.user, 'empleado')

    # Para acciones específicas sobre objetos (como editar un viaje o una parada), se verifica que el objeto pertenezca a la empresa del empleado.
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

class EsPasajeroOInvitado(permissions.BasePermission):
    """
    Permiso para el PasajeroViewSet:
    - Permite crear (POST / registrarse) de forma pública.
    - Para ver/modificar (GET, PUT, DELETE), exige ser el dueño del perfil.
    """
    def has_permission(self, request, view):
        # Permite el registro público (POST)
        if request.method == 'POST':
            return True
        # Para cualquier otra acción, el usuario sí o sí debe estar logueado
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # El superusuario de la terminal puede auditar todo si quiere
        if request.user.is_superuser:
            return True
        # El pasajero solo puede ver o editar SU propio objeto de perfil
        return obj.usuario == request.user