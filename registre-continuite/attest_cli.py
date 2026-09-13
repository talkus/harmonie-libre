# attest_cli.py
# CLI producteur de preuves JSON. Ne decide rien. N'ecrit pas dans la base.

import argparse
import json

from attest.envelope import build_envelope, sign_envelope


def cmd_attest(args):
    from cryptography.hazmat.primitives import serialization

    with open(args.payload, "r", encoding="utf-8") as fh:
        payload_data = json.load(fh)

    with open(args.policy_versions, "r", encoding="utf-8") as fh:
        policy_versions = json.load(fh)

    with open(args.private_key, "rb") as fh:
        private_key = serialization.load_pem_private_key(
            fh.read(), password=None
        )

    envelope = build_envelope(
        key_id=args.key_id,
        actor_id=args.actor_id,
        actor_role=args.actor_role,
        decision_id=args.decision_id,
        decision_type=args.decision_type,
        subject_type=args.subject_type,
        subject_id=args.subject_id,
        payload=payload_data,
        policy_versions=policy_versions,
    )

    canonical, digest, signature_hex = sign_envelope(private_key, envelope)

    record = {
        "protocol": envelope["protocol"],
        "attestation": {
            "attestation_id": envelope["attestation_id"],
            "key_id": envelope["key_id"],
            "actor_id": envelope["actor_id"],
            "actor_role": envelope["actor_role"],
            "attestation_method": "ed25519_jcs_rfc8785",
            "issued_at": envelope["issued_at"],
        },
        "signed_envelope": envelope,
        "signed_payload_hash": digest,
        "signature_hex": signature_hex,
        "signature_algorithm": "Ed25519",
        "canonicalization_scheme": "RFC8785-JCS",
        "hash_algorithm": "sha256",
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)

    print(f"Attestation ecrite : {args.out}")
    print(f"  attestation_id : {envelope['attestation_id']}")
    print(f"  decision_id    : {envelope['decision_id']}")
    print(f"  hash           : {digest[:16]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Producer de preuves d'attestation (JSON)"
    )
    sub = parser.add_subparsers(dest="command")

    p_attest = sub.add_parser("attest", help="Produire une attestation JSON")
    p_attest.add_argument("--private-key", required=True)
    p_attest.add_argument("--key-id", required=True)
    p_attest.add_argument("--actor-id", required=True)
    p_attest.add_argument("--actor-role", required=True)
    p_attest.add_argument("--decision-id", required=True)
    p_attest.add_argument("--decision-type", required=True)
    p_attest.add_argument("--subject-type", required=True)
    p_attest.add_argument("--subject-id", required=True)
    p_attest.add_argument("--payload", required=True)
    p_attest.add_argument("--policy-versions", required=True)
    p_attest.add_argument("--out", required=True)
    p_attest.set_defaults(func=cmd_attest)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
