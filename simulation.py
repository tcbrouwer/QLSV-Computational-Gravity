import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# --- CINEMATIC PHYSICS CONSTANTS ---
COUPLING_C = 2.0      # Gentle Gravity
LAMBDA = 0.5
DAMPING = 0.1         # Smooth motion
DT = 0.05
TIME_STEPS = 400      # Give it time to settle
GRID_SIZE = 6         # 6x6x6 = 216 nodes (Dense enough to look cool)
MASS_STRENGTH = 0.5   # Gentle warping (not total collapse)

# --- 1. SETUP 3D UNIVERSE ---
def create_universe_3d(size):
    G = nx.grid_graph(dim=[size, size, size])
    for n in G.nodes():
        # n is tuple (x,y,z)
        G.nodes[n]['pos'] = np.array([float(n[0]), float(n[1]), float(n[2])])
        G.nodes[n]['vel'] = np.array([0.0, 0.0, 0.0])
        G.nodes[n]['type'] = 'vacuum'
    return G

# --- 2. INJECT MASS ---
def inject_mass(G, strength):
    positions = [d['pos'] for n, d in G.nodes(data=True)]
    center_loc = np.mean(positions, axis=0)
    center_node = min(G.nodes(), key=lambda n: np.linalg.norm(G.nodes[n]['pos'] - center_loc))
    
    G.nodes[center_node]['type'] = 'mass'
    
    for u, v in G.edges():
        G[u][v]['ideal'] = 1.0 
        if u == center_node or v == center_node:
            G[u][v]['ideal'] = 1.0 - strength
    return G, center_node

# --- 3. PHYSICS ENGINE ---
def update_universe(G):
    forces = {n: np.zeros(3) for n in G.nodes()}
    
    for u, v in G.edges():
        p1 = G.nodes[u]['pos']
        p2 = G.nodes[v]['pos']
        diff = p2 - p1
        dist = np.linalg.norm(diff)
        
        if dist < 0.1: dist = 0.1 # Clamp
        
        direction = diff / dist
        ideal = G[u][v]['ideal']
        
        # Tension
        tension = -COUPLING_C * (dist - ideal)
        f_vec = tension * direction
        
        if G.nodes[u]['type'] != 'mass': forces[u] += f_vec
        if G.nodes[v]['type'] != 'mass': forces[v] -= f_vec

    for n in G.nodes():
        if G.nodes[n]['type'] == 'mass': continue
        G.nodes[n]['vel'] += forces[n] * DT
        G.nodes[n]['vel'] *= (1.0 - DAMPING)
        G.nodes[n]['pos'] += G.nodes[n]['vel'] * DT
        
    return G

# --- MAIN LOOP ---
print("Rendering Cinematic Universe...")
universe = create_universe_3d(GRID_SIZE)
universe, mass_node = inject_mass(universe, MASS_STRENGTH)

# Before state
pos_initial = {n: universe.nodes[n]['pos'].copy() for n in universe.nodes()}

# Evolution
for t in range(TIME_STEPS):
    universe = update_universe(universe)

pos_final = {n: universe.nodes[n]['pos'] for n in universe.nodes()}

# --- CINEMATIC VISUALIZATION ---
plt.style.use('dark_background') # Make it Sci-Fi
fig = plt.figure(figsize=(16, 8))

# Helper to calculate colors based on distance to center
def get_colors(graph, positions, center_node):
    center_pos = positions[center_node]
    colors = []
    sizes = []
    for n in graph.nodes():
        if n == center_node:
            # FIX: Use RGB Tuple instead of Hex String to prevent array error
            colors.append((1.0, 0.0, 0.33)) # Neon Red
            sizes.append(200)
        else:
            # Distance based color (Blue -> Purple -> White)
            d = np.linalg.norm(positions[n] - center_pos)
            # Normalized intensity
            intensity = max(0, min(1, 1 - (d / (GRID_SIZE*0.8))))
            # Blending Blue to Magenta
            colors.append((intensity, 0.2, 1.0 - intensity * 0.5)) 
            sizes.append(30 + intensity * 50)
    return colors, sizes

# PLOT 1: VACUUM
ax1 = fig.add_subplot(121, projection='3d')
ax1.set_title("T=0: The Quantum Vacuum", fontsize=16, color='white')
ax1.grid(False)
ax1.set_axis_off() # Hide axes for cleaner look

cols, sizes = get_colors(universe, pos_initial, mass_node)
xs = [pos_initial[n][0] for n in universe.nodes()]
ys = [pos_initial[n][1] for n in universe.nodes()]
zs = [pos_initial[n][2] for n in universe.nodes()]

ax1.scatter(xs, ys, zs, c=cols, s=sizes, alpha=0.6, edgecolors='none')

# PLOT 2: GRAVITY WELL
ax2 = fig.add_subplot(122, projection='3d')
ax2.set_title("T=400: Emergent Gravity (The Porcupine)", fontsize=16, color='white')
ax2.grid(False)
ax2.set_axis_off()

cols, sizes = get_colors(universe, pos_final, mass_node)
xs = [pos_final[n][0] for n in universe.nodes()]
ys = [pos_final[n][1] for n in universe.nodes()]
zs = [pos_final[n][2] for n in universe.nodes()]

ax2.scatter(xs, ys, zs, c=cols, s=sizes, alpha=0.8, edgecolors='none')

# Add connection lines only for the final plot (Porcupine Effect)
# Only draw lines connected to the center mass to keep it clean
center_pos = pos_final[mass_node]
for n in universe.neighbors(mass_node):
    p = pos_final[n]
    ax2.plot([center_pos[0], p[0]], [center_pos[1], p[1]], [center_pos[2], p[2]], 
             color='#FF0055', alpha=0.5, linewidth=1)

plt.tight_layout()
plt.savefig('qlsv_cinematic_3d.png', dpi=150, facecolor='black')
print("Render complete. Check 'qlsv_cinematic_3d.png'")
plt.show()
