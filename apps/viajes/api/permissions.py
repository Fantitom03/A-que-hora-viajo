from rest_framework import permissions

class EsEmpleadoOSuperuserOReadOnly(permissions.BasePermission):
    """
    PERMISOS BASADOS EN ATRIBUTOS DEL USUARIO
    ----------------------------------------------------------
    A diferencia de DjangoModelPermissions, que requiere configurar Grupos y Permisos
    manualmente en el Panel de Administración de Django, esta clase evalúa los permisos
    dinámicamente verificando las propiedades del usuario autenticado.
    
    ¿Por qué usamos esta aproximación?
    Es más escalable en un modelo multi-empresa (multi-tenant). Al depender de 
    `hasattr(request.user, 'empleado')`, automatizamos el permiso sin tener que 
    acordarnos de asignar grupos a mano cada vez que se registra un empleado.
    
    Reglas:
    - Lectura (GET, HEAD, OPTIONS): Permitida para todos (incluyendo pasajeros e invitados).
    - Escritura (POST, PUT, DELETE): Solo Superusuarios o usuarios que tengan un perfil de Empleado.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Si no hay usuario o no está autenticado, no tiene permiso para escribir
        if not request.user or not request.user.is_authenticated:
            return False
        # Si es superusuario o si tiene el perfil de empleado asociado, pasa.
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
    """
    MANEJO DE PERMISOS DE VIAJES Y PARADAS
    - Lectura (GET, HEAD, OPTIONS): Permitida para todos (incluyendo pasajeros e invitados).
    - Escritura (POST, PUT, DELETE): Solo Superusuarios o usuarios que tengan un perfil de Empleado.
    
    Además, para modificaciones a nivel de objeto, se verifica que el viaje o parada pertenezcan a la empresa del empleado autenticado.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Solo los usuarios autenticados con perfil de Empleado pueden hacer modificaciones a nivel de colección (POST)
        return request.user.is_authenticated and hasattr(request.user, 'empleado')

    # Para acciones específicas sobre objetos (PUT, PATCH, DELETE sobre un viaje o parada)
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # El superusuario de la terminal tiene control total siempre
        if request.user.is_superuser:
            return True
        # Se verifica que el viaje o la parada pertenezcan estrictamente a la empresa del empleado
        if hasattr(obj, 'empresa'):
            return obj.empresa == request.user.empleado.empresa
        if hasattr(obj, 'viaje'):
            return obj.viaje.empresa == request.user.empleado.empresa
        return False

class EsPersonalEmpresa(permissions.BasePermission):
    """
    MANEJO DE PERMISOS DE VIAJES Y ESTADOS ESTRICTO
    Solo permite el acceso a Empleados (y superusuarios).
    No permite acceso a pasajeros ni invitados.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or hasattr(request.user, 'empleado')

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'empleado'):
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
        # Los empleados pueden ver los datos de todos los pasajeros
        if hasattr(request.user, 'empleado'):
            return True
        # El pasajero solo puede ver o editar SU propio objeto de perfil
        return obj.usuario == request.user