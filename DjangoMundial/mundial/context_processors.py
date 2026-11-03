from .models import Seleccion


def confederaciones_menu(request):
    confederaciones = (
        Seleccion.objects
        .values_list('confederacion', flat=True)
        .distinct()
        .order_by('confederacion')
    )

    return {
        'confederaciones_menu': confederaciones
    }