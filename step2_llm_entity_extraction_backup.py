
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI


# 1. Define the structure for each entity
class Entity(BaseModel):
    name: str = Field(description="Name of the entity")
    entity_type: str = Field(
        description="PERSON, ORGANIZATION, LOCATION, "
                    "PRODUCT, TECHNOLOGY, or OTHER"
    )


# 2. Define the structure for the extraction result
class EntityExtraction(BaseModel):
    entities: List[Entity] = Field(
        description="Entities explicitly mentioned in the text"
    )


# 3. Initialize the language model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

structured_llm = llm.with_structured_output(EntityExtraction)


# 4. Load documents from Step 1
folder_path = Path("documents")
file_paths = sorted(folder_path.glob("*.txt"))

if not file_paths:
    raise FileNotFoundError(
        "No .txt files found in the documents folder."
    )


# 5. Extract entities from each document
for file_path in file_paths:
    loader = TextLoader(str(file_path), encoding="utf-8")
    documents = loader.load()

    for document in documents:
        prompt = f"""
        Extract the important entities explicitly mentioned
        in the following text.

        Identify people, organizations, locations, products,
        and technologies.

        Do not invent entities. Do not extract relationships.
        Return the entity names and their types.

        Text:
        {document.page_content}
        """

        result = structured_llm.invoke(prompt)

        print("\nSource:", document.metadata["source"])
        print("Extracted entities:")

        for entity in result.entities:
            print(
                f"  {entity.name} -> {entity.entity_type}"
            )
