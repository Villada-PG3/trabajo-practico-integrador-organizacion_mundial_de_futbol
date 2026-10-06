"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mundial import views
from django.contrib.auth import views as auth_views
from mundial.views import inicio, acerca, registro_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Raíz
    path('', views.inicio, name='inicio'),
    path('acerca/', views.acerca, name='acerca'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('registro/', registro_view, name='registro'),

    # Mundial
    path('mundial/', views.mundiales, name='mundiales'),
    path('mundial/<int:pk>/', views.detalle_mundial, name='detalle_mundial'),

    # Selección
    path('seleccion/', views.selecciones, name='selecciones'),
    path('seleccion/<int:pk>/', views.detalle_seleccion, name='detalle_seleccion'),

    # Jugador
    path('jugador/', views.jugadores, name='jugadores'),
    path('jugador/<int:pk>/', views.detalle_jugador, name='detalle_jugador'),

  
]

