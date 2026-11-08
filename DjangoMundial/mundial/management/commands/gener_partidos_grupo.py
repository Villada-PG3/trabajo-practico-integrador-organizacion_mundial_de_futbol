from itertools import combinations
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mundial.models import Mundial, PosicionGrupo, PartidoGrupo, Seleccion

class Command(BaseCommand):
    help = "Crea partidos pendientes para cada grupo sin inventar resultados ni fechas."

    def add_arguments(self, parser):
        parser.add_argument("anio", type=int, help="Año del Mundial, por ejemplo 2026")

    def handle(self, *args, **options):
        anio = options["anio"]
        try:
            mundial = Mundial.objects.get(anio=anio)
        except Mundial.DoesNotExist:
            raise CommandError(f"No existe un Mundial correspondiente al año {anio}.")
        if anio == 2022:
            raise CommandError("Qatar 2022 ya tiene sus partidos históricos; no generes duplicados.")
        grupos = {}
        for pos in PosicionGrupo.objects.filter(mundial=mundial).order_by("grupo", "pk"):
            grupos.setdefault(pos.grupo, []).append(pos.equipo)
        total = 0
        with transaction.atomic():
            for grupo, nombres in grupos.items():
                if PartidoGrupo.objects.filter(mundial=mundial, grupo=grupo).exists():
                    self.stdout.write(f"{grupo}: ya tiene partidos; se omite para evitar duplicados.")
                    continue
                if len(nombres) < 2:
                    self.stdout.write(f"{grupo}: menos de dos equipos; se omite.")
                    continue
                selecciones = list(Seleccion.objects.filter(nombre__in=nombres))
                if len(selecciones) != len(set(nombres)):
                    disponibles = {s.nombre for s in selecciones}
                    self.stdout.write(self.style.WARNING(f"{grupo}: faltan selecciones: {set(nombres) - disponibles}. Se omite."))
                    continue
                por_nombre = {s.nombre: s for s in selecciones}
                ordenadas = [por_nombre[n] for n in nombres]
                nuevos = [PartidoGrupo(mundial=mundial, grupo=grupo, equipo1=a, equipo2=b, jugado=False)
                          for a, b in combinations(ordenadas, 2)]
                PartidoGrupo.objects.bulk_create(nuevos)
                total += len(nuevos)
                self.stdout.write(f"{grupo}: {len(nuevos)} cruces pendientes creados.")
        self.stdout.write(self.style.SUCCESS(f"Listo: {total} partidos pendientes nuevos, sin resultados inventados."))
