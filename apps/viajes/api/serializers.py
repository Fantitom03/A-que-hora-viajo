from rest_framework import serializers
from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje, Parada, Ubicacion

class TerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model= Terminal
        fields = ['nombre', 'cantidad_plataformas']

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta: 
        model= Empresa
        fields = ['nombre', 'ventanilla', 'terminal']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['terminal'] = {
            'nombre_terminal' : instance.terminal.nombre
        }

        return representation

    def validate_ventanilla(self,data):
        if data <= 0:
            raise serializers.ValidationError("El número de ventanilla debe ser mayor a 0")
        return data
    
    def validate(self, data):
        terminal = data.get('terminal')
        ventanilla = data.get('ventanilla')

        existe = Empresa.objects.filter(
            terminal = terminal,
            ventanilla = ventanilla
        ).exists()

        if existe:
            raise serializers.ValidationError("Ya existe una empresa usando esa ventanilla en esta terminal")

        return data

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Empleado
        fields = ['usuario', 'empresa', 'rol']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['usuario'] = {
            'username' : instance.usuario.username,
            'dni' : instance.usuario.dni
        }

        representation['empresa'] = {
            'nombre empresa' : instance.empresa.nombre
        }

        return representation

class PasajeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pasajero
        fields = ['usuario', 'telefono']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['usuario'] = {
            'username' : instance.usuario.username,
            'dni' : instance.usuario.dni
        }

        return representation
    
class ViajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viaje
        fields = ['empresa', 'dias_operativos', 'horario_embarcacion', 'duracion', 'plataformas_asignadas', 'estado', 'demora', 'motivo_demora']
        read_only_fields = ['estado', 'demora', 'motivo_demora']


        def validate_dias_operativos(self, data):
            dias_validos = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']

            dias = [d.strip() for d in data.split(',')]

            for dia in dias:
                if dia not in dias_validos:
                    raise serializers.ValidationError(f"{dia} no es un dia valido")
            
            return data
        
        def validate_duracion(sefl,data):
            if data.total_seconds() <= 0:
                raise serializers.ValidationError("La duracion debe ser mayor a cero")
            
            return data
       
        def validate(self,data):
            plataforma = data.get('plataformas_asignadas')
            horario = data.get('horario_embarcacion')
            dias = data.get('dias_operativos')

            existe = Viaje.objects.filter(
                plataformas_asignadas = plataforma,
                horario_embarcacion = horario,
                dias_operativos = dias
            ).exists()

            if existe:
                raise serializers.ValidationError("Ya existe un viaje usando esa plataforma, en el mismo horario y día")
            
            return data


class ParadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parada
        fields = ['viaje', 'ubicacion', 'orden', 'tiempo_desde_salida', 'precio']

    def validate_orden(self,data):
        if data <= 0:
            raise serializers.ValidationError("El orden debe ser mayor a 0")
        
        return data

    def validate_precio(self, data):
        if data <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")

        return data
    
    def validate_tiempo_desde_salida(self,data):
        if data.total_seconds() < 0:
            raise serializers.ValidationError("El tiempo no puede ser negativo")
        
        return data
    
    def validate(self, data):
        existe = Parada.objects.filter(
            viaje=data['viaje'],
            orden=data['orden']
        ).exists()

        if existe:
            raise serializers.ValidationError("Ya existe una parada con ese orden en el viaje")
        
        return data

    def validate(self, data):
        existe = Parada.objects.filter(
            viaje=data['viaje'],
            ubicacion=data['ubicacion']
        ).exists()

        if existe:
            raise serializers.ValidationError("La ubicacion ya existe en este viaje")
        
        return data

class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = ['nombre_oficial', 'latitud', 'longitud']

    def validate_latitud(self,data):
        if data < -90 or data > 90:
            raise serializers.ValidationError("Latitud invalida")
        
        return data
    
    def validate_longitud(seld,data):
        if data < -180 or data > 180:
            raise serializers.ValidationError("Longitud invalida")
        
        return data