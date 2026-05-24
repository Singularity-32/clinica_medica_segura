from django.urls import path
from . import views

urlpatterns = [
    path('novo/', views.novo_agendamento, name='novo_agendamento'),
    path('cancelar/<int:pk>/', views.cancelar_agendamento, name='cancelar_agendamento'),
]
