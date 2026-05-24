from django.urls import path
from . import views

urlpatterns = [
    path('', views.solicitar_recuperacao, name='solicitar_recuperacao'),
    path('resetar/<str:token>/', views.resetar_senha, name='resetar_senha'),
]
