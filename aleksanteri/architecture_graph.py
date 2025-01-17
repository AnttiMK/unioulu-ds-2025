import networkx as nx
import matplotlib.pyplot as plt

# Define the graph
G = nx.DiGraph()

# Add nodes (microservices)
services = [
    "Policy Store", 
    "Authentication Gateway", 
    "Risk Assessment", 
    "Access Enforcement", 
    "Logging & Monitoring", 
    "Edge Enforcement Point", 
    "Management Dashboard"
]

G.add_nodes_from(services)

# Add edges (links between microservices)
edges = [
    ("Policy Store", "Access Enforcement"),       # Policy store sends policies to enforcement
    ("Policy Store", "Edge Enforcement Point"),   # Sync policies to edge nodes
    ("Policy Store", "Risk Assessment"),          # Policy updates influence risk assessment
    ("Authentication Gateway", "Access Enforcement"),  # Auth results sent to enforcement
    ("Authentication Gateway", "Risk Assessment"),     # Auth data used for risk scoring
    ("Risk Assessment", "Access Enforcement"),    # Risk scores influence access decisions
    ("Access Enforcement", "Logging & Monitoring"), # Access attempts logged
    ("Authentication Gateway", "Logging & Monitoring"), # Auth events logged
    ("Risk Assessment", "Logging & Monitoring"),  # Risk alerts logged
    ("Edge Enforcement Point", "Logging & Monitoring"), # Edge activities logged
    ("Management Dashboard", "Policy Store"),     # Admin updates policies via dashboard
    ("Management Dashboard", "Logging & Monitoring") # Dashboard monitors logs and system health
]

G.add_edges_from(edges)

# Draw the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)
nx.draw(
    G, pos, with_labels=True, node_size=3000, node_color="lightblue", font_size=10, font_weight="bold"
)
nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True)
plt.title("Zero-Trust Access Control System - Microservices Architecture", fontsize=14)
plt.show()
