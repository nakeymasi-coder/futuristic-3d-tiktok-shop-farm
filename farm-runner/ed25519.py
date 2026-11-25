"""Pure-Python Ed25519 (RFC 8032), standard library only.

Used by the farm runner to check that Mila's approvals and verdicts really
came from Mila (Glam, Nov 25: "Mila approvals count only from her verdict
file"). The runner holds only Mila's PUBLIC key (in farm-rules.json), so it
can check a signature but can never make one. Slow but fine for a few
signatures per run.
"""
import hashlib

_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _h(m):
    return hashlib.sha512(m).digest()


def _inv(x):
    return pow(x, _p - 2, _p)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = (x * _I) % _p
    if x % 2 != 0:
        x = _p - x
    return x


_By = 4 * _inv(5) % _p
_B = (_xrecover(_By) % _p, _By % _p, 1, (_xrecover(_By) * _By) % _p)
_ZERO = (0, 1, 1, 0)


def _add(P, Q):
    x1, y1, z1, t1 = P
    x2, y2, z2, t2 = Q
    a = (y1 - x1) * (y2 - x2) % _p
    b = (y1 + x1) * (y2 + x2) % _p
    c = t1 * 2 * _d * t2 % _p
    dd = z1 * 2 * z2 % _p
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % _p, g * h % _p, f * g % _p, e * h % _p)


def _mul(s, P):
    Q = _ZERO
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _encode(P):
    x, y, z, _ = P
    zi = _inv(z)
    x, y = x * zi % _p, y * zi % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decode(s):
    if len(s) != 32:
        raise ValueError("bad point length")
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= _p:
        raise ValueError("bad point")
    x = _xrecover(y)
    if (-x * x + y * y - 1 - _d * x * x * y * y) % _p != 0:
        raise ValueError("point not on curve")
    if (x & 1) != sign:
        x = _p - x
    return (x, y, 1, x * y % _p)


def _secret(seed):
    h = _h(seed)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_key(seed):
    a, _ = _secret(seed)
    return _encode(_mul(a, _B))


def sign(seed, msg):
    a, prefix = _secret(seed)
    A = _encode(_mul(a, _B))
    r = int.from_bytes(_h(prefix + msg), "little") % _L
    R = _encode(_mul(r, _B))
    k = int.from_bytes(_h(R + A + msg), "little") % _L
    S = (r + k * a) % _L
    return R + int.to_bytes(S, 32, "little")


def verify(pub, msg, sig):
    try:
        if len(sig) != 64:
            return False
        A = _decode(pub)
        R = _decode(sig[:32])
        S = int.from_bytes(sig[32:], "little")
        if S >= _L:
            return False
        k = int.from_bytes(_h(sig[:32] + pub + msg), "little") % _L
        return _encode(_mul(S, _B)) == _encode(_add(R, _mul(k, A)))
    except ValueError:
        return False
