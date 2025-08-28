"""_summary_
This module defines the GraphAIAgent class, which provides an interface to interact with AI models.
It also interacts with vector store and a Neo4j graph database.
It allows for the conversion of plain text reports into graph documents,
and enables querying the graph database using natural language questions.
"""

from typing import Iterable, Any
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_community.graphs.graph_document import GraphDocument as CommunityGraphDocument
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import SearchType, remove_lucene_chars
from langchain_neo4j.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import AppConfig
from ai.ai_court import AICourt
from ai.output_format import EntitiesFromQuestion
from ai.prompt import (
    STAGE_0_SYSTEM_PROMPT,
    STAGE_0_HUMAN_PROMPT,
    STAGE_1_SYSTEM_PROMPT,
    STAGE_1_HUMAN_PROMPT,
    QUESTION_PROMPT_HUMAN,
    QUESTION_PROMPT_SYSTEM,
    KNOWLEDGE_GRAPH_QUERY,
    RAG_PROMPT_SYSTEM_DEFENSIVE,
    RAG_PROMPT_SYSTEM_PROSECUTIVE,
    RAG_PROMPT_HUMAN,
    RAG_PROMPT_SYSTEM_REFEREE,
    RAG_PROMPT_HUMAN_REFEREE,
    CHAT_PROMPT_HUMAN,
    CHAT_PROMPT_SYSTEM,
)


