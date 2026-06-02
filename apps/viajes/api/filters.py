from django_filters import rest_framework as filters
from ..models import Viaje, Empresa

class ViajeFilter(filters.FilterSet):
    
    empresa = filters.CharFilter(field_name='empresa__nombre', lookup_expr='icontains')

    estado = filters.CharFilter(method='filtrar_por_estado')

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
    
    def filtrar_por_estado(self, queryset, name, value):
        from datetime import date, datetime
        from django.db.models import Q

        fecha_str = self.request.query_params.get('fecha')
        if fecha_str:
            try:
                fecha_consulta = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                fecha_consulta = date.today()
        else:
            fecha_consulta = date.today()

        if value.upper() in ['A_TIEMPO', 'PROGRAMADO']:
            return queryset.filter(
                Q(estados_diarios__fecha=fecha_consulta, estados_diarios__estado__in=['A_TIEMPO', 'PROGRAMADO']) |
                ~Q(estados_diarios__fecha=fecha_consulta)
            ).distinct()
        else:
            return queryset.filter(
                estados_diarios__fecha=fecha_consulta, 
                estados_diarios__estado=value.upper()
            ).distinct()
    

class EmpresaFilter(filters.FilterSet):
    
    nombre = filters.CharFilter(lookup_expr='icontains')

    terminal = filters.CharFilter(field_name='terminal__nombre', lookup_expr='icontains')

    class Meta:
        model = Empresa
        fields = []