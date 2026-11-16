"""Check sampled candidate motion; this is not a physics or biblical proof."""
import math


def validate_motion(frames, pairs, tolerance=1e-6):
    """Check each being/wheel pair in consecutive world-space samples.

    Rule: same translation and unchanged being orientation between samples.
    A fixed wheel offset is an explicit simplification, not a claim about angles,
    shape, unsampled motion, external spirit, or wheel rotation.
    Each frame: {'time': number, 'objects': {id: {'position': [x,y,z],
    'orientation': [w,x,y,z]}}}. Orientations are unit quaternions; q and -q
    represent the same orientation. Wheel orientation may change.
    """
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 < tolerance < 0.1:
        raise ValueError("tolerance must be finite and between 0 and 0.1")
    if len(frames) < 2 or not pairs:
        return ["at least two frames and one pair required"]
    beings = {b for b, _ in pairs}
    wheels = {w for _, w in pairs}
    if len(beings) != len(pairs) or len(wheels) != len(pairs) or beings & wheels:
        return ["pairs must contain unique, distinct beings and wheels"]
    errors = []

    def vector(frame, ident, key, size):
        obj = frame.get("objects", {}).get(ident, {})
        value = obj.get(key)
        if not isinstance(value, (list, tuple)) or len(value) != size or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value
        ):
            raise ValueError(f"{ident}: invalid {key}")
        if key == "orientation" and abs(sum(v * v for v in value) - 1.0) > tolerance * 2:
            raise ValueError(f"{ident}: orientation quaternion is not unit length")
        return value

    for k, (before, after) in enumerate(zip(frames, frames[1:]), 1):
        tb, ta = before.get("time"), after.get("time")
        if any(isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) for t in (tb, ta)) or ta <= tb:
            errors.append(f"frame {k}: time must increase and be finite")
            continue
        for being, wheel in pairs:
            try:
                bp, bn = vector(before, being, "position", 3), vector(after, being, "position", 3)
                wp, wn = vector(before, wheel, "position", 3), vector(after, wheel, "position", 3)
                qb, qn = vector(before, being, "orientation", 4), vector(after, being, "orientation", 4)
                diff = [(bn[i] - bp[i]) - (wn[i] - wp[i]) for i in range(3)]
                if math.sqrt(sum(v * v for v in diff)) > tolerance:
                    errors.append(f"frame {k}: {wheel} not synchronized with {being}")
                if min(math.dist(qb, qn), math.dist(qb, [-v for v in qn])) > tolerance:
                    errors.append(f"frame {k}: {being} changed orientation")
            except ValueError as exc:
                errors.append(f"frame {k}: {exc}")
    return errors
