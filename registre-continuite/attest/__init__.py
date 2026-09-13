"""Attestation layer — envelope construction, signing, and verification.

The CLI produces JSON proofs. The authority service applies them.
Only apply_status_transition writes 'valid' in authorization_verification_result.
"""