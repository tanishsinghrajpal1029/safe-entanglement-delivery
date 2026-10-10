import math
def _gammq(a, x):
    """regularised upper incomplete gamma Q(a, x) (Numerical Recipes: series for x < a + 1, continued fraction otherwise)."""
    if x <= 0: return 1.0
    gln = math.lgamma(a)
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(100000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15: break
        return 1.0 - s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 100000):
        an = -i * (i - a); b += 2; d = an * d + b
        if abs(d) < 1e-300: d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300: c = 1e-300
        d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-15: break
    return math.exp(-x + a * math.log(x) - gln) * h
class _Chi2:
    @staticmethod
    def sf(x, dof): return _gammq(dof / 2.0, x / 2.0)
chi2 = _Chi2()
