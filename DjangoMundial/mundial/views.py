from django.shortcuts import render, get_object_or_404
from .models import Mundial, Seleccion, Jugador

# --- Vistas Generales ---
def inicio(request):
    return render(request, 'inicio.html')

def acerca(request):
    return render(request, 'acerca.html')

# --- Vistas de Mundial ---
def mundiales(request):
    lista_mundiales = Mundial.objects.all()
    return render(request, 'mundial/mundiales.html', {'mundiales': lista_mundiales})

def detalle_mundial(request, pk):
    mundial = get_object_or_404(Mundial, pk=pk)
    return render(request, 'mundial/detalle_mundial.html', {'mundial': mundial})

# --- Vistas de Selección ---
def selecciones(request):
    lista_selecciones = Seleccion.objects.all()
    return render(request, 'seleccion/selecciones.html', {'selecciones': lista_selecciones})

def detalle_seleccion(request, pk):
    seleccion = get_object_or_404(Seleccion, pk=pk)
    return render(request, 'seleccion/detalle_seleccion.html', {'seleccion': seleccion})

# --- Vistas de Jugador ---
def jugadores(request):
    lista_jugadores = Jugador.objects.all()
    return render(request, 'jugador/jugadores.html', {'jugadores': lista_jugadores})

def detalle_jugador(request, pk):
    jugador = get_object_or_404(Jugador, pk=pk)
    return render(request, 'jugador/detalle_jugador.html', {'jugador': jugador})