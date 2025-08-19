import os
from typing import Iterable, Any
from langchain_core.runnables import  RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from neo4j import GraphDatabase
from neo4j import  Driver
from pydantic import SecretStr


class GraphAIAgent:
    """GraphRAG Agent for handling graph-based RAG tasks."""
    __llm_gemini: ChatGoogleGenerativeAI
    __llm_openai: ChatOpenAI
    __llm_ollama: ChatOllama
    __llm_transformer: LLMGraphTransformer

    __chunk_size: int
    __overlap: int

    def __init__(self, ai_model: str, chunk_size: int, overlap: int, ai_api_key: SecretStr = SecretStr("")):
        if ai_model.startswith("gemini"):
            # using google-gemini-api
            self.__llm_gemini = ChatGoogleGenerativeAI(model=ai_model, temperature=0.0, google_api_key=ai_api_key)
            self.__llm_transformer = LLMGraphTransformer(llm=self.__llm_gemini)
        elif ai_model.startswith("gpt") and not ai_model.startswith("gpt-oss"):
            # using open-api
            self.__llm_openai = ChatOpenAI(model_name=ai_model, temperature=0.0, openai_api_key=ai_api_key)
            self.__llm_transformer = LLMGraphTransformer(llm=self.__llm_openai)
        else:
            # using local llm model
            self.__llm_ollama = ChatOllama(model=ai_model, temperature=0.0)
            self.__llm_transformer = LLMGraphTransformer(llm=self.__llm_ollama)
        self.__chunk_size = chunk_size
        self.__overlap = overlap

    
    async def plain_text_2_graph(self, text: str) -> list[GraphDocument]:
        docs = [Document(page_content=text, metadata={"source": "report"})]
        documents: list[Document] = self.__split_plain_text_2_doc(docs)
        graph_documents: list[GraphDocument] = self.__llm_transformer.convert_to_graph_documents(documents)
        return graph_documents
    
    
    def __split_plain_text_2_doc(self, docs : Iterable[Document]) -> list[Document]:
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=self.__chunk_size,
            chunk_overlap=self.__overlap
        )
        return text_splitter.split_documents(docs)