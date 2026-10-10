import math
import numpy as np
_lg = np.vectorize(math.lgamma, otypes=[float])
def betaln(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return _lg(a) + _lg(b) - _lg(a + b)
