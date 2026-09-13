"""Authority service — applies attested transitions to the registry.

This is the only component that writes 'valid' in authorization_verification_result.
The CLI is a producer of proofs, not a judge.
"""