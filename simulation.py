import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# --- QLSV CONSTANTS ---
COUPLING_C = 20.0     # Strength of Gravity
LAMBDA = 0.5          # Correlation Length
DAMPING = 0.05        # Thermodynamic cooling
DT = 0.05             # Time Step
TIME_STEPS = 200      # Evolution Steps

# --- 1. SETUP THE VACUUM (S) ---
def create_universe(rows=5, cols=10):
    G = nx.Graph()
    # Manually create lattice to ensure stability
    for i in range(cols):
        for j in range(rows):
            x = i + (0.5 if j % 2 == 1 else 0)
            y = j * (np.sqrt(3)/2)
            G.add_node((i, j), pos=np.array([x, y]), vel=np.array([0., 0.]), type='vacuum')
    
    # Connect neighbors
    nodes = list(G.nodes(data=True))
    for i in range(len(nodes)):
        for k in range(i + 1, len(nodes)):
            n1, d1 = nodes[i]
            n2, d2 = nodes[k]
            dist = np.linalg.norm(d1['pos'] - d2['pos'])
            if dist < 1.1: G.add_edge(n1, n2)
    return G

# --- 2. INTRODUCE MASS (Q) ---
def inject_mass(G, mass_strength=0.9):
    pos_list = [d['pos'] for n, d in G.nodes(data=True)]
    center_loc = np.mean(pos_list, axis=0)
    center_node = min(G.nodes(), key=lambda n: np.linalg.norm(G.nodes[n]['pos'] - center_loc))
    
    G.nodes[center_node]['type'] = 'mass'
    
    for u, v in G.edges():
        G[u][v]['ideal'] = 1.0 
        if u == center_node or v == center_node:
            G[u][v]['ideal'] = 1.0 - mass_strength
    return G, center_node

# --- 3. THE RELATIONAL UPDATE LAW (Eq 2) ---
def update_universe(G):
    forces = {n: np.zeros(2) for n in G.nodes()}
    
    for u, v in G.edges():
        p1 = G.nodes[u]['pos']
        p2 = G.nodes[v]['pos']
        diff = p2 - p1
        dist = np.linalg.norm(diff)
        
        if dist < 0.01: dist = 0.01 # Stability clamp
        
        direction = diff / dist
        ideal = G[u][v]['ideal']
        
        # Calculate Tension
        tension = -COUPLING_C * (dist - ideal)
        f_vec = tension * direction
        
        if G.nodes[u]['type'] != 'mass': forces[u] += f_vec
        if G.nodes[v]['type'] != 'mass': forces[v] -= f_vec

    # Apply Integration
    for n in G.nodes():
        if G.nodes[n]['type'] == 'mass': continue
        G.nodes[n]['vel'] += forces[n] * DT
        G.nodes[n]['vel'] *= (1.0 - DAMPING)
        G.nodes[n]['pos'] += G.nodes[n]['vel'] * DT
        
    return G
    
# --- RUN & SAVE ---
# (Visualization code omitted for brevity; see README)
# plt.savefig('qlsv_simulation.png')