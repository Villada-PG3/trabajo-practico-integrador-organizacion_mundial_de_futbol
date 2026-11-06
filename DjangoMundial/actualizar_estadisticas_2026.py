"""Cruza estadísticas 2026 por identidad FIFA + país + fecha de nacimiento.

Uso:
 python actualizar_estadisticas_2026.py --verificar
 python actualizar_estadisticas_2026.py --aplicar      # exige los 1248
 python actualizar_estadisticas_2026.py --aplicar-parcial  # solo los seguros

No crea jugadores. Nunca modifica 2022. No reemplaza estadísticas de
jugadores que no puedan emparejarse sin ambigüedad.
"""
import argparse
import csv
import io
import os
import re
import sys
import unicodedata
from collections import defaultdict
from urllib.request import Request, urlopen

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import transaction
from mundial.models import HistorialJugador, Mundial

STILES = 'https://raw.githubusercontent.com/stiles/world-cup/main/data/processed/players.csv'
BASE = 'https://raw.githubusercontent.com/mominullptr/FIFA-World-Cup-2026-Dataset/main/'
SQUADS = BASE + 'squads_and_players.csv'
STATS = BASE + 'player_stats.csv'
TEAMS = BASE + 'teams.csv'
MATCHES = BASE + 'matches.csv'

PAISES = {
    'ALG':'argelia','ARG':'argentina','AUS':'australia','AUT':'austria',
    'BEL':'belgica','BIH':'bosnia y herzegovina','BRA':'brasil',
    'CPV':'cabo verde','CAN':'canada','COL':'colombia','COD':'rd del congo',
    'CRO':'croacia','CUW':'curazao','CZE':'chequia','CIV':'costa de marfil',
    'ECU':'ecuador','EGY':'egipto','ENG':'inglaterra','FRA':'francia',
    'GER':'alemania','GHA':'ghana','HAI':'haiti','IRN':'iran','IRQ':'irak',
    'JPN':'japon','JOR':'jordania','KOR':'corea del sur','MEX':'mexico',
    'MAR':'marruecos','NED':'paises bajos','NZL':'nueva zelanda',
    'NOR':'noruega','PAN':'panama','PAR':'paraguay','POR':'portugal',
    'QAT':'qatar','KSA':'arabia saudita','SCO':'escocia','SEN':'senegal',
    'RSA':'sudafrica','ESP':'espana','SWE':'suecia','SUI':'suiza',
    'TUN':'tunez','TUR':'turquia','USA':'estados unidos',
    'URU':'uruguay','UZB':'uzbekistan'
}
ALIASES = {
    'czechia':'chequia','republica checa':'chequia',
    'congo dr':'rd del congo','rd congo':'rd del congo',
    'republica democratica del congo':'rd del congo',
    'cote d ivoire':'costa de marfil', 'curacao':'curazao',
    'south africa':'sudafrica','south korea':'corea del sur',
    'korea republic':'corea del sur','usa':'estados unidos',
    'united states':'estados unidos','saudi arabia':'arabia saudita',
    'ir iran':'iran','morocco':'marruecos','tunisia':'tunez',
    'algeria':'argelia','egypt':'egipto','new zealand':'nueva zelanda',
    'japan':'japon','netherlands':'paises bajos',
    'switzerland':'suiza','sweden':'suecia','turkiye':'turquia',
    'turkey':'turquia','england':'inglaterra','scotland':'escocia',
    'germany':'alemania','spain':'espana','france':'francia',
    'belgium':'belgica','croatia':'croacia',
    'bosnia and herzegovina':'bosnia y herzegovina',
    'brazil':'brasil','iraq':'irak','jordan':'jordania',
    'norway':'noruega','portugal':'portugal',
    'colombia':'colombia','austria':'austria',
    'canada':'canada','qatar':'qatar','ghana':'ghana',
    'haiti':'haiti','panama':'panama','senegal':'senegal',
    'uzbekistan':'uzbekistan','ecuador':'ecuador',
    'paraguay':'paraguay','uruguay':'uruguay','mexico':'mexico',
    'australia':'australia','argentina':'argentina',
}
POS = {'0':'ARQ','1':'DEF','2':'MED','3':'DEL',
       'GK':'ARQ','DEF':'DEF','MID':'MED','FWD':'DEL'}

