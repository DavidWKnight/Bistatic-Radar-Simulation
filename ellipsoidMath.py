import numpy as np

def Ellipsoid():
    a: float
    b: float
    c: float

    def __init__(f1: np.array, f2: np.array):
        # In our case two of the axes, b and c, are the same since we're assuming symmetricality

        # a = semi major axis
        # 2a = dt

        # Definition of an ellipsoid https://en.wikipedia.org/wiki/Ellipsoid#Standard_equation
        # (x**2)/(a**2) + (y**2)/(b**2) + (z**2)/(c**2) = 1
        # With translation added (h in +Z, k in +Y, q in +Z)
        # ((x-h)**2)/(a**2) + (((y-k)**2)/(b**2) + ((z-q)**2)/(c**2) = 1
        # Allow for radius != 1
        # ((x-h)**2)/(a**2) + (((y-k)**2)/(b**2) + ((z-q)**2)/(c**2) = r
        # Replace let a**2 = A; b**2 = B, c**2 = C
        # ((x-h)**2)/A + (((y-k)**2)/B + ((z-q)**2)/C = r
        # Get all unknowns onto right side


        pass