class GraphAIAgent:
    """_summary_
    GraphAIAgent is a class that provides an interface\
        to interact with AI models and Neo4j graph database.
    It allows for the conversion of plain text reports into graph documents,\
        and enables querying the graph database
    using natural language questions. The class supports various AI models\
        including Google Gemini, OpenAI, and Ollama.
    It handles the initialization of the AI model, graph connection,\
        and vector store for document retrieval.

    Raises:
        ValueError: logger: when logger is not provided
        ValueError: app_config: when app_config is not provided
        ValueError: ai_config: when AI configuration is not provided
        ValueError: graph_config: when graph session configuration is not provided
        Exception: llm: when there is an error initializing the AI model or graph connection
    """
    __logger: Any
    __llm: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama
    __llm_transformer: LLMGraphTransformer
    __graph: Neo4jGraph
    __vector_index: Neo4jVector
    __vectorstore_retrieval: VectorStoreRetriever
    # __graph_driver: Driver
    __chunk_size: int
    __overlap: int

    def __init__(self,
                 logger: Any,
                 app_config: AppConfig | None = None):
        """Initialize the GraphAIAgent with the specified AI model and configuration."""

        try:
            self.__logger = logger
            if not logger:
                raise ValueError("Logger must be provided for GraphAIAgent initialization.")
            if app_config is None:
                raise ValueError("app_config must be provided for AI model initialization.")

            ai_config = app_config.get_ai_config()
            graph_config = app_config.get_graph_session_config()

            if not ai_config:
                raise ValueError("AI configuration is required for AI model initialization.")
            if not graph_config:
                raise ValueError(
                    "Graph session configuration is required for Neo4j connection."
                )

            self.__chunk_size = ai_config["chunk_size"]
            self.__overlap = ai_config["overlap"]
            ai_model:str = ai_config["model"]

            self.__logger.info("Initializing GraphAIAgent with AI model and configuration.")

            if ai_model.startswith("gemini"):
                self.__logger.info("Using Google Gemini API for LLM.")
                # using google-gemini-api
                self.__llm = ChatGoogleGenerativeAI(
                    model=ai_model,
                    temperature=0.0,
                    google_api_key=app_config.get_ai_api_key(),
                )
                self.__llm_transformer = LLMGraphTransformer(llm=self.__llm)

                # instance to vectorize the documents using Google Generative AI embeddings
                self.__vector_index = Neo4jVector.from_existing_graph(
                    GoogleGenerativeAIEmbeddings(
                        model="models/text-embedding-004",
                        google_api_key=app_config.get_ai_api_key()
                    ),
                    search_type=SearchType.HYBRID,
                    node_label="Document",
                    text_node_properties=["text"],
                    embedding_node_property="embedding",
                    username=app_config.neo4j_user,
                    password=app_config.get_neo4j_password().get_secret_value(),
                    url=f"bolt://{app_config.neo4j_uri}:7687",
                )
                self.__logger.info("Google Gemini API initialized successfully.")

            elif ai_model.startswith("gpt") and not ai_model.startswith("gpt-oss"):
                self.__logger.info("Using OpenAI API for LLM.")
                # using openai api
                self.__llm = ChatOpenAI(
                    model=ai_model, temperature=0.0, api_key=app_config.get_ai_api_key()
                )
                self.__llm_transformer = LLMGraphTransformer(llm=self.__llm)

                # instance to vectorize the documents using OpenAI embeddings
                self.__vector_index = Neo4jVector.from_existing_graph(
                    OpenAIEmbeddings(
                        model="text-embedding-ada-002",
                        api_key=app_config.get_ai_api_key()
                    ),
                    search_type=SearchType.HYBRID,
                    node_label="Document",
                    text_node_properties=["text"],
                    embedding_node_property="embedding",
                    username=app_config.neo4j_user,
                    password=app_config.get_neo4j_password().get_secret_value(),
                    url=f"bolt://{app_config.neo4j_uri}:7687",
                )
                self.__logger.info("OpenAI API initialized successfully.")
            else:
                self.__logger.info("Using Ollama API for LLM.")
                # using local llm model
                self.__llm = ChatOllama(
                    model=ai_model, temperature=0.0, disable_streaming=False
                )
                self.__llm_transformer = LLMGraphTransformer(llm=self.__llm)

                # instance to vectorize the documents using Ollama embeddings
                self.__vector_index = Neo4jVector.from_existing_graph(
                    OllamaEmbeddings(
                        model="all-minilm:22m"
                        ),
                    search_type=SearchType.HYBRID,
                    node_label="Document",
                    text_node_properties=["text"],
                    embedding_node_property="embedding",
                    username=app_config.neo4j_user,
                    password=app_config.get_neo4j_password().get_secret_value(),
                    url=f"bolt://{app_config.neo4j_uri}:7687",
                )
                self.__logger.info("Ollama API initialized successfully.")

            self.__vectorstore_retrieval: VectorStoreRetriever = self.__vector_index.as_retriever()

            self.__logger.info("Initializing Neo4j graph connection for ai agent.")
            # Initialize the Neo4j graph connection
            self.__graph = Neo4jGraph(
                url=f"bolt://{graph_config['uri']}:7687",
                username=graph_config["user"],
                password=app_config.get_neo4j_password().get_secret_value()
            )
            self.__logger.info("Neo4j graph connection initialized successfully.")

            self.__logger.info("Initializing GraphAIAgent complete.")
        except Exception as e:
            self.__logger.error(f"Error initializing GraphAIAgent: {e}")
            raise e

    def __del__(self):
        """Destructor to close the Neo4j graph connection."""
        if self.__graph:
            self.__logger.info("Closing Neo4j graph connection.")
            self.__graph.close()
            self.__logger.info("Neo4j graph connection closed.")


    async def post_report_to_graph(self, text: str):
        """Convert plain text to graph documents."""
        if not text:
            raise ValueError("Input text cannot be empty.")

        # first convert the report to a common behavior report.
        common_report = self.__convert_report_to_common__behavior_report(text)

        # Unify entities using to lower.
        unified_common_report = common_report.lower()

        print(f"Converted common report: {unified_common_report}")

        return unified_common_report

        # then convert the common report to graph documents
        # docs = [Document(page_content=text, metadata={"source": "report"})]
        # documents: list[Document] = self.__split_plain_text_2_doc(docs)

        docs = [Document(page_content=unified_common_report, metadata={"source": "report"})]
        documents: list[Document] = self.__split_plain_text_2_doc(docs)

        community_graph_documents: list[CommunityGraphDocument] = (
            self.__llm_transformer.convert_to_graph_documents(documents)
        )

        graph_documents = [self.__to_neo4j_graph_doc(cdoc) for cdoc in community_graph_documents]

        ## upsert graph documents into Neo4j
        if graph_documents:
            self.__graph.add_graph_documents(
                graph_documents,
                baseEntityLabel=True,
                include_source=True,
            )
        return unified_common_report

    async def analyze_behavior_with_ai(self, question: str) -> dict:
        """Analyze behavior with AI using the provided question."""
        if not question:
            raise ValueError("Question cannot be empty.")

        generated_response = self.__full_retriever(question)

        defensive_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(RAG_PROMPT_SYSTEM_DEFENSIVE)),
            ("human", RAG_PROMPT_HUMAN)
        ])

        prosecutive_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(RAG_PROMPT_SYSTEM_PROSECUTIVE)),
            ("human", RAG_PROMPT_HUMAN)
        ])
        defensive_rag_chain: RunnableSerializable = (
            defensive_prompt
            | self.__llm
            | StrOutputParser()
        )
        prosecutive_rag_chain: RunnableSerializable = (
            prosecutive_prompt
            | self.__llm
            | StrOutputParser()
        )
        referee_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(RAG_PROMPT_SYSTEM_REFEREE)),
            ("human", RAG_PROMPT_HUMAN_REFEREE)
        ])
        defensive_result = defensive_rag_chain.invoke({
            "context": generated_response,
            "question": question,
        })
        prosecutive_result = prosecutive_rag_chain.invoke({
            "context": generated_response,
            "question": question,
        })
        referee_chain: RunnableSerializable = (
            referee_prompt
            | self.__llm
            | StrOutputParser()
        )
        result = referee_chain.invoke({
            "defense": defensive_result,
            "prosecution": prosecutive_result,
            "context": generated_response,
            "question": question,
        })

        # print all the intermediate results with json format
        return {
            "defense": defensive_result,
            "prosecution": prosecutive_result,
            "final_verdict": result
        }
        
    async def chat_with_ai(self, question: str) -> dict:
        """Chat with the AI model using the provided question."""
        if not question:
            raise ValueError("Question cannot be empty.")

        generated_response = self.__full_retriever(question)

        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(CHAT_PROMPT_SYSTEM)),
            ("human", CHAT_PROMPT_HUMAN)
        ])

        rag_chain: RunnableSerializable = (
            rag_prompt
            | self.__llm
            | StrOutputParser()
        )

        result = rag_chain.invoke({
            "context": generated_response,
            "question": question,
        })

        # print all the intermediate results with json format
        return {
            "answer": result
        }

    def __split_plain_text_2_doc(self, docs: Iterable[Document]) -> list[Document]:
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=self.__chunk_size, chunk_overlap=self.__overlap
        )
        return text_splitter.split_documents(docs)

    def __to_neo4j_graph_doc(self, cdoc: CommunityGraphDocument) -> GraphDocument:
        # Convert community nodes to neo4j nodes
        neo4j_nodes = [
            Node(
                # unify the node id is lower case
                id=self.__unify_entity_node_id(node.id),
                type=node.type,
                properties=node.properties
            )
            for node in cdoc.nodes
        ]
        neo4j_relationships = [
            Relationship(
                # unify the relationship id is lower case
                source=Node(
                    id=self.__unify_entity_node_id(rel.source.id),
                    type=rel.source.type,
                    properties=rel.source.properties
                ),
                target=Node(
                    id=self.__unify_entity_node_id(rel.target.id),
                    type=rel.target.type,
                    properties=rel.target.properties
                ),
                type=remove_lucene_chars(rel.type),
                properties=rel.properties,
            )
            for rel in cdoc.relationships
        ]
        return GraphDocument(
            nodes=neo4j_nodes,
            relationships=neo4j_relationships,
            source=cdoc.source,
        )

    def __unify_entity_node_id(self, node_id: str|int)->str|int:
        """
        Unify the node id to lower case if it is a string.
        Also, Activate a disabled URL
        """
        if isinstance(node_id, str):
            unified_id = self.__unify_entity(node_id)
            # Activate a disabled URL
            unified_id = unified_id.replace("[.]", ".")
            return unified_id
        return node_id

    def __unify_entity(self, entity: str) -> str:
        """Unify the entity to lower case."""
        return entity.strip().lower()

    def __convert_report_to_common__behavior_report(self, text: str) -> str:
        """Chat with the AI model using the provided messages."""

        # stage_0_prompt = ChatPromptTemplate.from_messages([
        #     ("system", STAGE_0_SYSTEM_PROMPT),
        #     ("human", STAGE_0_HUMAN_PROMPT)
        # ])

        # overview_chain = stage_0_prompt | self.__llm | StrOutputParser()

        # stage_1_prompt = ChatPromptTemplate.from_messages([
        #     ("system", STAGE_1_SYSTEM_PROMPT),
        #     ("human", STAGE_1_HUMAN_PROMPT)
        # ])

        # indicate_chain = stage_1_prompt | self.__llm | StrOutputParser()

        # indicate_entities = indicate_chain.invoke({
        #     "report_text": text,
        # })

        # overview_entities = overview_chain.invoke({
        #     "report_text": text,
        # })
        
        court = AICourt(
            self.__llm,
            3,
            (
                STAGE_1_SYSTEM_PROMPT,
                STAGE_1_HUMAN_PROMPT
            ),
            (
                STAGE_1_SYSTEM_PROMPT,
                STAGE_1_HUMAN_PROMPT
            ),
            (
                STAGE_1_SYSTEM_PROMPT,
                STAGE_1_HUMAN_PROMPT
            ),
        )

        refined_report = court.debate({
            "report_text": text,
        })

        # ## Combine the overview and indicate entities into a single output
        # refined_report = overview_entities + "\n\n" + indicate_entities

        return refined_report

    def __graph_retriever(self, question: str)->str:
        """Retrieve relevant information from the graph based on the question."""
        result:str = ""
        # Extract entities from the question
        question_prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_PROMPT_SYSTEM),
            ("human", QUESTION_PROMPT_HUMAN)
        ])
        question_chain = question_prompt | self.__llm.with_structured_output(EntitiesFromQuestion)
        extracted = question_chain.invoke({"question": question})
        # Check generated response is valid
        if not extracted \
            or not isinstance(extracted, EntitiesFromQuestion) \
            or not extracted.entities:
            self.__logger.warning("No entities extracted from the question.")
            return result
        # trim the additional spaces and only keep the first word if multiple words
        extracted.entities = [self.__unify_entity(e) for e in extracted.entities if e]
        self.__logger.info(f"Extracted entities from question: {extracted.entities}")
        for entity in extracted.entities:
            response = self.__graph.query(
                KNOWLEDGE_GRAPH_QUERY,
                {"id": entity}
            )
            if response:
                result += "\n".join([r['OUTPUT'] for r in response])
        self.__logger.info(f"Graph retrieval result: {result}")
        return result

    def __full_retriever(self, question: str):
        graph_data = self.__graph_retriever(question)
        if graph_data == "":
            graph_data = "No relevant graph data found."
        vector_data = [doc.page_content for doc in self.__vectorstore_retrieval.invoke(question)]
        combined_data = f"""\
Graph Data:
{graph_data}
Vector Data:
{"#Document ".join(vector_data)}
        """
        return combined_data


    def __escape_braces(self, s: str) -> str:
        s = s.replace("{", "{{").replace("}", "}}")
        return s
