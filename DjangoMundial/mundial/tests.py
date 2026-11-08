from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Mundial, Seleccion, Confederacion, Jugador, HistorialJugador, ParticipacionSeleccion, PartidoGrupo
from .panel import registros_del_mundial

class AdministracionPorMundialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m2022 = Mundial.objects.create(anio=2022, nombre="Qatar 2022", sede="Qatar")
        cls.m2026 = Mundial.objects.create(anio=2026, nombre="Mundial 2026", sede="Norteamérica")
        cls.seleccion = Seleccion.objects.create(nombre="Argentina")
        cls.jugador = Jugador.objects.create(
            apellido_nombres="Jugador Prueba", pasaporte="TEST-01", edad=25,
            posicion="DEL", equipo_actual="Equipo", pais_equipo="Argentina",
            numero_camiseta=10, seleccion=cls.seleccion,
        )
        cls.historial = HistorialJugador.objects.create(mundial=cls.m2022, jugador=cls.jugador)
        cls.admin = get_user_model().objects.create_superuser(username="admin_test", email="test@example.com", password="clave-test-123")

    def test_historial_no_aparece_en_otro_mundial(self):
        self.assertEqual(registros_del_mundial(self.m2022, "jugadores").count(), 1)
        self.assertEqual(registros_del_mundial(self.m2026, "jugadores").count(), 0)

    def test_participacion_unica(self):
        ParticipacionSeleccion.objects.create(mundial=self.m2022, seleccion=self.seleccion)
        duplicado = ParticipacionSeleccion(mundial=self.m2022, seleccion=self.seleccion)
        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_partidos_no_admiten_mismo_equipo(self):
        partido = PartidoGrupo(mundial=self.m2026, grupo="Grupo A", equipo1=self.seleccion, equipo2=self.seleccion)
        with self.assertRaises(ValidationError):
            partido.full_clean()

    def test_panel_requiere_autenticacion(self):
        response = self.client.get(reverse("panel_inicio"))
        self.assertEqual(response.status_code, 302)

    def test_panel_mundial_permite_superusuario(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("panel_mundial", args=[self.m2026.pk]))
        self.assertEqual(response.status_code, 200)
