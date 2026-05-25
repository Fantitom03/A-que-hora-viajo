from django.contrib import admin
from .models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion

# Registramos los modelos base de la infraestructura
admin.site.register(Terminal)
admin.site.register(Empresa)

# Registramos los roles
admin.site.register(Empleado)
admin.site.register(Pasajero)

# Registramos la lógica de los colectivos
admin.site.register(Viaje)
admin.site.register(Parada)
admin.site.register(Ubicacion)