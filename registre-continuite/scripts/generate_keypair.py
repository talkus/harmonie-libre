#!/usr/bin/env python3
"""generate_keypair.py — Genere une paire de cles Ed25519 et affiche les informations
necessaires pour l enregistrement dans le registre.

Usage:
    python3 scripts/generate_keypair.py --passphrase "ma_phrase_secrete_16+chars"
    python3 scripts/generate_keypair.py --passphrase "..." --out ed25519_key.pem
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attest.key_crypto import generate_keypair, serialize_private_key


def main():
    parser = argparse.ArgumentParser(
        description="Genere une paire de cles Ed25519 pour le registre de continuite"
    )
    parser.add_argument("--passphrase", required=True,
                        help="Phrase de passe (min 16 caracteres)")
    parser.add_argument("--out", default="ed25519_key.pem",
                        help="Chemin du fichier PEM de sortie")
    args = parser.parse_args()

    if len(args.passphrase) < 16:
        print("ERREUR : Phrase de passe trop courte. Minimum 16 caracteres.", file=sys.stderr)
        sys.exit(1)

    private_key, pub_hex, fingerprint = generate_keypair()
    serialize_private_key(private_key, args.passphrase, args.out)

    print(f"Cle privee ecrite : {args.out} (permissions 0600)")
    print(f"Cle publique (hex) : {pub_hex}")
    print(f"Empreinte SHA-256 : {fingerprint}")
    print()
    print("Pour enregistrer cette cle dans le registre :")
    print("  key_id       = (choisir un identifiant unique)")
    print("  actor_id     = (votre identifiant)")
    print(f"  public_key_hex = {pub_hex}")
    print(f"  fingerprint    = {fingerprint}")
    print()
    print("ATTENTION : Ne commettez JAMAIS le fichier PEM dans Git.")
    print("           Ne l affichez JAMAIS dans un chat, Notion, ou DuckDB.")


if __name__ == "__main__":
    main()
