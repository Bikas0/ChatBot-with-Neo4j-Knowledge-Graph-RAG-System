import os
import warnings
from typing import Tuple, List
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
warnings.filterwarnings("ignore", category=DeprecationWarning)


# Define the Entities model
class Entities(BaseModel):
    names: List[str] = Field(
        ..., description="All person, organization, or business entities in the text"
    )

# Define prompt for entity extraction
def create_prompt_template():
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are extracting organization and person entities from the text."),
            ("human", "Use the given format to extract information from the following input: {question}"),
        ]
    )

# Generate full-text query from input
def generate_full_text_query(input: str) -> str:
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

# Structured retrieval function
def structured_retriever(question: str, graph, entity_chain) -> str:
    result = ""
    try:
        entities = entity_chain.invoke({"question": question})
        for entity in entities.names:
            response = graph.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                YIELD node,score
                CALL {
                  WITH node
                  MATCH (node)-[r:!MENTIONS]->(neighbor)
                  RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                  UNION ALL
                  WITH node
                  MATCH (node)<-[r:!MENTIONS]-(neighbor)
                  RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
                }
                RETURN output LIMIT 50
                """,
                {"query": generate_full_text_query(entity)},
            )
            result += "\n".join([el['output'] for el in response])
    except Exception as e:
        result += f"Error in structured retrieval: {e}"
    return result

# Define retriever function
def retriever(question: str, graph, entity_chain, vector_index):
    structured_data = structured_retriever(question, graph, entity_chain)
    unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
    final_data = f"""Structured data:
    {structured_data}
    Unstructured data:
    {"#Document ".join(unstructured_data)}
    """
    return final_data

# Define question handling and answer generation function
def Chat(graph, llm, embedding, vector_index, question):
    # Initialize components
    entity_chain = create_prompt_template() | llm.with_structured_output(Entities)

    # Condense a chat history and follow-up question into a standalone question
    _template = """Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question,
    in its original language.
    Chat History:
    {chat_history}
    Follow-Up Input: {question}
    Standalone question:"""  # noqa: E501
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

    # Condense chat history and follow-up question if chat history exists
    def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
        buffer = []
        for human, ai in chat_history:
            buffer.append(HumanMessage(content=human))
            buffer.append(AIMessage(content=ai))
        return buffer

    _search_query = RunnableBranch(
        (
            RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(run_name="HasChatHistoryCheck"),
            RunnablePassthrough.assign(
                chat_history=lambda x: _format_chat_history(x["chat_history"])
            )
            | CONDENSE_QUESTION_PROMPT
            | llm
            | StrOutputParser(),
        ),
        RunnableLambda(lambda x: x["question"]),
    )

    # Build final prompt template
    template = """Answer the question based only on the following context. Please understand the overall meaning of the question, even if there are spelling mistakes, and ensure that no negative words or sentences are used, like Unfortunately:
    {context}
    Question: {question}
    Use natural language and be concise.
    Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        RunnableParallel(
            {
                "context": _search_query | (lambda q: retriever(q, graph, entity_chain, vector_index)),
                "question": RunnablePassthrough(),
            }
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    # Invoke the chain and return the response
    try:
        response = chain.invoke({"question": question})
    except Exception as e:
        response = f"Error: {e}"
    return response