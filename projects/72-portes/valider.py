#!/usr/bin/env python3
"""Validation croisée sans dépendance des trois CSV canoniques 72 portes v1.1.1."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CYCLES = ('I', 'II', 'III', 'IV', 'V', 'VI')

def charger(nom):
    with (ROOT / nom).open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=';')
        assert reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), f'colonnes invalides : {nom}'
        rows = list(reader)
    assert all(None not in row and None not in row.values() for row in rows), f'ligne mal formée : {nom}'
    return rows

def verifier():
    manifest = json.loads((ROOT / 'empreintes.json').read_text(encoding='utf-8'))
    for nom, data in manifest['files'].items():
        raw = (ROOT / nom).read_bytes()
        assert len(raw) == data['bytes'], f'longueur différente : {nom}'
        assert hashlib.sha256(raw).hexdigest() == data['sha256'], f'empreinte différente : {nom}'
    axes, portes, transitions = (charger(n) for n in ('axes.csv','portes.csv','transitions.csv'))
    assert (len(axes),len(portes),len(transitions)) == (9,72,71)
    assert sorted(int(p['n']) for p in portes) == list(range(1,73))
    assert sorted(int(p['position_chemin']) for p in portes) == list(range(1,73))
    assert sorted(int(t['position']) for t in transitions) == list(range(1,72))
    assert {t['id'] for t in transitions} == {f'T{i}' for i in range(1,72)}
    assert {a['id'] for a in axes} == {f'AX{i}' for i in range(1,10)}
    assert Counter(a['type'] for a in axes) == {'Polaire':2,'Dynamique':7}
    assert {p['famille'] for p in portes} == {f'F{i}' for i in range(1,17)}
    assert Counter(p['pivot'] for p in portes) == {'':60,'★':12}
    assert Counter(p['cycle'] for p in portes) == dict.fromkeys(CYCLES,12)
    assert Counter(t['cycle'] for t in transitions) == {'I':11,**dict.fromkeys(CYCLES[1:],12)}
    chemin = sorted(portes,key=lambda p:int(p['position_chemin']))
    par_id = {int(p['n']):p for p in portes}
    assert chemin[0]['nom'] == 'Source' and chemin[-1]['nom'] == 'Repos'
    assert chemin[0]['transition_entrante'] == '' and chemin[-1]['transition_sortante'] == ''
    assert all(p['transition_entrante'] and p['transition_sortante'] for p in chemin[1:-1])
    for pos, transition in enumerate(sorted(transitions,key=lambda t:int(t['position'])),start=1):
        avant, apres = chemin[pos-1:pos+1]
        assert transition['id'] == f'T{pos}'
        assert (transition['de_n'],transition['de_nom']) == (avant['n'],avant['nom'])
        assert (transition['vers_n'],transition['vers_nom']) == (apres['n'],apres['nom'])
        assert avant['transition_sortante'] == transition['id'] == apres['transition_entrante']
        assert transition['cycle'] == apres['cycle']
    for pos,p in enumerate(chemin,start=1):
        assert p['cycle'] == CYCLES[(pos-1)//12]
    membres=Counter()
    for axe in axes:
        for prefix in ('pole_1','pole_2'):
            porte = par_id[int(axe[f'{prefix}_n'])]
            assert (porte['nom'],porte['axe'],porte['type_axe']) == (axe[f'{prefix}_nom'],axe['id'],axe['type'])
            membres[porte['n']] += 1
    assert len(membres)==18 and all(v==1 for v in membres.values())
    for p in portes:
        assert bool(p['axe'])==bool(p['type_axe'])
        assert bool(p['axe']) == (p['n'] in membres)
    assert (par_id[25]['nom'],par_id[25]['position_chemin'],par_id[25]['cycle']) == ('Argile','24','II')
    assert (par_id[24]['nom'],par_id[24]['position_chemin'],par_id[24]['cycle']) == ('Sable','25','III')
    for pos,noms in [(24,('Argile','Sable')),(42,('Nuée','Pluie')),(62,('Serrure','Clé')),(12,('Feu','Miroir')),(60,('Étoile','Porte'))]:
        assert (chemin[pos-1]['nom'],chemin[pos]['nom']) == noms
    return {'statut':'PASS','portes':72,'transitions':71,'familles':16,'axes':9,'pivots':12,'cycles':{c:12 for c in CYCLES},'fichiers_sha256':'VALIDES'}

if __name__ == '__main__':
    print(json.dumps(verifier(),ensure_ascii=False))
