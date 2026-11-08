from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("mundial", "0013_panel_por_mundial")]

    operations = [
        migrations.AddField(
            model_name="partidogrupo", name="jugado",
            field=models.BooleanField(default=False, verbose_name="Partido disputado", help_text="Activar cuando el resultado sea definitivo; permite distinguir 0-0 de un partido pendiente."),
        ),
        migrations.CreateModel(
            name="EventoGrupo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(max_length=20, choices=[("GOL", "Gol"), ("PENAL", "Gol de penal"), ("AUTOGOL", "Gol en contra"), ("AMARILLA", "Tarjeta amarilla"), ("ROJA", "Tarjeta roja"), ("DOBLE_AMARILLA", "Expulsión por doble amarilla"), ("CAMBIO", "Cambio de jugador"), ("FALTA", "Falta"), ("INICIO", "Inicio del partido"), ("DESCANSO", "Descanso"), ("FINAL", "Final del partido")])),
                ("minuto", models.CharField(max_length=10, help_text="Ejemplo: 34 o 45+2")),
                ("equipo", models.CharField(max_length=100, blank=True)),
                ("jugador", models.CharField(max_length=150, blank=True)),
                ("jugador_entra", models.CharField(max_length=150, blank=True)),
                ("jugador_sale", models.CharField(max_length=150, blank=True)),
                ("descripcion", models.TextField(blank=True)),
                ("partido_grupo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, null=True, blank=True, related_name="eventos_grupo", to="mundial.partidogrupo", verbose_name="Partido de grupos")),
                ("partido_qatar", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, null=True, blank=True, related_name="eventos_grupo", to="mundial.partidomundial2022", verbose_name="Partido histórico Qatar 2022")),
            ],
            options={"verbose_name": "Evento de partido de grupos", "verbose_name_plural": "Eventos de partidos de grupos", "ordering": ["pk"]},
        ),
    ]
