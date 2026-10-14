
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase


# 1. Define the allowed entity types
EntityType = Literal[
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "PRODUCT",
    "TECHNOLOGY",
    "SERVICE",
    "INDUSTRY",
    "OTHER",
]


# 2. Define the relationship structure
class Relationship(BaseModel):
    subject: str = Field(description="Starting entity name")
    subject_type: EntityType = Field(description="Starting entity type")
    relationship: str = Field(description="Relationship in uppercase snake case")
    object: str = Field(description="Ending entity name")
    object_type: EntityType = Field(description="Ending entity type")


class RelationshipExtraction(BaseModel):
    relationships: list[Relationship]


# 3. Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
extractor = llm.with_structured_output(RelationshipExtraction)


def extract_relationships(documents_folder):
    relationships = []

    for file_path in sorted(documents_folder.glob("*.txt")):
        document = TextLoader(
            str(file_path), encoding="utf-8"
        ).load()

        if not document:
            continue

        prompt = f"""
        Extract relationships explicitly supported by this text.

        For each relationship, identify:
        - subject and its entity type
        - relationship name in uppercase snake case
        - object and its entity type

        Do not invent facts. Return an empty list if there are no
        supported relationships.

        Text:
        {document[0].page_content}
        """

        result = extractor.invoke(prompt)

        for rel in result.relationships:
            relationships.append({
                "subject": rel.subject.strip(),
                "subject_type": rel.subject_type,
                "relationship": rel.relationship.strip().upper(),
                "object": rel.object.strip(),
                "object_type": rel.object_type,
            })

    return relationships


# 4. Read Neo4j credentials
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

if not all([uri, username, password]):
    raise ValueError(
        "Neo4j credentials are missing. Set NEO4J_URI, "
        "NEO4J_USERNAME, and NEO4J_PASSWORD in CMD."
    )

# 5. Locate documents
documents_folder = Path("documents")

if not documents_folder.exists():
    raise FileNotFoundError("The documents folder was not found.")

# 6. Extract relationships
relationships = extract_relationships(documents_folder)

# 7. Store the graph
driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

try:
    driver.verify_connectivity()

    with driver.session() as session:
        for rel in relationships:
            session.run(
                """
                MERGE (s:Entity {name: $subject})
                ON CREATE SET s.type = $subject_type
                MERGE (o:Entity {name: $object})
                ON CREATE SET o.type = $object_type
                MERGE (s)-[r:RELATED_TO {type: $relationship}]->(o)
                """,
                subject=rel["subject"],
                subject_type=rel["subject_type"],
                relationship=rel["relationship"],
                object=rel["object"],
                object_type=rel["object_type"],
            )

    print(f"Successfully processed {len(relationships)} relationships.")
    print("Knowledge graph saved to Neo4j AuraDB.")

finally:
    driver.close()
