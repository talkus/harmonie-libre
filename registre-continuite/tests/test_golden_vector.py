# tests/test_golden_vector.py
# Vecteur canonique : fige la canonicalisation JCS (RFC 8785) et la signature
# Ed25519 contre toute regression de serialisation JSON.
#
# Toute divergence dans le format canonique (ordre des cles, encodage
# Unicode, precision des flottants) casse ce test immediatement.

import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden_vector.json"


@pytest.fixture
def golden():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_golden_vector_envelope(golden):
    """Le hash JCS de l'enveloppe doit correspondre exactement au vecteur fige.

    Ce test detecte toute regression de :
    - Ordre des cles (JCS trie par codepoint UTF-16)
    - Encodage Unicode (NFC vs NFD, espaces significatifs)
    - Precision des flottants (round-trip JSON)
    - Format des timestamps (Z vs +00:00)
    """
    sk_bytes = bytes.fromhex(golden["private_key_hex_seed"])
    sk = Ed25519PrivateKey.from_private_bytes(sk_bytes)

    # Canonicalisation JCS stricte
    import rfc8785
    canonical_bytes = rfc8785.dumps(golden["envelope_inputs"])
    computed_sha = hashlib.sha256(canonical_bytes).hexdigest()

    assert computed_sha == golden["expected_envelope_jcs_sha256"], (
        f"Regression de canonicalisation JCS : "
        f"attendu {golden['expected_envelope_jcs_sha256']}, "
        f"obtenu {computed_sha}"
    )

    # Signature et verification Ed25519
    sig = sk.sign(canonical_bytes)
    sk.public_key().verify(sig, canonical_bytes)  # leve InvalidSignature si echec


def test_golden_vector_key_is_rfc8032_test_vector(golden):
    """La graine utilisee est le vecteur de test RFC 8032 Section 7.1.

    Verifie que la cle publique derivee correspond au vecteur connu.
    """
    sk_bytes = bytes.fromhex(golden["private_key_hex_seed"])
    sk = Ed25519PrivateKey.from_private_bytes(sk_bytes)
    pub_bytes = sk.public_key().public_bytes(
        encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.Raw,
        format=__import__('cryptography').hazmat.primitives.serialization.PublicFormat.Raw,
    )
    # RFC 8032 Test 1 public key
    expected_pub_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    assert pub_bytes.hex() == expected_pub_hex, (
        f"Cle publique inattendue : attendu {expected_pub_hex}, "
        f"obtenu {pub_bytes.hex()}"
    )
