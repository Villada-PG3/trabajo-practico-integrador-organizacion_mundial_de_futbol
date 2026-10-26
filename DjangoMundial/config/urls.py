"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path
from mundial import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # Administración
    path('admin/', admin.site.urls),

    # Páginas principales
    path('', views.inicio, name='inicio'),
    path('acerca/', views.acerca, name='acerca'),

    # Autenticación
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='inicio'
        ),
        name='logout'
    ),

    path(
        'registro/',
        views.registro_view,
        name='registro'
    ),

    # Mundiales
    path(
        'mundial/',
        views.MundialListView.as_view(),
        name='mundiales'
    ),

    path(
        'mundial/<int:pk>/',
        views.detalle_mundial,
        name='detalle_mundial'
    ),

    # Confederaciones
    path(
        'confederaciones/',
        views.selecciones,
        name='lista_confederaciones'
    ),

    path(
        'confederaciones/<int:pk>/',
        views.detalle_confederacion,
        name='detalle_confederacion'
    ),

    # Selecciones
    path(
        'seleccion/',
        views.selecciones,
        name='selecciones'
    ),

    path(
        'seleccion/<int:pk>/',
        views.detalle_seleccion,
        name='detalle_seleccion'
    ),

    # Jugadores - Sin modificaciones
    path(
        'jugador/',
        views.jugadores,
        name='jugadores'
    ),

    path(
        'jugador/<int:pk>/',
        views.detalle_jugador,
        name='detalle_jugador'
    ),

    # Detalle de partido
    path(
        'partido/<int:partido_id>/',
        views.detalle_partido,
        name='detalle_partido'
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )