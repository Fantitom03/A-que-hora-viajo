import requests
from rest_framework import serializers
from datetime import datetime, date, timedelta
from django.conf import settings
from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion, EstadoViajeDiario
from django.contrib.auth import get_user_model
UsuarioBase = get_user_model()

# --- Modelos Base ---

class TerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terminal
        fields = ['id', 'nombre', 'cantidad_plataformas']


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Empresa
        fields = ['id', 'nombre', 'ventanilla', 'terminal']

    # Si la empresa tiene una terminal asignada, en la representación se muestra el nombre de la terminal en lugar del ID
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.terminal:
            representation['terminal'] = {'nombre_terminal': instance.terminal.nombre}
        return representation

    # Validación ventanilla (debe ser mayor a 0)
    def validate_ventanilla(self, data):
        if data <= 0:
            raise serializers.ValidationError("El número de ventanilla debe ser mayor a 0")
        return data
    
    # Validación de duplicidad de ventanilla en la misma terminal
    def validate(self, data):
        terminal = data.get('terminal')
        ventanilla = data.get('ventanilla')
        if Empresa.objects.filter(terminal=terminal, ventanilla=ventanilla).exists():
            raise serializers.ValidationError("Ya existe una empresa usando esa ventanilla en esta terminal")
        return data

class EmpleadoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    dni = serializers.CharField(write_only=True)
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all(), required=False)
    rol = serializers.ChoiceField(choices=Empleado.ROLES, default='VENTANILLA')

    class Meta:
        model = Empleado
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'dni', 'usuario', 'empresa', 'rol']
        read_only_fields = ['usuario']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request:
            return attrs
            
        if request.method == 'POST':
            username = attrs.get('username')
            dni = attrs.get('dni')
            
            # Verificamos duplicados
            if UsuarioBase.objects.filter(username=username).exists() or UsuarioBase.objects.filter(dni=dni).exists():
                raise serializers.ValidationError({"error": "Este DNI o username ya está registrado como usuario en el sistema."})
                
            # Si es superusuario, debe mandar la empresa
            if request.user.is_superuser:
                if 'empresa' not in attrs:
                    raise serializers.ValidationError({"empresa": "Como superusuario, debe especificar el ID de la 'empresa' a la que pertenecerá el empleado."})
            else:
                # Si es encargado, lo asignamos a su misma empresa automáticamente
                attrs['empresa'] = request.user.empleado.empresa
                
        return attrs

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        dni = validated_data.pop('dni')
        
        nuevo_usuario = UsuarioBase.objects.create_user(
            username=username,
            dni=dni,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        empleado = Empleado.objects.create(usuario=nuevo_usuario, **validated_data)
        return empleado

    # Representación del empleado, muestra el username y el nombre de la empresa.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['usuario'] = {
            'username': instance.usuario.username,
            # 'dni': instance.usuario.dni  # Descomentar si agregaste el campo dni a tu modelo custom User
        }
        representation['empresa'] = {'nombre_empresa': instance.empresa.nombre}
        return representation

