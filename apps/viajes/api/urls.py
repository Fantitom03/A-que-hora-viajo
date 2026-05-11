from django.urls import include, path

app_name = 'viajes'

urlpatterns = [
    path('api/', include('apps.viajes.api.router'))
]