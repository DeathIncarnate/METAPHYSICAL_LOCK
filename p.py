import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Parameters
u = np.linspace(0, 2*np.pi, 100)
w = np.linspace(-1, 1, 30)
U, W = np.meshgrid(u, w)

# Parametric equations for Möbius strip
X = (1 + (W/2)*np.cos(7*U/2)) * np.cos(U)
Y = (1 + (W/2)*np.cos(7*U/2)) * np.sin(U)
Z = (W/2)*np.sin(7*U/2)




# Plot
fig = plt.figure(figsize=(20,16))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, color="cyan", alpha=0.7, edgecolor="k", linewidth=0.2)

# Axis labels with explanations
ax.set_xlabel("x = (1 + (w/2)cos(u/2))cos(u)\n(loop around, u)", fontsize=9)
ax.set_ylabel("y = (1 + (w/2)sin(u/2))cos(u)\n(loop around, u)", fontsize=9)
ax.set_zlabel("z = (w/2)sin(u/2)\n(half-twist, u/2)", fontsize=9)

ax.set_title("Möbius Strip with Parametric Coordinates (u, w)", fontsize=12)
plt.show()