class PasajeroSerializer(serializers.ModelSerializer):
    # Declaramos los campos planos. Los hacemos opcionales (required=False) para que los PATCH parciales funcionen bien sin obligar a mandar contraseña siempre.
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    dni = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Pasajero
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'dni', 'telefono', 'recibir_alertas']

    def create(self, validated_data):
        # 1. Sacamos los campos sueltos que vinieron en la raíz del JSON
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        dni = validated_data.pop('dni', '')
        
        # 2. Creamos el usuario base encriptando su contraseña
        nuevo_usuario = UsuarioBase.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dni=dni
        )
        
        # 3. Creamos el perfil del pasajero atado a ese usuario
        pasajero = Pasajero.objects.create(usuario=nuevo_usuario, **validated_data)
        return pasajero

    def update(self, instance, validated_data):
        # 1. Separamos los datos que corresponden al UsuarioBase
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        dni = validated_data.pop('dni', None)
        
        # 2. Actualizamos el perfil del pasajero (telefono, recibir_alertas) con lo que quede
        instance = super().update(instance, validated_data)
        
        # 3. Actualizamos el UsuarioBase si nos pasaron algún dato
        usuario = instance.usuario
        modificado = False
        
        if username is not None:
            usuario.username = username
            modificado = True
        if first_name is not None:
            usuario.first_name = first_name
            modificado = True
        if last_name is not None:
            usuario.last_name = last_name
            modificado = True
        if dni is not None:
            usuario.dni = dni
            modificado = True
        if password is not None:
            usuario.set_password(password) # set_password maneja la encriptación automáticamente
            modificado = True
            
        if modificado:
            usuario.save()
            
        return instance

    # En la representación del pasajero, se muestra el username y el nombre completo del usuario asociado en lugar de su ID.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        representation['usuario'] = {
            'username': instance.usuario.username,
            'nombre_completo': f"{instance.usuario.first_name} {instance.usuario.last_name}"
        }
        
        return representation
    
    # Método para validar los datos del serializer para que el usuario común no pueda modificar datos que no debe.
    def validate(self, attrs):
        # Obtenemos el request para saber qué método HTTP estamos usando
        request = self.context.get('request')
        
        # Validación de unicidad en la creación
        if request and request.method == 'POST':
            username = attrs.get('username')
            dni = attrs.get('dni')
            telefono = attrs.get('telefono')
            
            if UsuarioBase.objects.filter(username=username).exists() or UsuarioBase.objects.filter(dni=dni).exists():
                raise serializers.ValidationError({"error": "Este usuario o DNI ya está registrado."})
            
            if Pasajero.objects.filter(telefono=telefono).exists():
                raise serializers.ValidationError({"error": "Este teléfono ya está registrado."})
        
        # Solo aplicamos esta restricción si estamos actualizando (PUT o PATCH)
        # Un usuario común es aquel que NO es superadmin ni empleado.
        is_admin_o_empleado = request.user.is_superuser or hasattr(request.user, 'empleado')
        if request and request.method in ['PUT', 'PATCH'] and not is_admin_o_empleado:
            
            # Verificamos si el usuario común intenta mandar datos que no debe
            campos_bloqueados = ['username', 'password', 'first_name', 'last_name', 'dni']
            
            for campo in campos_bloqueados:
                if campo in request.data:
                    raise serializers.ValidationError({
                        "error": f"No tienes autorización para modificar '{campo}'. Si necesitas cambiar tus datos personales, por favor comunícate con un administrador o empleado por ventanilla."
                    })
                     
        return attrs



# --- Modelos Clave del Sistema ---
    
class UbicacionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ubicacion
        fields = ['id', 'nombre_oficial', 'latitud', 'longitud']

    # Al interceptar la validación, redondeamos la latitud y longitud a 6 decimales para asegurar el formato correcto, y validamos que estén dentro de los rangos permitidos.
    def validate_latitud(self, value):
        value = round(float(value), 6)
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitud inválida")
        return value
    
    def validate_longitud(self, value):
        value = round(float(value), 6)
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitud inválida")
        return value


class ParadaSerializer(serializers.ModelSerializer):
    ubicacion_detalles = UbicacionSerializer(source='ubicacion', read_only=True)
    horario_estimado_parada = serializers.SerializerMethodField()

    class Meta:
        model = Parada
        fields = ['id', 'viaje', 'ubicacion', 'ubicacion_detalles', 'orden', 'tiempo_desde_salida', 'precio', 'horario_estimado_parada']

    # Lógica para calcular el horario estimado de llegada a esta parada, sumando el tiempo desde la salida al horario de embarcación del viaje, 
    # y considerando las demoras informadas por ventanilla.
    def get_horario_estimado_parada(self, obj):
        viaje = obj.viaje
        base_datetime = datetime.combine(date.today(), viaje.horario_embarcacion)
        registro = viaje.estados_diarios.filter(fecha=date.today()).first()
        demora = registro.tiempo_demora if registro else timedelta(minutes=0)
        resultado = base_datetime + obj.tiempo_desde_salida + demora
        return resultado.time().strftime("%H:%M")

    # Validacion de orden de parada (debe ser mayor a 0)
    def validate_orden(self, data):
        if data <= 0: raise serializers.ValidationError("El orden debe ser mayor a 0")
        return data

    # Validacion de precio
    def validate_precio(self, data):
        if data <= 0: raise serializers.ValidationError("El precio debe ser mayor a 0")
        return data
    
    # Validacion de tiempo desde salida (no puede ser negativo)
    def validate_tiempo_desde_salida(self, data):
        if data.total_seconds() < 0: raise serializers.ValidationError("El tiempo no puede ser negativo")
        return data
    
    # Validacion de duplicidad de orden y ubicación en el mismo viaje
    def validate(self, data):

        queryset = Parada.objects.all()

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(
            viaje=data['viaje'],
            orden=data['orden']
        ).exists():
            raise serializers.ValidationError(
                "Ya existe una parada con ese orden en el viaje"
            )

        if queryset.filter(
            viaje=data['viaje'],
            ubicacion=data['ubicacion']
        ).exists():
            raise serializers.ValidationError(
                "La ubicación ya existe en este viaje"
            )

        return data


