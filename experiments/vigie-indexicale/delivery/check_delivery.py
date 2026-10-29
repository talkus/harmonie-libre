#!/usr/bin/env python3
"""Vigie Indexicale: byte-for-byte provenance between a private source ZIP and a
Netlify publication ZIP. Non-authorizing, non-authenticating, no network/credentials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import PurePosixPath, Path

PUBLIC = (
    '_headers', 'anchor-core.mjs', 'ancrage.html', 'ancrage.mjs',
    'app.js', 'core.mjs', 'index.html', 'styles.css',
)
REQUIRED_SOURCE = ('web/src/core.mjs', 'web/src/anchor.mjs',
                   'web/tests/indexical.test.mjs', 'git_witness/witness/verify.mjs')
H64 = re.compile(r'^[a-f0-9]{64}$')
MAX_FILES = 500
MAX_MEMBER = 32_000_000
MAX_TOTAL = 80_000_000

class GuardFailure(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _valid_path(name: str) -> bool:
    path = PurePosixPath(name)
    return (bool(name) and not name.startswith('/') and '\\' not in name
            and ':' not in name and not any(p in ('', '.', '..') for p in name.rstrip('/').split('/'))
            and not path.is_absolute())

def _open_zip(archive: bytes):
    if not isinstance(archive, bytes):
        raise GuardFailure('OCTETS_ARCHIVE_ABSENTS')
    import io
    try:
        z = zipfile.ZipFile(io.BytesIO(archive))
    except (zipfile.BadZipFile, ValueError):
        raise GuardFailure('ZIP_INVALIDE') from None
    infos = z.infolist()
    if not infos or len(infos) > MAX_FILES:
        z.close(); raise GuardFailure('ZIP_NOMBRE_ENTREES')
    names, total = set(), 0
    for info in infos:
        name = info.filename
        if not _valid_path(name) or name in names:
            z.close(); raise GuardFailure('ZIP_CHEMIN_OU_DOUBLON')
        names.add(name)
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            z.close(); raise GuardFailure('ZIP_LIEN_SYMBOLIQUE')
        if info.file_size > MAX_MEMBER:
            z.close(); raise GuardFailure('ZIP_TAILLE_ENTREE')
        total += info.file_size
        if total > MAX_TOTAL:
            z.close(); raise GuardFailure('ZIP_TAILLE_TOTALE')
    try:
        bad = z.testzip()
    except (zipfile.BadZipFile, EOFError, RuntimeError, OSError):
        bad = True
    if bad:
        z.close(); raise GuardFailure('ZIP_CRC_INVALIDE')
    return z

def verify_delivery(source_bytes: bytes, public_bytes: bytes,
                    *, expected_source_sha: str, expected_public_sha: str) -> dict:
    """Checks locally supplied bytes, not authenticity of their provider/identity."""
    baseline = dict(ok=False, epistemic='E0', authentication='NOT_ESTABLISHED',
                    deployState='NOT_ASSESSED', browserExecution='NOT_TESTED',
                    authorization='NOT_ASSESSED', canon='NOT_ADOPTED', modelAuthority='none')
    try:
        if not H64.fullmatch(str(expected_source_sha)) or not H64.fullmatch(str(expected_public_sha)):
            raise GuardFailure('PINS_INVALIDES')
        source_hash, public_hash = sha256(source_bytes), sha256(public_bytes)
        if source_hash != expected_source_sha:
            raise GuardFailure('SOURCE_EMPREINTE_DIFFERENTE')
        if public_hash != expected_public_sha:
            raise GuardFailure('DEPLOIEMENT_ARCHIVE_EMPREINTE_DIFFERENTE')
        with _open_zip(source_bytes) as src, _open_zip(public_bytes) as pub:
            srcnames = set(src.namelist())
            pubnames = set(pub.namelist())
            if any(name not in srcnames for name in REQUIRED_SOURCE):
                raise GuardFailure('ARCHIVE_SOURCE_INCOMPLETE')
            if pubnames != set(PUBLIC):
                raise GuardFailure('PUBLICATION_FICHIERS_MANQUANTS_OU_SUPPLEMENTAIRES')
            observed = {}
            for name in PUBLIC:
                source_name = 'web/public/' + name
                if source_name not in srcnames:
                    raise GuardFailure('SOURCE_PUBLIQUE_MANQUANTE')
                lhs, rhs = src.read(source_name), pub.read(name)
                if lhs != rhs:
                    raise GuardFailure('OCTETS_PUBLIES_NON_LIES_A_SOURCE:' + name)
                observed[name] = dict(sha256=sha256(rhs), bytes=len(rhs))
            if src.read('web/src/core.mjs') != src.read('web/public/core.mjs'):
                raise GuardFailure('MOTEUR_SOURCE_PUBLIE_DIFFERENT')
            if src.read('web/src/anchor.mjs') != src.read('web/public/anchor-core.mjs'):
                raise GuardFailure('ANCRAGE_SOURCE_PUBLIE_DIFFERENT')
        return dict(baseline, ok=True, code='LIVRABLES_OCTET_A_OCTET_CONCORDANTS_NON_AUTHENTIFIANTS',
                    sourceSha256=source_hash, deployPackageSha256=public_hash,
                    fileCount=len(PUBLIC), assets=observed)
    except GuardFailure as error:
        return dict(baseline, code=error.code)
    except (TypeError, AttributeError, zipfile.BadZipFile, KeyError, OSError, EOFError, RuntimeError) as error:
        return dict(baseline, code='ARCHIVES_ILLISIBLES', errorType=type(error).__name__)

def main(argv=None):
    parser=argparse.ArgumentParser(description='Vigie v0.8 — provenance des octets entre ZIP source et ZIP Netlify')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--public', type=Path, required=True)
    parser.add_argument('--expected-source-sha', required=True)
    parser.add_argument('--expected-public-sha', required=True)
    args=parser.parse_args(argv)
    try:
        result=verify_delivery(args.source.read_bytes(), args.public.read_bytes(),
            expected_source_sha=args.expected_source_sha, expected_public_sha=args.expected_public_sha)
    except OSError:
        result={'ok':False,'code':'FICHIERS_INDISPONIBLES','authorization':'NOT_ASSESSED','epistemic':'E0'}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result['ok'] else 1

if __name__=='__main__':
    sys.exit(main())