def normalizar(s):
    s = unicodedata.normalize('NFKD', str(s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c)).casefold()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', s).split())

def pais(s):
    s = normalizar(s)
    return ALIASES.get(s, s)

def leer(url):
    print('Leyendo:',url, flush=True)
    with urlopen(Request(url, headers={'User-Agent':'MundoFutbol/1.0'}), timeout=60) as f:
        rows = list(csv.DictReader(io.StringIO(f.read().decode('utf-8-sig'))))
    if not rows:
        raise RuntimeError('No hay datos en '+url)
    print('Registros:',len(rows))
    return rows

def entero(row, key):
    value = str(row.get(key,'')).strip()
    if not value.isdecimal():
        raise RuntimeError(f'Valor ausente o no entero: {key} en {row.get("player_name")}')
    return int(value)

def parecidos(a, b):
    a, b = normalizar(a), normalizar(b)
    if a == b: return True
    aa,bb = a.split(), b.split()
    if sorted(aa) == sorted(bb): return True
    # Orden invertido, con nombres compuestos separados o juntos
    if ''.join(sorted(aa)) == ''.join(sorted(bb)): return True
    if len(aa)>=2 and len(bb)>=2 and set(aa)&set(bb) and (set(aa)<=set(bb) or set(bb)<=set(aa)):
        return True
    return False

