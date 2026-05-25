from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class CustomUserAdmin(UserAdmin):
    # Agregamos el DNI a las vistas de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('dni',)}),
    )
    # Agregamos el DNI a la pantalla de creación de usuarios
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {'fields': ('dni',)}),
    )

admin.site.register(Usuario, CustomUserAdmin)
