from django.urls import path

from . import views

urlpatterns = [
    path('confederaciones/', views.lista_confederaciones, name='lista_confederaciones'),
    path('confederaciones/<int:pk>/', views.detalle_confederacion, name='detalle_confederacion'),

    # Selecciones
    path('selecciones/', views.selecciones, name='selecciones'),
    path('selecciones/<int:pk>/', views.detalle_seleccion, name='detalle_seleccion'),
]
