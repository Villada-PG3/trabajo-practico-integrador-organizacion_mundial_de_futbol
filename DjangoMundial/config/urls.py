
"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path
from mundial import views, panel
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # Administración tradicional
    path(
        'admin/',
        admin.site.urls
    ),

    # ======================================
    # NUEVO PANEL DE ADMINISTRACIÓN
    # ======================================

    path(
        'panel/',
        panel.inicio_panel,
        name='panel_inicio'
    ),

    path(
        'panel/<slug:seccion>/nuevo/',
        panel.formulario_registro,
        name='panel_nuevo'
    ),

    path(
        'panel/<slug:seccion>/<int:pk>/editar/',
        panel.formulario_registro,
        name='panel_editar'
    ),

    path(
        'panel/<slug:seccion>/<int:pk>/eliminar/',
        panel.eliminar_registro,
        name='panel_eliminar'
    ),

    path(
        'panel/<slug:seccion>/',
        panel.listar_registros,
        name='panel_listado'
    ),

    
# ==========================================
# PANEL POR MUNDIAL
# ==========================================

path(
    'panel/mundial/<int:mundial_id>/',
    panel.administrar_mundial,
    name='panel_mundial'
),

path(
    'panel/mundial/<int:mundial_id>/<slug:seccion>/nuevo/',
    panel.formulario_mundial,
    name='panel_mundial_nuevo'
),

path(
    'panel/mundial/<int:mundial_id>/<slug:seccion>/<int:pk>/editar/',
    panel.formulario_mundial,
    name='panel_mundial_editar'
),

path(
    'panel/mundial/<int:mundial_id>/<slug:seccion>/<int:pk>/eliminar/',
    panel.eliminar_mundial_registro,
    name='panel_mundial_eliminar'
),

path(
    'panel/mundial/<int:mundial_id>/<slug:seccion>/',
    panel.listado_mundial,
    name='panel_mundial_listado'
),


    # ======================================
    # PÁGINAS PRINCIPALES
    # ======================================

    path(
        '',
        views.inicio,
        name='inicio'
    ),

    path(
        'acerca/',
        views.acerca,
        name='acerca'
    ),

    # ======================================
    # AUTENTICACIÓN
    # ======================================

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

    # ======================================
    # MUNDIALES
    # ======================================

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

    # ======================================
    # CONFEDERACIONES
    # ======================================

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

    # ======================================
    # SELECCIONES
    # ======================================

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

    # ======================================
    # JUGADORES
    # ======================================

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

    # ======================================
    # DETALLE DE PARTIDO
    # ======================================

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
