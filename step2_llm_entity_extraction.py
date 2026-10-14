
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI


# 1. Allow only these entity types
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


# 2. Define the structure of one entity
class Entity(BaseModel):
    name: str = Field(description="The entity's name")
    entity_type: EntityType = Field(
        description="The entity's most suitable type"
    )


# 3. Define the complete extraction result
class EntityExtraction(BaseModel):
    entities: list[Entity] = Field(
        description="Unique entities explicitly mentioned in the text"
    )


# 4. Initialize the language model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

structured_llm = llm.with_structured_output(EntityExtraction)


# 5. Find all text files
folder_path = Path("documents")
file_paths = sorted(folder_path.glob("*.txt"))

if not file_paths:
    raise FileNotFoundError(
        "No .txt files found in the documents folder."
    )


# 6. Store all extracted entities here
unique_entities = {}


# 7. Process each document
for file_path in file_paths:
    loader = TextLoader(str(file_path), encoding="utf-8")
    documents = loader.load()

    for document in documents:
        prompt = f"""
        Extract important entities explicitly mentioned in this text.

        Use exactly one of these types for each entity:
        PERSON, ORGANIZATION, LOCATION, PRODUCT,
        TECHNOLOGY, SERVICE, INDUSTRY, OTHER.

        Classification guidance:
        - People: PERSON
        - Companies: ORGANIZATION
        - Physical or geographic places: LOCATION
        - Named goods: PRODUCT
        - Software and technical concepts: TECHNOLOGY
        - Services offered to customers: SERVICE
        - Business sectors: INDUSTRY
        - Use OTHER only when no other type fits.

        Examples:
        "John" -> PERSON
        "Microsoft" -> ORGANIZATION
        "software" -> TECHNOLOGY
        "cloud computing" -> TECHNOLOGY
        "cloud computing services" -> SERVICE
        "technology industry" -> INDUSTRY

        Do not invent entities.
        Do not extract relationships.
        Avoid returning the same entity more than once
        within this document.

        Text:
        {document.page_content}
        """

        result = structured_llm.invoke(prompt)

        source_name = Path(
            document.metadata["source"]
        ).name

        print(f"\nProcessed: {source_name}")

        # 8. Combine duplicates across all documents
        for entity in result.entities:
            name = entity.name.strip()

            if not name:
                continue

            # Ignore capitalization and surrounding whitespace
            key = name.casefold()

            if key not in unique_entities:
                unique_entities[key] = {
                    "name": name,
                    "entity_type": entity.entity_type,
                    "sources": set(),
                }

            # Remember every file that mentions the entity
            unique_entities[key]["sources"].add(source_name)


# 9. Print the final deduplicated entity list
print("\n" + "=" * 50)
print("FINAL UNIQUE ENTITY LIST")
print("=" * 50)

for item in sorted(
    unique_entities.values(),
    key=lambda entity: entity["name"].casefold(),
):
    sources = ", ".join(sorted(item["sources"]))

    print(
        f"\nName: {item['name']}"
        f"\nType: {item['entity_type']}"
        f"\nFound in: {sources}"
    )

print("\n" + "=" * 50)
print("Total unique entities:", len(unique_entities))
print("=" * 50)