class ViajeSerializer(serializers.ModelSerializer):
    paradas = ParadaSerializer(many=True, read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    terminal_nombre = serializers.CharField(source='empresa.terminal.nombre', read_only=True, allow_null=True)
    terminal_id = serializers.UUIDField(source='empresa.terminal.id', read_only=True, allow_null=True)
    horario_llegada_final = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    demora = serializers.SerializerMethodField()
    motivo_demora = serializers.SerializerMethodField()
    horario_embarcacion_actualizado = serializers.SerializerMethodField()

    class Meta:
        model = Viaje
        fields = '__all__'

    def get_registro_hoy(self, obj):
        request = self.context.get('request')
        fecha_consulta = date.today()
        if request and request.query_params.get('fecha'):
            try:
                fecha_consulta = datetime.strptime(request.query_params.get('fecha'), "%Y-%m-%d").date()
            except ValueError:
                pass
        
        if not hasattr(obj, f'_registro_{fecha_consulta}'):
            from apps.viajes.api.services.viajes_service import actualizar_estado_viaje_lazy
            # Llamamos a nuestro servicio de actualización perezosa de estados de viajes, 
            # que actualiza el estado del viaje si es necesario y lo persiste en la base de datos.
            registro = actualizar_estado_viaje_lazy(obj, fecha_consulta)
            setattr(obj, f'_registro_{fecha_consulta}', registro)
        return getattr(obj, f'_registro_{fecha_consulta}')

    def get_estado(self, obj):
        registro = self.get_registro_hoy(obj)
        return registro.estado if registro else 'A_TIEMPO'

    def get_demora(self, obj):
        registro = self.get_registro_hoy(obj)
        return registro.tiempo_demora if registro else timedelta(minutes=0)

    def get_motivo_demora(self, obj):
        registro = self.get_registro_hoy(obj)
        return registro.motivo_demora if registro else None

    def get_horario_llegada_final(self, obj):
        request = self.context.get('request')
        fecha_consulta = date.today()
        if request and request.query_params.get('fecha'):
            try:
                fecha_consulta = datetime.strptime(request.query_params.get('fecha'), "%Y-%m-%d").date()
            except ValueError:
                pass

        base_datetime = datetime.combine(fecha_consulta, obj.horario_embarcacion)
        demora = self.get_demora(obj)
        resultado = base_datetime + obj.duracion + demora
        return resultado.time().strftime("%H:%M")

    def get_horario_embarcacion_actualizado(self, obj):
        request = self.context.get('request')
        fecha_consulta = date.today()
        if request and request.query_params.get('fecha'):
            try:
                fecha_consulta = datetime.strptime(request.query_params.get('fecha'), "%Y-%m-%d").date()
            except ValueError:
                pass

        base_datetime = datetime.combine(fecha_consulta, obj.horario_embarcacion)
        demora = self.get_demora(obj)
        resultado = base_datetime + demora
        return resultado.time().strftime("%H:%M")

    # Validacion de días operativos
    def validate_dias_operativos(self, data):
        dias_validos = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
        # Valida que cada elemento en data sea un día de la semana válido.
        for dia in data:
            if dia.upper() not in dias_validos:
                raise serializers.ValidationError(f"{dia} no es un día válido")
        return data
    
    # Validación de duración
    def validate_duracion(self, data):
        if data.total_seconds() <= 0:
            raise serializers.ValidationError("La duración debe ser mayor a cero")
        return data
    
    def validate(self, data):
        plataforma = data.get('plataformas_asignadas')
        horario = data.get('horario_embarcacion')
        dias = data.get('dias_operativos')
        
        # Validación de duplicidad en la misma plataforma/horario
        existe = Viaje.objects.filter(
            plataformas_asignadas=plataforma,
            horario_embarcacion=horario,
            dias_operativos=dias
        ).exists()

        if existe:
            raise serializers.ValidationError("Ya existe un viaje usando esa plataforma, en el mismo horario y días")

        request = self.context.get('request')
        if request and hasattr(request.user, 'empleado') and not request.user.is_superuser:
            empresa = data.get('empresa')
            if empresa and empresa != request.user.empleado.empresa:
                raise serializers.ValidationError({"empresa": "No tienes permiso para asignar viajes a otra empresa."})

        return data

class EstadoViajeDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoViajeDiario
        fields = '__all__'