def procesar(modo):
    fifa = leer(STILES)
    squads = leer(SQUADS)
    stats = leer(STATS)
    teams = leer(TEAMS)
    matches = leer(MATCHES)
    if len(fifa)!=1248 or len(squads)!=1248 or len(stats)!=1248 or len(teams)!=48 or len(matches)!=104:
        raise RuntimeError('La cobertura cambió: se esperaban 1248 FIFA, 1248 planteles y estadísticas, 48 selecciones y 104 partidos. No se modificó nada.')
    if any(p.get('status','').strip().lower()!='completed' for p in matches):
        raise RuntimeError('Hay partidos no finalizados en la fuente: no se aplican estadísticas parciales.')
    mapa_equipos = {str(e['team_id']).strip(): pais(e['team_name']) for e in teams}
    if len(mapa_equipos)!=48:
        raise RuntimeError('IDs de equipos repetidos.')
    # ID de la segunda fuente -> equipo, fecha de nacimiento, nombre, posición
    fuente = {}
    for s in squads:
        sid = str(s['player_id']).strip()
        team = mapa_equipos.get(str(s['team_id']).strip())
        if not sid or sid in fuente or not team:
            raise RuntimeError('Fila de plantel duplicada o sin selección.')
        fuente[sid] = {'pais':team,'dob':s['date_of_birth'].strip()[:10],
                       'nombre':s['player_name'], 'pos':POS.get(s['position'].strip().upper())}
    # ID FIFA -> participante del plantel original, conservando la ID usada en Django.
    por_fecha = defaultdict(list)
    fifa_ids = set()
    for f in fifa:
        fid = str(f['player_id']).strip()
        team = PAISES.get(f['team_abbr'].strip().upper())
        if not fid or fid in fifa_ids or not team:
            raise RuntimeError('ID FIFA inválida o equipo no reconocido.')
        fifa_ids.add(fid)
        por_fecha[(team, f['dob'].strip()[:10])].append(f)
    mundial = Mundial.objects.get(anio=2026)
    historiales = list(HistorialJugador.objects.filter(mundial=mundial).select_related('jugador','jugador__seleccion'))
    if len(historiales)!=1248:
        raise RuntimeError(f'Se esperaban 1248 historiales, se encontraron {len(historiales)}.')
    por_fifa = defaultdict(list)
    for h in historiales:
        passport = h.jugador.pasaporte
        if passport.startswith(('Q22-FIFA-','Q26-FIFA-')):
            fid = passport.split('-')[-1]
            por_fifa[fid].append(h)
    emparejados=[]
    pendientes=[]
    usados=set()
    for stat in stats:
        sid = str(stat['player_id']).strip()
        s = fuente.get(sid)
        if not s:
            pendientes.append(('sin plantel de origen',sid,''))
            continue
        potencial = por_fecha.get((s['pais'],s['dob']),[])
        # Si comparten nacimiento, desambiguamos por nombre y posición.
        if len(potencial)>1:
            potencial = [f for f in potencial if parecidos(f['name'],s['nombre'])]
        elif len(potencial)==1:
            # Edad y país solos son suficientes solo si el nombre o posición también concuerda.
            f=potencial[0]
            if not (parecidos(f['name'], s['nombre']) or POS.get(f['position'])==s['pos']):
                potencial=[]
        if len(potencial)!=1:
            pendientes.append((s['pais'],s['nombre'],'fecha/nombre sin match único'))
            continue
        f=potencial[0]
        fid=str(f['player_id']).strip()
        db = por_fifa.get(fid,[])
        if len(db)!=1 or pais(db[0].jugador.seleccion.nombre)!=s['pais'] or db[0].pk in usados:
            pendientes.append((s['pais'],s['nombre'],'ID FIFA sin historial único'))
            continue
        valores={k:entero(stat,v) for k,v in [('partidos_jugados','matches_played'),('goles','goals'),('asistencias','assists')]}
        pj=valores['partidos_jugados']
        if pj>8 or valores['goles']>20 or valores['asistencias']>20 or (pj==0 and (valores['goles'] or valores['asistencias'])):
            raise RuntimeError('Estadística incompatible para '+s['nombre'])
        usados.add(db[0].pk)
        emparejados.append((db[0],valores))
    print('\n=== RESUMEN ===')
    print('Encontrados con seguridad:',len(emparejados),'de 1248')
    print('Pendientes:',len(pendientes))
    print('Ejemplos de pendientes (hasta 60):')
    for x in pendientes[:60]: print(' | '.join(map(str,x)))
    print('Goles coincidentes:',sum(v['goles'] for _,v in emparejados))
    print('Máximo PJ:',max((v['partidos_jugados'] for _,v in emparejados), default=0))
    print('Con PJ:',sum(v['partidos_jugados']>0 for _,v in emparejados))
    print('Primeros goleadores:')
    for h,v in sorted(emparejados,key=lambda x:x[1]['goles'],reverse=True)[:10]:
        print(h.jugador.apellido_nombres,'|',h.jugador.seleccion.nombre,'|',v)
    if modo=='verificar':
        print('VERIFICACIÓN: no se escribió nada.')
        return
    if modo=='aplicar' and len(emparejados)!=1248:
        raise RuntimeError('Faltan coincidencias. No se modificó nada. Usá --aplicar-parcial para guardar SOLO los emparejados con seguridad.')
    if not emparejados:
        raise RuntimeError('No hay coincidencias seguras, no se aplicó nada.')
    with transaction.atomic():
        for h,v in emparejados:
            h.partidos_jugados=v['partidos_jugados']
            h.goles=v['goles']
            h.asistencias=v['asistencias']
        HistorialJugador.objects.bulk_update([h for h,_ in emparejados], ['partidos_jugados','goles','asistencias'],batch_size=300)
    print('GUARDADOS:',len(emparejados),'historiales de 2026; NO se tocaron otros años.')
    if pendientes: print('ATENCIÓN:',len(pendientes),'historiales pendientes conservan sus valores anteriores y deben revisarse.')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--verificar',action='store_true')
    g.add_argument('--aplicar',action='store_true')
    g.add_argument('--aplicar-parcial',action='store_true')
    a=p.parse_args()
    try:
        procesar('verificar' if a.verificar else 'aplicar-parcial' if a.aplicar_parcial else 'aplicar')
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
