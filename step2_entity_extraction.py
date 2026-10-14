
from pathlib import Path
from langchain_community.document_loaders import TextLoader

# Step 1: Load documents
folder_path = Path("documents")
file_paths = sorted(folder_path.glob("*.txt"))

documents = []

for file_path in file_paths:
    loader = TextLoader(str(file_path), encoding="utf-8")
    documents.extend(loader.load())

# Step 2: Define known entities
entity_dictionary = {
    "PERSON": ["John", "Sarah"],
    "ORGANIZATION": ["OpenAI", "Microsoft"],
    "TECHNOLOGY": [
        "artificial intelligence",
        "cloud computing",
        "software",
    ],
}

# Step 3: Extract unique entities from each document
for document in documents:
    text = document.page_content.lower()
    found_entities = {}

    for entity_type, entity_names in entity_dictionary.items():
        for entity in entity_names:
            if entity.lower() in text:
                found_entities[entity.lower()] = (
                    entity,
                    entity_type,
                )

    # Step 4: Display unique entities
    print("\nSource:", document.metadata["source"])
    print("Entities:")

    for entity, entity_type in found_entities.values():
        print(f"  {entity} -> {entity_type}")

    print("Unique entity count:", len(found_entities))
