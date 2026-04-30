import os
import logging
from dotenv import load_dotenv

from knowledge.embedder import Embedder
from knowledge.vector_store import VectorStore
from tools.file_tools import FileTools
from tools.rag_tool import RAGTool
from tools.mysql_tool import MySQLTool
from db.mysql_client import get_db_client_from_env

from tools.executor import ToolExecutor
from agent.model_client import OllamaClient
from agent.controller import AgentController

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/agent.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)

    print("Initializing local agent components...")
    logger.info("Starting initialization of local agent components.")

    try:
        embedder = Embedder()
        chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        vectorstore = VectorStore(persist_dir=chroma_dir, embedder=embedder)

        file_tools = FileTools()
        rag_tool = RAGTool(embedder=embedder, vector_store=vectorstore)

        mysql_client = get_db_client_from_env()
        mysql_tool = MySQLTool(mysql_client=mysql_client) if mysql_client else None

        tool_executor = ToolExecutor(
            file_tools=file_tools,
            rag_tool=rag_tool,
            mysql_tool=mysql_tool
            )
        
        model_client = OllamaClient()

        agent_controller = AgentController(
            model_client=model_client,
            tool_executor=tool_executor,
            max_iterations=10
        )
        logger.info("Initialization completed successfully. Local agent is ready to receive user input.")

        print("Local agent initialized. Input '.exit' or '.quit' to exit.")

        while True:
            user_input = input("\nUser: ")

            if not user_input.strip():
                print("Please enter a valid question or command.")
                continue
            if user_input.strip().lower() in {".exit", ".quit"}:
                print("Exiting local agent. Goodbye!")
                break

            print("Agent is thinking...")

            answer = agent_controller.run(user_input=user_input)
            print(f"\nAgent: {answer}")
        
    except Exception as e:
        logger.critical("A critical error occurred during agent initialization or execution.", exc_info=True)
        print(f"An critical error occurred: {str(e)}. Check logs for details.")
        print(f"Find details in logs/agent.log")

if __name__ == "__main__":
    main()