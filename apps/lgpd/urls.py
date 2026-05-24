from django.urls import path
from . import views

urlpatterns = [
    path('', views.painel_lgpd, name='painel_lgpd'),
    path('exportar/', views.exportar_dados, name='exportar_dados'),
    path('excluir/', views.excluir_conta, name='excluir_conta'),
]
