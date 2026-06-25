import networkx as nx
import numpy as np
import plotly.graph_objects as go

# Parameters
n_nodes = 150
radius = 1.0

# Place nodes on a sphere using Fibonacci spiral (nice uniform distribution)
indices = np.arange(0, n_nodes, dtype=float) + 0.5
phi = np.arccos(1 - 2*indices/n_nodes)
theta = np.pi * (1 + 5**0.5) * indices

x = radius * np.cos(theta) * np.sin(phi)
y = radius * np.sin(theta) * np.sin(phi)
z = radius * np.cos(phi)
positions = np.vstack((x, y, z)).T

# Build a geometric graph: connect nodes if they're close on the sphere
G = nx.Graph()
for i in range(n_nodes):
    G.add_node(i, pos=positions[i])
dist_thresh = 0.3  # threshold for connection distance
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        dist = np.linalg.norm(positions[i] - positions[j])
        if dist < dist_thresh:
            G.add_edge(i, j)

# Extract for plotting
edge_x, edge_y, edge_z = [], [], []
for u, v in G.edges():
    x0, y0, z0 = positions[u]
    x1, y1, z1 = positions[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    edge_z += [z0, z1, None]

edge_trace = go.Scatter3d(
    x=edge_x, y=edge_y, z=edge_z,
    mode='lines',
    line=dict(color='lightgray', width=1),
    hoverinfo='none'
)

node_trace = go.Scatter3d(
    x=x, y=y, z=z,
    mode='markers',
    marker=dict(symbol='circle',
                size=4,
                color='cyan',
                line=dict(width=0)),
    hoverinfo='none'
)

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title="Network Wrapped Around a Sphere 🌐",
                    showlegend=False,
                    scene=dict(xaxis=dict(visible=False),
                               yaxis=dict(visible=False),
                               zaxis=dict(visible=False)),
                    margin=dict(l=0, r=0, b=0, t=30))
               )
fig.show()
