from django.shortcuts import render, get_object_or_404, redirect 
from .models import Mundial, Seleccion, Jugador
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

# --- Vistas Generales ---
def inicio(request):
    # Obtenemos los últimos 3 mundiales ordenados por año descendente
    ultimos_mundiales = Mundial.objects.all().order_by('-anio')[:3]
    
    return render(request, 'inicio.html', {
        'ultimos_mundiales': ultimos_mundiales
    })

def acerca(request):
    return render(request, 'acerca.html')

@staff_member_required
def crear_mundial(request):
    # Esta vista solo la podrá abrir un usuario que sea Administrador/Staff
    if request.method == 'POST':
        # Procesar formulario...
        pass
    return render(request, 'mundial/crear_mundial.html')
def registro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada con éxito! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})

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