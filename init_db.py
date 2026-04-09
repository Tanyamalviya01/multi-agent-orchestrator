import os
import sys
import time
from dotenv import load_dotenv

# The SQLite fix for Linux VMs
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def main():
    print("1. Loading the Tesla 10-K PDF...")
    loader = PyPDFLoader("tesla_10k.pdf") 
    pages = loader.load()
    print(f"Successfully loaded {len(pages)} pages.")

    print("2. Chopping the document into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(pages)
    print(f"Created {len(chunks)} searchable chunks.")

    print("3. Initializing Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    print("4. Saving to ChromaDB in batches to respect free tier limits...")
    # Initialize empty database
    vectorstore = Chroma(
        persist_directory="./chroma_data",
        embedding_function=embeddings
    )

    # Process in batches of 80 to stay under the 100/min limit
    batch_size = 80
    total_batches = (len(chunks) // batch_size) + 1

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        current_batch = (i // batch_size) + 1
        print(f"-> Processing batch {current_batch} of {total_batches}...")
        
        # Add the batch to the database
        vectorstore.add_documents(batch)
        
        # If there are still more chunks to process, wait 60 seconds
        if i + batch_size < len(chunks):
            print("   Waiting 60 seconds for the API rate limit to reset... (Do not close)")
            time.sleep(60)

    print("\nDATABASE READY! The AI has finished analyzing the document.")

if __name__ == "__main__":
    main()