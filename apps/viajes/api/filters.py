from django_filters import rest_framework as filters
from ..models import Viaje, Empresa

class ViajeFilter(filters.FilterSet):
    
    empresa = filters.CharFilter(field_name='empresa__nombre', lookup_expr='icontains')

    estado = filters.CharFilter(lookup_expr='iexact')

    horario_desde = filters.TimeFilter(field_name='horario_embarcacion', lookup_expr='gte')

    horario_hasta = filters.TimeFilter(field_name='horario_embarcacion', lookup_expr='lte')

    destino = filters.CharFilter(field_name='paradas__ubicacion__nombre_oficial', lookup_expr='icontains')

    dia = filters.CharFilter(method='filtrar_por_dia')

    plataforma = filters.NumberFilter(method='filtrar_por_plataforma')

    class Meta:
        model = Viaje
        fields = []

    def filtrar_por_dia(self, queryset, name, value):
        return queryset.filter(dias_operativos__contains=[value.upper()])
    
    def filtrar_por_plataforma(self, queryset, name, value):
        return queryset.filter(plataformas_asignadas__contains=[value])
    

class EmpresaFilter(filters.FilterSet):
    
    nombre = filters.CharFilter(lookup_expr='icontains')

    terminal = filters.CharFilter(field_name='terminal__nombre', lookup_expr='icontains')

    class Meta:
        model = Empresa
        fields = []