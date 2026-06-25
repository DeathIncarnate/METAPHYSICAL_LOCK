
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import re, math

# -----------------------------
# Load dataset
# -----------------------------
csv_path = "C:/Users/Nick/Desktop/contig_pair_topXss.csv"
df_txt = pd.read_csv(csv_path, header=None, dtype=str)
rows_text = [" ".join([str(x) for x in df_txt.iloc[idx].dropna().values]) for idx in range(len(df_txt))]

pattern = re.compile(
    r"\[(\d+)\]\s*last=(\d+)\s*pred_gap=(\d+)\s*true_gap=(\d+)\s*err=(-?\d+)\s*cand=(\d+)\s*verified=(\d+)\s*\?ver=(\d+)"
)
rows = []
for ln in rows_text:
    m = pattern.match(ln.strip())
    if m:
        rows.append({
            "index": int(m.group(1)),
            "last": int(m.group(2)),
            "pred_gap": int(m.group(3)),
            "true_gap": int(m.group(4)),
            "err": int(m.group(5)),
            "cand": int(m.group(6)),
            "verified": int(m.group(7)),
            "ver": int(m.group(8)),
        })
df = pd.DataFrame(rows).sort_values("index").reset_index(drop=True)

# -----------------------------
# Parameters for torus mapping
# -----------------------------
N = len(df)
n_vis = min(1500, N)
t = np.arange(n_vis)

# Frequencies (carrier/envelope/extra)
base3 = [53/116, 5/116, 3/25]

theta1 = 2*np.pi*base3[0]*t
theta2 = 2*np.pi*base3[1]*t

# Torus embedding
R, r = 3.0, 1.0
x = (R + r*np.cos(theta2)) * np.cos(theta1)
y = (R + r*np.cos(theta2)) * np.sin(theta1)
z = r * np.sin(theta2)

# Residuals as color
resid = (df["pred_gap"].values[:n_vis] - df["true_gap"].values[:n_vis])

# -----------------------------
# Build interactive 3D scatter
# -----------------------------
fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection='3d')
p = ax.scatter(x, y, z, c=resid, cmap="coolwarm", s=15, alpha=0.8)

# Overlay harmonic trajectories
tt = np.linspace(0, 2*np.pi*116, 2000)
colors = ['blue','green','orange']
freqs = base3
labels = ['f1 ~53/116','f2 ~5/116','f3 ~3/25']
for f,c,l in zip(freqs, colors, labels):
    ph1 = 2*np.pi*base3[0]*tt
    ph2 = 2*np.pi*base3[1]*tt
    ph_mod = 2*np.pi*f*tt
    xx = (R + r*np.cos(ph_mod)) * np.cos(ph1)
    yy = (R + r*np.cos(ph_mod)) * np.sin(ph1)
    zz = r * np.sin(ph_mod)
    ax.plot(xx, yy, zz, c=c, lw=2, label=l)

ax.set_title("Interactive 3D Torus of Prime Residuals")
ax.legend()
fig.colorbar(p, ax=ax, label="Residual bias")

plt.show()
