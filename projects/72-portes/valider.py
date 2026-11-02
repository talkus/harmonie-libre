#!/usr/bin/env python3
"""Contrôle déterministe des trois tables canoniques 72 portes v1.1.1."""
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
        lecteur = csv.DictReader(handle, delimiter=';')
        assert lecteur.fieldnames and len(lecteur.fieldnames) == len(set(lecteur.fieldnames)), nom
        lignes = list(lecteur)
    assert all(set(ligne) == set(lecteur.fieldnames) for ligne in lignes), nom
    assert all(None not in ligne and None not in ligne.values() for ligne in lignes), nom
    return lignes


def verifier():
    manifeste = json.loads((ROOT / 'empreintes.json').read_text(encoding='utf-8'))
    assert manifeste['version'] == '1.1.1'
    assert set(manifeste['files']) == {'axes.csv', 'portes.csv', 'transitions.csv'}
    for nom, trace in manifeste['files'].items():
        octets = (ROOT / nom).read_bytes()
        assert len(octets) == trace['bytes'], f'{nom} : taille modifiée'
        assert hashlib.sha256(octets).hexdigest() == trace['sha256'], f'{nom} : SHA-256 modifié'

    axes = charger('axes.csv')
    portes = charger('portes.csv')
    transitions = charger('transitions.csv')
    assert (len(axes), len(portes), len(transitions)) == (9, 72, 71)
    assert sorted(int(p['n']) for p in portes) == list(range(1, 73))
    assert sorted(int(p['position_chemin']) for p in portes) == list(range(1, 73))
    assert sorted(int(t['position']) for t in transitions) == list(range(1, 72))
    assert {t['id'] for t in transitions} == {f'T{i}' for i in range(1, 72)}
    assert {a['id'] for a in axes} == {f'AX{i}' for i in range(1, 10)}
    assert Counter(a['type'] for a in axes) == {'Polaire': 2, 'Dynamique': 7}
    assert {p['famille'] for p in portes} == {f'F{i}' for i in range(1, 17)}
    assert Counter(p['pivot'] for p in portes) == {'': 60, '★': 12}
    assert Counter(p['cycle'] for p in portes) == dict.fromkeys(CYCLES, 12)
    assert Counter(t['cycle'] for t in transitions) == {'I': 11, **dict.fromkeys(CYCLES[1:], 12)}

    par_id = {int(p['n']): p for p in portes}
    chemin = sorted(portes, key=lambda p: int(p['position_chemin']))
    assert chemin[0]['nom'] == 'Source' and chemin[-1]['nom'] == 'Repos'
    assert chemin[0]['transition_entrante'] == ''
    assert chemin[-1]['transition_sortante'] == ''
    assert all(p['transition_entrante'] and p['transition_sortante'] for p in chemin[1:-1])

    for position, t in enumerate(sorted(transitions, key=lambda t: int(t['position'])), 1):
        avant, apres = chemin[position - 1:position + 1]
        assert t['id'] == f'T{position}'
        assert (t['de_n'], t['de_nom']) == (avant['n'], avant['nom'])
        assert (t['vers_n'], t['vers_nom']) == (apres['n'], apres['nom'])
        assert avant['transition_sortante'] == t['id'] == apres['transition_entrante']
        assert t['cycle'] == apres['cycle']

    for position, p in enumerate(chemin, 1):
        assert p['cycle'] == CYCLES[(position - 1) // 12]

    membres = Counter()
    for axe in axes:
        for prefixe in ('pole_1', 'pole_2'):
            porte = par_id[int(axe[f'{prefixe}_n'])]
            assert porte['nom'] == axe[f'{prefixe}_nom']
            assert porte['axe'] == axe['id']
            assert porte['type_axe'] == axe['type']
            membres[porte['n']] += 1
    assert len(membres) == 18 and all(nombre == 1 for nombre in membres.values())
    for porte in portes:
        assert bool(porte['axe']) == bool(porte['type_axe'])
        if not porte['axe']:
            assert porte['n'] not in membres

    assert (par_id[25]['nom'], par_id[25]['position_chemin'], par_id[25]['cycle']) == ('Argile', '24', 'II')
    assert (par_id[24]['nom'], par_id[24]['position_chemin'], par_id[24]['cycle']) == ('Sable', '25', 'III')
    assert chemin[23]['nom'] == 'Argile' and chemin[24]['nom'] == 'Sable'
    assert chemin[41]['nom'] == 'Nuée' and chemin[42]['nom'] == 'Pluie'
    assert chemin[61]['nom'] == 'Serrure' and chemin[62]['nom'] == 'Clé'
    assert chemin[11]['nom'] == 'Feu' and chemin[12]['nom'] == 'Miroir'
    assert chemin[59]['nom'] == 'Étoile' and chemin[60]['nom'] == 'Porte'
    print(json.dumps({'statut': 'PASS', 'portes': 72, 'transitions': 71,
                      'familles': 16, 'pivots': 12, 'axes': 9,
                      'cycles': dict(Counter(p['cycle'] for p in portes)),
                      'octets_sha256': 'PASS'}, ensure_ascii=False))


if __name__ == '__main__':
    verifier()
