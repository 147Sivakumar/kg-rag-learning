
import os
from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

if not all([uri, username, password]):
    raise ValueError(
        "Missing Neo4j credentials. "
        "Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD."
    )

driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

try:
    driver.verify_connectivity()
    print("Successfully connected to Neo4j AuraDB!")

    with driver.session() as session:
        result = session.run("RETURN 'KG-RAG connection works!' AS message")
        print(result.single()["message"])

except Exception as error:
    print("Connection failed:", error)

finally:
    driver.close()
