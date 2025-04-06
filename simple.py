import numpy as np
import scipy
import matplotlib.pyplot as plt
import scipy.optimize

# Center of the reference frame is the transmitter
# Pulse is transmitted at t=0

transmitterENU = np.array([0, 0, 0])

targetsENU = np.array([
    [0, 1, 0]
])

receiversENU = np.array([
    [2, 0, 0], # 1km east
    [2, 0.2, 0], 
    [2, -0.2, 0]
])
dReceiver = np.linalg.norm(receiversENU - transmitterENU,axis=1)

# Replace c later with speed of light in air
tDirectRX = dReceiver / scipy.constants.c
tTargetRX = (np.linalg.norm(targetsENU, axis=1) + np.linalg.norm(targetsENU-receiversENU, axis=1)) / scipy.constants.c

# Could insert noise onto time measurements

dTargetPath = ((tTargetRX - tDirectRX) * scipy.constants.c) + dReceiver

targetSemiMajorAxis = dTargetPath / 2 # ellipse d1 + d2 = 2a https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:conics/x9e81a4f98389efdf:ellipse-foci/v/foci-of-an-ellipse
targetSemiMinorAxis = np.sqrt((dTargetPath / 2)**2 - (dReceiver/2)**2)



dTargetTruth = np.linalg.norm(targetsENU - receiversENU, axis=1)

def est(p):
    d1 = np.linalg.norm(p - transmitterENU)
    d2 = np.linalg.norm(p - receiversENU, axis=1)
    dist = d1 + d2
    error = dist - dTargetPath
    print(f"p = {p}, error = {np.sum(error**2)}")
    return np.sum(error**2)

general = scipy.optimize.minimize(est, np.zeros(3), method='Nelder-Mead', tol=1e-12)
print(f"general = {general}")
# print(f"{est([0, 1e3, 0])}")

# def mapEllipse(a, b, h, k):
#     # ((x-h)**2 / a**2) + (y**2)/(b**2) = 1
#     # (y**2)/(b**2) = 1 - ((x-h)**2 / a**2)
#     # (y**2) = (b**2) * (1 - ((x-h)**2 / a**2))
#     # y = sqrt((b**2) * (1 - ((x-h)**2 / a**2)))
#     # y = np.sqrt((b**2) * (1 - ((x-h)**2 / a**2)))
#     x = np.linspace(-a, a, 100)
#     y = (b/a) * np.sqrt(a**2 - x**2)+k
#     ny = -y # Don't forget negative half
#     return [np.concatenate([x,x[::-1]]) + h, np.concatenate([y, ny[::-1]])]

# plt.scatter(transmitterENU[0], transmitterENU[1])
# plt.scatter(targetsENU[:,0], targetsENU[:,1])
# plt.scatter(receiversENU[:,0], receiversENU[:,1])

# # Plot ellipses
# # [x, y] = mapEllipse(1, 1, 0)
# [x, y] = mapEllipse(targetSemiMajorAxis[0], targetSemiMinorAxis[0], dReceiver[0]/2, receiversENU[0][1]/2)
# plt.plot(x, y)
# [x, y] = mapEllipse(targetSemiMajorAxis[1], targetSemiMinorAxis[1], dReceiver[1]/2, receiversENU[1][1]/2)

# theta = -np.arctan2(receiversENU[1][1], receiversENU[1][0])
# DCM = np.array([
#     [np.cos(theta), -np.sin(theta)],
#     [np.sin(theta), np.cos(theta)]
# ])
# out = DCM @ np.array([x, y])
# plt.plot(out[0, :], out[1, :])

# # [x, y] = mapEllipse(targetSemiMajorAxis[2], targetSemiMinorAxis[2], dReceiver[2]/2, receiversENU[2][1]/2)
# # plt.plot(x, y)

# plt.show()
