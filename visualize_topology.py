# visualize_topology.py
import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def visualize_mobius_topology(topology_file: str):
    """3D visualization of the Möbius strip topology"""
    
    with open(topology_file, 'r') as f:
        data = json.load(f)
    
    viz_data = data["visualization"]
    points = viz_data["points_3d"]
    
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Color points by braid
    colors = ['red', 'green', 'blue']
    for point in points:
        braid = point["braid"]
        ax.scatter(point["x"], point["y"], point["z"], 
                  c=colors[braid], s=20, alpha=0.6)
    
    # Draw braid paths
    for braid, path in viz_data["braid_paths"].items():
        path = np.array(path)
        ax.plot(path[:, 0], path[:, 1], path[:, 2], 
               c=colors[braid], alpha=0.3, linewidth=1)
    
    ax.set_title("SECP256K1 Curve: Möbius Strip Three-Braid Topology")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    
    plt.show()

if __name__ == "__main__":
    visualize_mobius_topology("secp256k1_mobius_topology.json")
