import os
import PyPDF2
import faiss
import numpy as np
import openai
import pickle
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables (for OpenAI API key)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

PDF_DIR = "knowledge_base_pdfs"
FAISS_INDEX_PATH = "faiss_index.idx"
TEXT_CHUNKS_PATH = "text_chunks.pkl"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 100 # Characters of overlap between chunks

def get_pdf_text(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or "" # Add empty string if extract_text returns None
        logger.info(f"Successfully extracted text from: {pdf_path}")
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
    return text

def get_text_chunks(text):
    """Splits text into overlapping chunks."""
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunks.append(text[i:i + CHUNK_SIZE])
    return chunks

def get_embeddings(texts, model="text-embedding-ada-002"):
    """Generates embeddings for a list of texts using OpenAI.
    Handles potential API errors and returns None for failed embeddings.
    """
    embeddings_list = []
    for i in range(0, len(texts), 20): # Process in batches of 20 to stay within API limits if many chunks
        batch_texts = texts[i:i+20]
        try:
            res = openai.Embedding.create(input=batch_texts, engine=model)
            embeddings_list.extend([r['embedding'] for r in res['data']])
        except openai.error.RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit, consider retrying later or reducing batch size: {e}")
            # Pad with Nones for failed embeddings in this batch
            embeddings_list.extend([None] * len(batch_texts))
            break # Stop processing further batches on rate limit
        except Exception as e:
            logger.error(f"Error generating embeddings for a batch: {e}")
            # Pad with Nones for failed embeddings in this batch
            embeddings_list.extend([None] * len(batch_texts))
    return embeddings_list

def main():
    logger.info("Starting knowledge base indexing process...")
    all_text_chunks = []
    all_embeddings = []
    
    if not os.path.exists(PDF_DIR) or not os.listdir(PDF_DIR):
        logger.warning(f"PDF directory '{PDF_DIR}' is empty or does not exist. No index will be built.")
        return

    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(PDF_DIR, filename)
            logger.info(f"Processing PDF: {pdf_path}")
            
            raw_text = get_pdf_text(pdf_path)
            if not raw_text:
                logger.warning(f"No text extracted from {pdf_path}. Skipping.")
                continue
                
            chunks = get_text_chunks(raw_text)
            if not chunks:
                logger.warning(f"No chunks created from {pdf_path}. Skipping.")
                continue

            logger.info(f"Generated {len(chunks)} chunks from {pdf_path}.")
            
            embeddings = get_embeddings(chunks)
            
            # Filter out chunks for which embedding generation failed
            valid_embeddings = []
            valid_chunks = []
            for i, emb in enumerate(embeddings):
                if emb is not None:
                    valid_embeddings.append(emb)
                    valid_chunks.append(chunks[i])
                else:
                    logger.warning(f"Skipping chunk {i} from {pdf_path} due to embedding failure.")

            if not valid_embeddings:
                logger.warning(f"No valid embeddings generated for {pdf_path}. Skipping.")
                continue

            all_text_chunks.extend(valid_chunks)
            all_embeddings.extend(valid_embeddings)
            logger.info(f"Generated {len(valid_embeddings)} embeddings for {pdf_path}.")

    if not all_embeddings:
        logger.error("No embeddings were generated from any PDF. Index building aborted.")
        return

    embeddings_np = np.array(all_embeddings).astype('float32')
    
    # Dimension of embeddings (e.g., 1536 for text-embedding-ada-002)
    d = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)
    
    logger.info(f"FAISS index built successfully with {index.ntotal} vectors.")
    
    # Save FAISS index and text chunks
    faiss.write_index(index, FAISS_INDEX_PATH)
    logger.info(f"FAISS index saved to {FAISS_INDEX_PATH}")
    
    with open(TEXT_CHUNKS_PATH, 'wb') as f:
        pickle.dump(all_text_chunks, f)
    logger.info(f"Text chunks saved to {TEXT_CHUNKS_PATH}")
    
    logger.info("Knowledge base indexing process completed.")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Cannot generate embeddings.")
    else:
        main() 