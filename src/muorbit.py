
from nsnppt import KOREC
TABLE = dict((l, (k, a)) for (l, k, a) in KOREC)


def full_sim(x, y, cap=200000):
    R = [0] * 8; R[1] = x; R[2] = y
    lab = 'l0'; seen = set(); n = 0
    while lab != 'l22':
        key = (lab, tuple(R))
        if key in seen: return None, n
        seen.add(key)
        kind, args = TABLE[lab]
        if kind == 'ADD':
            R[args[0]] += 1; lab = 'l%d' % args[1]
        else:
            if R[args[0]] > 0: R[args[0]] -= 1; lab = 'l%d' % args[1]
            else: lab = 'l%d' % args[2]
        n += 1
        if n > cap: return None, n
    return R[0], n


def orbit(x, y, maxc=300000):
    """Closed-form model. Returns (r0, dispatches) for HALT, None for cycle."""
    t = 0; u = 0; r2 = y; r3 = 0; r0 = 0
    seen = {}; steps = 0
    xp1 = x + 1
    while True:
        s = 0
        while True:                                  # fetch passes
            C = s + t + 1
            while xp1 % C == 0:
                C += 1
            k = xp1 % C
            t = C - k
            if u > 0:
                u -= 1; s = k                        # l10 consumed r4: refetch
            else:
                break                                # -> interpreter
        r4w = k // 3
        d = k % 3
        halt = False
        if d == 1:
            if r3 > 0:
                r3 -= 1
                if r4w > 0: u = r4w - 1
                else: halt = True
            else:
                r0 += 1; u = r4w
        elif d == 2:
            r2 += 1; r3 += 1
            if r4w > 0: u = r4w - 1
            else: halt = True
        else:
            if r2 > 0:
                r2 -= 1
                if r4w > 0: u = r4w - 1
                else: halt = True
            elif r0 > 0:
                r0 -= 1; u = r4w
            else:
                if r4w > 0: u = r4w - 1
                else: halt = True
        steps += 1
        if halt: return r0, steps
        if steps > maxc: return None, steps
        key = (t, u, r2, r3, r0)
        if key in seen: return None, steps
        seen[key] = 1


if __name__ == '__main__':
    print('validation: orbit model vs full simulation')
    bad = 0
    for x in list(range(0, 400)) + [23, 100, 997]:
        for y in (0, 1, 2, 3):
            r1, n1 = full_sim(x, y, cap=30000)
            r2, n2 = orbit(x, y)
            ok = (r1 is None and r2 is None) or \
                 (r1 is not None and r2 is not None and r1 == r2)
            if not ok:
                bad += 1
                print('  MISMATCH x=%d y=%d: full=%s orbit=%s' % (x, y, r1, r2))
    print('  mismatches: %d' % bad)
