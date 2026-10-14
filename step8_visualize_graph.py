
import os
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)

# Create a NetworkX graph
graph = nx.DiGraph()

try:
    # Read relationships from Neo4j
    query = """
    MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
    RETURN s.name AS subject,
           s.type AS subject_type,
           r.type AS relationship,
           o.name AS object,
           o.type AS object_type
    """

    with driver.session() as session:
        records = list(session.run(query))

    # Add entities and relationships
    for record in records:
        graph.add_node(
            record["subject"],
            entity_type=record["subject_type"]
        )

        graph.add_node(
            record["object"],
            entity_type=record["object_type"]
        )

        graph.add_edge(
            record["subject"],
            record["object"],
            relationship=record["relationship"]
        )

    if graph.number_of_nodes() == 0:
        print("No graph data found in Neo4j.")
    else:
        # Calculate node positions
        positions = nx.spring_layout(graph, seed=42)

        # Draw nodes and labels
        plt.figure(figsize=(14, 9))

        nx.draw_networkx_nodes(
            graph, positions,
            node_size=2500,
            node_color="lightblue"
        )

        nx.draw_networkx_labels(
            graph, positions,
            font_size=9
        )

        nx.draw_networkx_edges(
            graph, positions,
            arrows=True,
            arrowsize=20,
            edge_color="gray"
        )

        # Draw relationship names on edges
        edge_labels = nx.get_edge_attributes(
            graph, "relationship"
        )

        nx.draw_networkx_edge_labels(
            graph, positions,
            edge_labels=edge_labels,
            font_size=8
        )

        plt.title("My KG-RAG Knowledge Graph")
        plt.axis("off")
        plt.tight_layout()

        # Save the graph image
        plt.savefig(
            "knowledge_graph.png",
            dpi=200,
            bbox_inches="tight"
        )

        print("Graph image saved as knowledge_graph.png")
        plt.show()

finally:
    driver.close()
