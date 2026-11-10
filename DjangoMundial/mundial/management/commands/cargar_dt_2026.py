from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mundial.models import Mundial, Seleccion, PersonalTecnico

# Directores técnicos que participaron en la Copa Mundial 2026.
# Referencia: FIFA, «Los 48 entrenadores de la Copa Mundial», 11/06/2026.
# Las claves corresponden a los nombres utilizados en MundoFútbol.
DT_2026 = {
    "Alemania": ("Julian", "Nagelsmann"),
    "Arabia Saudita": ("Georgios", "Donis"),
    "Argelia": ("Vladimir", "Petković"),
    "Argentina": ("Lionel", "Scaloni"),
    "Australia": ("Tony", "Popovic"),
    "Austria": ("Ralf", "Rangnick"),
    "Bosnia y Herzegovina": ("Sergej", "Barbarez"),
    "Brasil": ("Carlo", "Ancelotti"),
    "Bélgica": ("Rudi", "Garcia"),
    "Cabo Verde": ("Pedro Leitão", "Brito"),
    "Canadá": ("Jesse", "Marsch"),
    "Colombia": ("Néstor", "Lorenzo"),
    "Corea del Sur": ("Hong", "Myung-bo"),
    "Costa de Marfil": ("Emerse", "Faé"),
    "Croacia": ("Zlatko", "Dalić"),
    "Curazao": ("Dick", "Advocaat"),
    "Ecuador": ("Sebastián", "Beccacece"),
    "Egipto": ("Hossam", "Hassan"),
    "Escocia": ("Steve", "Clarke"),
    "España": ("Luis", "de la Fuente"),
    "Estados Unidos": ("Mauricio", "Pochettino"),
    "Francia": ("Didier", "Deschamps"),
    "Ghana": ("Carlos", "Queiroz"),
    "Haití": ("Sébastien", "Migné"),
    "Inglaterra": ("Thomas", "Tuchel"),
    "Irak": ("Graham", "Arnold"),
    "Irán": ("Amir", "Ghalenoei"),
    "Japón": ("Hajime", "Moriyasu"),
    "Jordania": ("Jamal", "Sellami"),
    "Marruecos": ("Mohamed", "Ouahbi"),
    "México": ("Javier", "Aguirre"),
    "Noruega": ("Ståle", "Solbakken"),
    "Nueva Zelanda": ("Darren", "Bazeley"),
    "Panamá": ("Thomas", "Christiansen"),
    "Paraguay": ("Gustavo", "Alfaro"),
    "Países Bajos": ("Ronald", "Koeman"),
    "Portugal": ("Roberto", "Martínez"),
    "Qatar": ("Julen", "Lopetegui"),
    "RD del Congo": ("Sébastien", "Desabre"),
    "Senegal": ("Pape", "Thiaw"),
    "Sudáfrica": ("Hugo", "Broos"),
    "Suecia": ("Graham", "Potter"),
    "Suiza": ("Murat", "Yakin"),
    "Turquía": ("Vincenzo", "Montella"),
    "Túnez": ("Sabri", "Lamouchi"),
    "Uruguay": ("Marcelo", "Bielsa"),
    "Uzbekistán": ("Fabio", "Cannavaro"),
    "Chequia": ("Miroslav", "Koubek"),
}

# Se usa solamente si tu BD utiliza el otro nombre.
ALIAS_SELECCIONES = {
    "Chequia": ("República Checa",),
    "RD del Congo": ("RD Congo", "República Democrática del Congo"),
    "Arabia Saudita": ("Arabia Saudí",),
    "Corea del Sur": ("República de Corea",),
    "Qatar": ("Catar",),
    "Países Bajos": ("Holanda",),
    "Costa de Marfil": ("Costa de Marfil",),
}


class Command(BaseCommand):
    help = "Carga los 48 directores técnicos del Mundial 2026 sin duplicar registros."

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Muestra cambios sin guardar.")

    def handle(self, *args, **options):
        mundial = Mundial.objects.filter(anio=2026).first()
        if mundial is None:
            raise CommandError("No existe el Mundial 2026 en la base de datos.")

        simular = options["simular"]
        nuevos = 0
        existentes = 0
        faltantes = []
        ambiguos = []

        with transaction.atomic():
            for pais, (nombre, apellido) in DT_2026.items():
                posibles = (pais, *ALIAS_SELECCIONES.get(pais, ()))
                selecciones = list(Seleccion.objects.filter(nombre__in=posibles))

                if not selecciones:
                    faltantes.append(pais)
                    continue
                if len(selecciones) > 1:
                    ambiguos.append(pais)
                    continue
                seleccion = selecciones[0]

                # No reemplazar información existente ni duplicar el DT de la edición.
                if PersonalTecnico.objects.filter(
                    seleccion=seleccion, mundial=mundial, funcion="DT"
                ).exists():
                    existentes += 1
                    continue

                self.stdout.write(f"{'[SIMULADO] ' if simular else ''}+ {pais}: {nombre} {apellido}")
                nuevos += 1
                if not simular:
                    # No es un pasaporte real. Solo un marcador técnico temporal
                    # porque el campo es obligatorio y unique=True en el modelo.
                    marcador = f"PENDIENTE-DT-2026-{seleccion.pk}"
                    if PersonalTecnico.objects.filter(pasaporte=marcador).exists():
                        raise CommandError(f"Identificador temporal ya utilizado: {marcador}")
                    PersonalTecnico.objects.create(
                        nombre=nombre,
                        apellido=apellido,
                        seleccion=seleccion,
                        mundial=mundial,
                        funcion="DT",
                        pasaporte=marcador,
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Nuevos: {nuevos} | Ya existentes: {existentes} | "
            f"Sin selección: {len(faltantes)} | Ambiguos: {len(ambiguos)}"
        ))
        if faltantes:
            self.stdout.write(self.style.WARNING("Selecciones no encontradas: " + ", ".join(faltantes)))
        if ambiguos:
            self.stdout.write(self.style.WARNING("Nombres ambiguos: " + ", ".join(ambiguos)))
        self.stdout.write("Los campos pasaporte PENDIENTE-DT-2026-* no contienen documentos reales.")
