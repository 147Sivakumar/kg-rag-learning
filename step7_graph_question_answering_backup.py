
import os
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI

# 1. Connect to Neo4j
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)

# 2. Initialize the language model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# 3. Retrieve matching facts from the knowledge graph
def retrieve_graph_facts(question):
    query = """
    MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
    WHERE any(
        word IN split(
            toLower($question), ' '
        )
        WHERE size(replace(word, '?', '')) > 2
        AND (
            toLower(s.name) CONTAINS
                replace(replace(word, '?', ''), '.', '')
            OR toLower(o.name) CONTAINS
                replace(replace(word, '?', ''), '.', '')
            OR toLower(r.type) CONTAINS
                replace(replace(word, '?', ''), '.', '')
        )
    )
    RETURN s.name AS subject,
           r.type AS relationship,
           o.name AS object
    LIMIT 20
    """

    with driver.session() as session:
        records = session.run(query, question=question)

        return [
            f"{record['subject']} --[{record['relationship']}]--> "
            f"{record['object']}"
            for record in records
        ]

def retrieve_graph_facts(question):
    query = """
    MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)

    WITH s, r, o,
         toLower($question) AS q

    WHERE
        (toLower(s.name) IN split(q, ' ')
         OR q CONTAINS toLower(s.name))
        OR
        (toLower(o.name) IN split(q, ' ')
         OR q CONTAINS toLower(o.name))

    RETURN s.name AS subject,
           r.type AS relationship,
           o.name AS object

    ORDER BY
        CASE
            WHEN q CONTAINS toLower(s.name) THEN 0
            WHEN q CONTAINS toLower(o.name) THEN 1
            ELSE 2
        END

    LIMIT 20
    """

    with driver.session() as session:
        records = session.run(query, question=question)

        return [
            f"{record['subject']} --[{record['relationship']}]--> "
            f"{record['object']}"
            for record in records
        ]



# 4. Ask a question and generate an answer
if __name__ == "__main__":
    try:
        question = input(
            "Ask a question about your knowledge graph: "
        )

        facts = retrieve_graph_facts(question)

        if not facts:
            print("No matching graph facts were found.")
        else:
            print("\nRetrieved graph facts:")
            for fact in facts:
                print(fact)

            context = "\n".join(facts)

            prompt = f"""
            Answer using only the graph facts provided.
            If the facts do not contain the answer, say so.

            Graph facts:
            {context}

            Question: {question}
            """

            response = llm.invoke(prompt)
            print("\nAnswer:", response.content)

    except Exception as e:
        print("Error:", e)

    finally:
        driver.close()
