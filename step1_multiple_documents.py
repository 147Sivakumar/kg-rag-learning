
from pathlib import Path
from langchain_community.document_loaders import TextLoader

folder_path = Path("documents")
file_paths = list(folder_path.glob("*.txt"))

documents = []

for file_path in file_paths:
    loader = TextLoader(str(file_path), encoding="utf-8")
    loaded_docs = loader.load()
    documents.extend(loaded_docs)

print("Total documents loaded:", len(documents))

for index, document in enumerate(documents, start=1):
    filename = Path(document.metadata["source"]).name
    character_count = len(document.page_content)

    print(f"\nDocument {index}")
    print("Filename:", filename)
    print("Characters:", character_count)
