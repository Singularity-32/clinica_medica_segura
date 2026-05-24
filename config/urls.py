from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.autenticacao.urls')),
    path('recuperacao/', include('apps.recuperacao.urls')),
    path('lgpd/', include('apps.lgpd.urls')),
    path('agendamento/', include('apps.agendamento.urls')),
    path('', include('apps.autenticacao.urls')),  # raiz → login
]
