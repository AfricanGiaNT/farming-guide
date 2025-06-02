import os
import logging
import openai
import faiss
import numpy as np
import pickle
from typing import Optional, List

from search import search_online
from database import log_query

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants
MAX_RETRIES = 3
CONFIDENCE_THRESHOLD = 0.7

# --- Constants for RAG --- 
FAISS_INDEX_PATH = "faiss_index.idx"
TEXT_CHUNKS_PATH = "text_chunks.pkl"
KNOWLEDGE_TOP_K = 3 # Number of top chunks to retrieve from PDF knowledge
# --- End Constants --- 

# --- Load RAG Knowledge Base --- 
faiss_index = None
text_chunks = None

def load_knowledge_base():
    global faiss_index, text_chunks
    try:
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(TEXT_CHUNKS_PATH):
            faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            with open(TEXT_CHUNKS_PATH, 'rb') as f:
                text_chunks = pickle.load(f)
            logger.info(f"Successfully loaded FAISS index ({faiss_index.ntotal} vectors) and text chunks.")
        else:
            logger.warning("FAISS index or text chunks file not found. PDF knowledge base will be unavailable.")
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        faiss_index = None
        text_chunks = None

# Call load_knowledge_base on module import (application startup)
load_knowledge_base()
# --- End Load RAG --- 

def get_embedding_for_query(text, model="text-embedding-ada-002"):
    """Generates embedding for a single query string."""
    try:
        res = openai.Embedding.create(input=[text], engine=model)
        return res['data'][0]['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding for query: {e}")
        return None

def retrieve_from_pdf_knowledge(query_text: str, top_k: int = KNOWLEDGE_TOP_K) -> List[str]:
    """Retrieves top_k relevant text chunks from the PDF knowledge base."""
    if not faiss_index or not text_chunks:
        logger.warning("Attempted to retrieve from PDF knowledge, but index or chunks are not loaded.")
        return []
    
    query_embedding = get_embedding_for_query(query_text)
    if query_embedding is None:
        return []
    
    query_embedding_np = np.array([query_embedding]).astype('float32')
    
    try:
        distances, indices = faiss_index.search(query_embedding_np, top_k)
        retrieved_chunks = [text_chunks[i] for i in indices[0] if i < len(text_chunks)]
        # Log distances for diagnostics if needed: logger.debug(f"Distances: {distances[0]}, Indices: {indices[0]}")
        return retrieved_chunks
    except Exception as e:
        logger.error(f"Error searching FAISS index: {e}")
        return []

def preprocess_query(query: str) -> str:
    """Clean and standardize the query"""
    query = ' '.join(query.split())
    query_lower = query.lower()
    if 'malawi' not in query_lower and 'lilongwe' not in query_lower:
        query = f"{query} (for Lilongwe, Malawi context)"
    return query

def generate_response(prompt: str, temperature: float = 0.7) -> str:
    """Generate response using OpenAI GPT"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert agricultural advisor specializing in farming practices "
                        "in Lilongwe, Malawi. Provide practical, actionable advice considering the "
                        "local climate, soil conditions, and common farming practices. Use simple "
                        "language and include specific timing, techniques, and local considerations. "
                        "Format responses with bullet points and emojis where appropriate. "
                        "Base your answer primarily on the provided context from documents. If the context is insufficient, say so."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=700, # Increased slightly for potentially more context
            temperature=temperature,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        return response.choices[0].message.content.strip()
    except openai.error.RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        return "⚠️ Service is currently busy. Please try again in a few moments."
    except openai.error.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "⚠️ AI service temporarily unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return None # Changed from error string to None to allow fallback logic

def format_response_with_source(response: str, source: str) -> str:
    source_emoji = {
        "pdf_knowledge": "📚",
        "online_search": "🌐", 
        "ai_fallback": "🤖"
    }
    emoji = source_emoji.get(source, "ℹ️")
    if "Source:" in response:
        return response
    return f"{response}\n\n{emoji} Source: {source.replace('_', ' ').title()}"

def process_query(query: str) -> str:
    logger.info(f"Processing query: {query}")
    processed_query = preprocess_query(query)
    final_response = None
    source_used = "ai_fallback" # Default source

    # Step 1: Retrieve from PDF Knowledge Base
    logger.info(f"Attempting to retrieve context from PDF knowledge base for: {processed_query}")
    pdf_context_chunks = retrieve_from_pdf_knowledge(processed_query)
    
    context_for_llm = ""
    if pdf_context_chunks:
        context_for_llm = "\n\nContext from documents:\n" + "\n---\n".join(pdf_context_chunks)
        logger.info(f"Retrieved {len(pdf_context_chunks)} chunks from PDF knowledge.")
        source_used = "pdf_knowledge"
    else:
        logger.info("No relevant context found in PDF knowledge base.")

    # Step 2: (Optional) Online Search if PDF context is weak or as supplement
    # For now, let's always try online search and append, or use if PDF context is empty
    online_search_results = search_online(processed_query)
    if online_search_results and online_search_results != "No information found":
        context_for_llm += "\n\nContext from online search:\n" + online_search_results
        logger.info("Added context from online search.")
        if source_used == "pdf_knowledge":
            source_used = "pdf_knowledge_and_online"
        else:
            source_used = "online_search"
    else:
        logger.info("No additional information found from online search or search was skipped.")

    # Step 3: Generate AI response based on available context
    if context_for_llm:
        prompt = f"User question: '{query}'\n{context_for_llm}\n\nBased on the provided context, please answer the user's question. If the context is insufficient to answer the question fully, state that and provide any general advice you can."
        logger.info("Generating AI response using retrieved context.")
        ai_response = generate_response(prompt, temperature=0.5)
        if ai_response:
            final_response = ai_response
            # No save_to_db for RAG, as answers are dynamic. Logging is still useful.
            log_query(query, source_used)
        else:
            logger.warning("AI generation failed even with context.")
    
    # Step 4: Fallback to pure AI generation if no context and no response yet
    if not final_response:
        logger.info("No context available or previous AI generation failed. Falling back to pure AI generation.")
        fallback_prompt = f"""Provide agricultural advice for this question: '{query}'
    
        Focus on:
        - Practical advice for small-scale farmers in Lilongwe, Malawi
        - Consider local climate (subtropical highland, rainy season Nov-Apr)
        - Common crops: maize, tobacco, groundnuts, beans, vegetables
        - Local challenges: soil fertility, water management, pest control
        
        If you're not certain about specific details for Lilongwe, provide general best practices
        that would apply to similar climates and clearly indicate what farmers should verify locally."""
        ai_response = generate_response(fallback_prompt, temperature=0.6)
        if ai_response:
            final_response = ai_response + "\n\n💡 Tip: For the most specific advice, also consult local agricultural extension officers. This answer is based on general knowledge."
            source_used = "ai_fallback"
            log_query(query, source_used)
        else:
            logger.error("Pure AI fallback generation also failed.")

    if final_response:
        return format_response_with_source(final_response, source_used)
    else:
        # Absolute fallback message
        return (
            "�� I apologize, but I'm having trouble processing your request at the moment. "
            "Please try rephrasing your question or contact local agricultural extension services "
            "for immediate assistance.\n\n"
            "📞 Lilongwe ADD: +265 1 754 244 (example number)"
        )

# Reminder: Ensure .env has OPENAI_API_KEY
# If you decide to use the old search_db or save_to_db, uncomment their imports and usage. 