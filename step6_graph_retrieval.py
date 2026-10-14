
import os
from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

if not all([uri, username, password]):
    raise ValueError(
        "Neo4j credentials are missing. "
        "Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD."
    )

driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

query = """
MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
RETURN
    s.name AS subject,
    r.type AS relationship,
    o.name AS object
ORDER BY subject
"""

try:
    driver.verify_connectivity()

    with driver.session() as session:
        result = session.run(query)

        print("\nKNOWLEDGE GRAPH RESULTS")
        print("=" * 50)

        count = 0

        for record in result:
            print(
                f"{record['subject']} "
                f"--[{record['relationship']}]--> "
                f"{record['object']}"
            )
            count += 1

        print("=" * 50)
        print(f"Total relationships retrieved: {count}")

finally:
    driver.close()
