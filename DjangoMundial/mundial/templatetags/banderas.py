
from django import template
import unicodedata

register = template.Library()


def normalizar(nombre):
    nombre = unicodedata.normalize("NFD", str(nombre))
    nombre = "".join(
        letra for letra in nombre
        if unicodedata.category(letra) != "Mn"
    )
    return nombre.lower().strip()


CODIGOS = {
    "argentina": "ar",
    "brasil": "br",
    "francia": "fr",
    "alemania": "de",
    "espana": "es",
    "inglaterra": "gb-eng",
    "escocia": "gb-sct",
    "gales": "gb-wls",
    "portugal": "pt",
    "italia": "it",
    "paises bajos": "nl",
    "holanda": "nl",
    "belgica": "be",
    "croacia": "hr",
    "suiza": "ch",
    "dinamarca": "dk",
    "suecia": "se",
    "noruega": "no",
    "polonia": "pl",
    "austria": "at",
    "serbia": "rs",
    "ucrania": "ua",
    "republica checa": "cz",
    "chequia": "cz",
    "eslovaquia": "sk",
    "eslovenia": "si",
    "turquia": "tr",
    "bosnia y herzegovina": "ba",
    "rumania": "ro",
    "hungria": "hu",
    "grecia": "gr",
    "mexico": "mx",
    "estados unidos": "us",
    "canada": "ca",
    "costa rica": "cr",
    "panama": "pa",
    "jamaica": "jm",
    "haiti": "ht",
    "curazao": "cw",
    "curacao": "cw",
    "paraguay": "py",
    "uruguay": "uy",
    "colombia": "co",
    "ecuador": "ec",
    "peru": "pe",
    "chile": "cl",
    "bolivia": "bo",
    "venezuela": "ve",
    "japon": "jp",
    "corea del sur": "kr",
    "corea del norte": "kp",
    "china": "cn",
    "australia": "au",
    "nueva zelanda": "nz",
    "iran": "ir",
    "irak": "iq",
    "arabia saudita": "sa",
    "arabia saudí": "sa",
    "qatar": "qa",
    "catar": "qa",
    "uzbekistan": "uz",
    "jordania": "jo",
    "emiratos arabes unidos": "ae",
    "indonesia": "id",
    "senegal": "sn",
    "marruecos": "ma",
    "ghana": "gh",
    "argelia": "dz",
    "tunez": "tn",
    "egipto": "eg",
    "sudafrica": "za",
    "costa de marfil": "ci",
    "camerun": "cm",
    "nigeria": "ng",
    "rd congo": "cd",
    "rd del congo": "cd",
    "republica democratica del congo": "cd",
    "congo rd": "cd",
    "cabo verde": "cv",
    "mali": "ml",
}



@register.filter
def bandera(nombre):
    codigo = CODIGOS.get(normalizar(nombre))

    if not codigo:
        return ""

    return f"https://flagcdn.com/{codigo}.svg"

@register.simple_tag
def enlace_seleccion(nombre, anio):
    from django.urls import reverse
    from mundial.models import Seleccion

    equivalencias = {
        "republica checa": "chequia",
        "rd congo": "rd del congo",
        "republica democratica del congo": "rd del congo",
        "cote d'ivoire": "costa de marfil",
        "curacao": "curazao",
        "holanda": "paises bajos",
    }

    def nombre_normalizado(texto):
        texto = normalizar(texto)
        return equivalencias.get(texto, texto)

    nombre_buscado = nombre_normalizado(nombre)

    for seleccion in Seleccion.objects.all():
        if nombre_normalizado(seleccion.nombre) == nombre_buscado:
            url = reverse(
                "detalle_seleccion",
                args=[seleccion.pk]
            )
            return f"{url}?anio={anio}"

    return ""

