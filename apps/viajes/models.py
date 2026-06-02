import uuid
from django.db import models
from datetime import timedelta
from django.contrib.postgres.fields import ArrayField

# 1. Configuración de la Terminal (Usaremos un modelo de fila única)
class Terminal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, default="Terminal Central")
    cantidad_plataformas = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Terminales"

# 2. Empresas de Colectivo
class Empresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    ventanilla = models.PositiveIntegerField()
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name = 'empresas', null=True, blank=True)

    def __str__(self):
        return self.nombre

# 3. Empleados (Extendemos el usuario base de Django)
# El "DNI" del empleado se guardará en el campo 'username' del modelo User de Django
class Empleado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROLES = [
        ('ENCARGADO', 'Encargado de Sucursal'),
        ('VENTANILLA', 'Empleado de Ventanilla'),
    ]
    
    usuario = models.OneToOneField('usuarios.Usuario', on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empleados')
    rol = models.CharField(max_length=20, choices=ROLES, default='VENTANILLA')

    def __str__(self):
        return f"{self.usuario.username} ({self.rol} en {self.empresa.nombre})"

# 5. Lugares (Geolocalizados)
class Ubicacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_oficial = models.CharField(max_length=200, unique=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    
    def __str__(self):
        return self.nombre_oficial

    class Meta:
        ordering = ['nombre_oficial']



# 6. El Viaje (El núcleo del sistema)
class Viaje(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    DIAS = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIERCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SABADO', 'Sábado'),
        ('DOMINGO', 'Domingo')
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='viajes')


    
    # Tiempos
    horario_embarcacion = models.TimeField()
    duracion = models.DurationField(help_text="Duración total del viaje completo")

    # Optimizados con ArrayField gracias a PostgreSQL
    dias_operativos = ArrayField(models.CharField(max_length=15, choices=DIAS), blank=True, null=True)
    
    # Plataformas asignadas (si se asignan manualmente, sino se asignan automáticamente al crear el viaje)
    plataformas_asignadas = ArrayField(models.PositiveIntegerField(), blank=True, null=True)

    # Demoras y Estado (Manejados ahora en EstadoViajeDiario)

    def __str__(self):
        ultima_parada = self.paradas.order_by('-orden').first()

        destino = (
            ultima_parada.ubicacion.nombre_oficial
            if ultima_parada else "Sin destino"
        )

        return f"{self.empresa.nombre} -> {destino}"


# 7. Las Paradas (Intermedia entre Viaje y Ubicacion)
class Parada(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='paradas')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT) # PROTECT evita que borres un lugar si un viaje lo usa
    orden = models.PositiveIntegerField() # Para saber qué parada es la 1ra, 2da, etc.
    tiempo_desde_salida = models.DurationField()
    precio = models.DecimalField(max_digits=8, decimal_places=2) # Precio para esa parada específica

    class Meta:
        ordering = ['orden'] # Siempre se listan en orden de ruta

class Pasajero(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Enganchamos el pasajero al sistema de login de Django
    usuario = models.OneToOneField('usuarios.Usuario', on_delete=models.CASCADE, related_name='perfil_pasajero')
    
    # Datos extra que necesitamos para la app
    telefono = models.CharField(max_length=20, unique=True, help_text="Número para notificaciones")
    recibir_alertas = models.BooleanField(default=True)

    def __str__(self):
        return f"Pasajero: {self.usuario.first_name} {self.usuario.last_name} ({self.usuario.username})"

# 8. Estado Diario de Viaje (Demoras y Estado por fecha)
class EstadoViajeDiario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ESTADOS = [
        ('A_TIEMPO', 'A tiempo'),
        ('ABORDANDO', 'Abordando'),
        ('DEMORADO', 'Demorado'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='estados_diarios')
    fecha = models.DateField(help_text="Fecha en la que ocurre este registro")
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='A_TIEMPO')
    tiempo_demora = models.DurationField(default=timedelta(minutes=0))
    motivo_demora = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('viaje', 'fecha')

    def __str__(self):
        return f"Estado del viaje {self.viaje.id} para el día {self.fecha} - Estado: {self.estado}"