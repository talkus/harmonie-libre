# attest/key_crypto.py
# Generation et serialisation des cles Ed25519.
# PKCS#8 chiffre avec phrase de passe — jamais de cle privee en clair.

import hashlib
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_keypair() -> tuple[Ed25519PrivateKey, str, str]:
    """Genere une paire Ed25519.

    Returns:
        (private_key, public_key_hex, fingerprint_sha256)
    """
    private_key = Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub_hex = pub_bytes.hex()
    fingerprint = hashlib.sha256(pub_bytes).hexdigest()
    return private_key, pub_hex, fingerprint


def serialize_private_key(
    private_key: Ed25519PrivateKey,
    passphrase: str,
    path: str | None = None,
) -> bytes:
    """Serialise une cle privee Ed25519 en PKCS#8 chiffre.

    Ne stockez JAMAIS le resultat sans chiffrement supplementaire ou
    sans permissions 0600. Ne passez JAMAIS le contenu par chat, Git,
    Notion, n8n, ou DuckDB.

    Args:
        private_key: La cle privee Ed25519.
        passphrase: Phrase de passe (min 16 caracteres recommande).
        path: Si fourni, ecrit le PEM a ce chemin avec permissions 0600.
    """
    if len(passphrase) < 16:
        raise ValueError(
            "Phrase de passe trop courte : minimum 16 caracteres."
        )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            passphrase.encode("utf-8")
        ),
    )

    if path:
        # Ecrire avec permissions restrictives
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(pem)
    return pem


def load_private_key(path: str, passphrase: str) -> Ed25519PrivateKey:
    """Charge une cle privee depuis un fichier PKCS#8 chiffre.

    Note : ssh-keygen peut avoir des difficultes a lire certains
    PKCS#8 chiffres pour Ed25519. Utilisez cette fonction (via
    cryptography.load_pem_private_key) plutot que ssh-keygen.
    """
    with open(path, "rb") as fh:
        pem = fh.read()
    return serialization.load_pem_private_key(
        pem,
        password=passphrase.encode("utf-8"),
    )


def fingerprint_of_public_hex(public_key_hex: str) -> str:
    """Calcule le SHA-256 des 32 octets bruts de la cle publique.

    C'est la methode canonique et sans ambiguite.
    Ne pas utiliser l'empreinte du PEM (variations d'encodage).
    """
    pub_bytes = bytes.fromhex(public_key_hex)
    if len(pub_bytes) != 32:
        raise ValueError(
            f"Cle publique Ed25519 attendue : 32 octets, recu {len(pub_bytes)}."
        )
    return hashlib.sha256(pub_bytes).hexdigest()
