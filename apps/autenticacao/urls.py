from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('logout/', views.logout_view, name='logout'),
    path('verificar-2fa/', views.verificar_2fa, name='verificar_2fa'),
    path('configurar-2fa/', views.configurar_2fa, name='configurar_2fa'),
    path('painel/', views.painel, name='painel'),
]
