
from django.db import migrations


def asociar_datos_existentes(apps, schema_editor):
    Mundial = apps.get_model("mundial", "Mundial")
    Historial = apps.get_model("mundial", "HistorialJugador")
    Participacion = apps.get_model("mundial", "ParticipacionSeleccion")
    Partido2022 = apps.get_model("mundial", "PartidoMundial2022")
    Tecnico = apps.get_model("mundial", "PersonalTecnico")

    # Asociar selecciones según sus jugadores.
    parejas = Historial.objects.exclude(
        jugador__seleccion__isnull=True
    ).values_list(
        "mundial_id", "jugador__seleccion_id"
    ).distinct()

    for mundial_id, seleccion_id in parejas.iterator():
        Participacion.objects.get_or_create(
            mundial_id=mundial_id,
            seleccion_id=seleccion_id
        )

    # Asociar las selecciones de los partidos históricos.
    qatar = Mundial.objects.filter(anio=2022).first()

    if qatar:
        partidos = Partido2022.objects.filter(
            mundial=qatar
        ).values_list("equipo1_id", "equipo2_id")

        for equipo1_id, equipo2_id in partidos.iterator():
            for seleccion_id in (equipo1_id, equipo2_id):
                if seleccion_id:
                    Participacion.objects.get_or_create(
                        mundial=qatar,
                        seleccion_id=seleccion_id
                    )

    # Conservar los dorsales originales en cada historial.
    historiales = Historial.objects.select_related(
        "jugador"
    ).filter(numero_camiseta_mundial__isnull=True)

    for historial in historiales.iterator():
        historial.numero_camiseta_mundial = (
            historial.jugador.numero_camiseta
        )
        historial.save(
            update_fields=["numero_camiseta_mundial"]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("mundial", "0005_historialjugador_numero_camiseta_mundial_and_more"),
    ]

    operations = [
        migrations.RunPython(
            asociar_datos_existentes,
            migrations.RunPython.noop
        ),
    ]
