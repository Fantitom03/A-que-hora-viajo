from django.db import models
from datetime import timedelta

# 1. Configuración de la Terminal (Usaremos un modelo de fila única)
class Terminal(models.Model):
    nombre = models.CharField(max_length=100, default="Terminal Central")
    cantidad_plataformas = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Terminales"

# 2. Empresas de Colectivo
class Empresa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ventanilla = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre

# 3. Empleados (Extendemos el usuario base de Django)
# El "DNI" del empleado se guardará en el campo 'username' del modelo User de Django
class Empleado(models.Model):
    ROLES = [
        ('ENCARGADO', 'Encargado de Sucursal'),
        ('VENTANILLA', 'Empleado de Ventanilla'),
    ]
    
    usuario = models.OneToOneField('usuarios.Usuario', on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empleados')
    rol = models.CharField(max_length=20, choices=ROLES, default='VENTANILLA')

    def __str__(self):
        return f"{self.usuario.username} ({self.rol} en {self.empresa.nombre})"


# 4. El Viaje (El núcleo del sistema)
class Viaje(models.Model):
    ESTADOS = [
        ('A_TIEMPO', 'A tiempo'),
        ('ABORDANDO', 'Abordando'),
        ('DEMORADO', 'Demorado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='viajes')
    destino = models.CharField(max_length=150)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tiempos
    fecha = models.DateField()
    horario_embarcacion = models.TimeField()
    duracion = models.DurationField(help_text="Formato: HH:MM:SS")
    
    # Como SQLite no soporta ArrayField (solo PostgreSQL), guardamos las plataformas 
    # como un texto separado por comas (Ej: "12, 13")
    plataformas_asignadas = models.CharField(max_length=50, blank=True, null=True) 
    
    # Demoras y Estado
    estado = models.CharField(max_length=20, choices=ESTADOS, default='A_TIEMPO')
    demora = models.DurationField(default=timedelta(minutes=0))
    motivo_demora = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.empresa.nombre} -> {self.destino} ({self.fecha} {self.horario_embarcacion})"


class Pasajero(models.Model):
    # Enganchamos el pasajero al sistema de login de Django
    usuario = models.OneToOneField('usuarios.Usuario', on_delete=models.CASCADE, related_name='perfil_pasajero')
    
    # Datos extra que necesitamos para la app
    telefono = models.CharField(max_length=20, unique=True, help_text="Número para notificaciones")
    recibir_alertas = models.BooleanField(default=True)

    def __str__(self):
        return f"Pasajero: {self.usuario.first_name} {self.usuario.last_name} ({self.usuario.username})"