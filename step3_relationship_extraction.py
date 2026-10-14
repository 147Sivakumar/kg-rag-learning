
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI


# 1. Define allowed entity types
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


# 2. Define one relationship
class Relationship(BaseModel):
    subject: str = Field(
        description="Name of the starting entity"
    )
    subject_type: EntityType = Field(
        description="Type of the starting entity"
    )
    relationship: str = Field(
        description="Short relationship label, such as WORKS_AT"
    )
    object: str = Field(
        description="Name of the connected entity"
    )
    object_type: EntityType = Field(
        description="Type of the connected entity"
    )


# 3. Define the extraction result
class RelationshipExtraction(BaseModel):
    relationships: list[Relationship] = Field(
        description="Relationships explicitly supported by the text"
    )


# 4. Initialize the language model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

structured_llm = llm.with_structured_output(
    RelationshipExtraction
)


# 5. Find the documents
folder_path = Path("documents")
file_paths = sorted(folder_path.glob("*.txt"))

if not file_paths:
    raise FileNotFoundError(
        "No .txt files found in the documents folder."
    )


# 6. Store unique relationships
unique_relationships = {}


# 7. Process each document
for file_path in file_paths:
    loader = TextLoader(
        str(file_path),
        encoding="utf-8",
    )
    documents = loader.load()

    for document in documents:
        prompt = f"""
        Extract relationships explicitly stated in this text.

        Return each relationship as:
        subject, subject_type, relationship,
        object, object_type.

        Allowed entity types:
        PERSON, ORGANIZATION, LOCATION, PRODUCT,
        TECHNOLOGY, SERVICE, INDUSTRY, OTHER.

        Use short uppercase relationship labels,
        such as WORKS_AT, DEVELOPS, USES, or LOCATED_IN.

        Examples:
        "John works at OpenAI."
        -> (John, PERSON, WORKS_AT, OpenAI, ORGANIZATION)

        "OpenAI develops artificial intelligence."
        -> (OpenAI, ORGANIZATION, DEVELOPS,
            artificial intelligence, TECHNOLOGY)

        Only extract relationships supported by the text.
        Do not invent facts.
        Do not return a relationship if the connection is unclear.
        If no relationships are stated, return an empty list.

        Text:
        {document.page_content}
        """

        result = structured_llm.invoke(prompt)

        source_name = Path(
            document.metadata["source"]
        ).name

        print(f"\nProcessed: {source_name}")

        for item in result.relationships:
            subject = item.subject.strip()
            relation = item.relationship.strip().upper()
            object_name = item.object.strip()

            if not subject or not relation or not object_name:
                continue

            # Deduplicate equivalent triples, ignoring capitalization
            key = (
                subject.casefold(),
                relation,
                object_name.casefold(),
            )

            if key not in unique_relationships:
                unique_relationships[key] = {
                    "subject": subject,
                    "subject_type": item.subject_type,
                    "relationship": relation,
                    "object": object_name,
                    "object_type": item.object_type,
                    "sources": set(),
                }

            unique_relationships[key]["sources"].add(
                source_name
            )


# 8. Print all unique relationships
print("\n" + "=" * 60)
print("FINAL UNIQUE RELATIONSHIPS")
print("=" * 60)

for item in sorted(
    unique_relationships.values(),
    key=lambda r: (
        r["subject"].casefold(),
        r["relationship"],
        r["object"].casefold(),
    ),
):
    print(
        f"\n({item['subject']} "
        f"[{item['subject_type']}], "
        f"{item['relationship']}, "
        f"{item['object']} "
        f"[{item['object_type']}])"
    )

    print(
        "Found in:",
        ", ".join(sorted(item["sources"])),
    )

print("\n" + "=" * 60)
print(
    "Total unique relationships:",
    len(unique_relationships),
)
print("=" * 60)
