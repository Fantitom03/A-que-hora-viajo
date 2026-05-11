from rest_framework import serializers
from ..models import Terminal, Empresa, Empleado, Pasajero, Viaje

class TerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model= Terminal
        fields = ['nombre', 'cantidad_plataformas']

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta: 
        model= Empresa
        fields = ['nombre', 'ventanilla']

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
        fields = ['empresa', 'destino', 'precio', 'fecha', 'horario_embarcacion', 'duracion', 'plataformas_asignadas', 'estado', 'demora', 'motivo_demora']
        read_only_fields = ['fecha', 'estado', 'demora', 'motivo_demora']
