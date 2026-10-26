from .models import Confederacion


def confederaciones_menu(request):
    """Permite mostrar las confederaciones en todas las plantillas."""
    return {
        "confederaciones_menu": Confederacion.objects.all().order_by("nombre")
    }