import os
import logging
import openai
import faiss
import numpy as np
import pickle
from typing import Optional, List, Dict
from collections import deque

from search import search_online
from database import log_query

logger = logging.getLogger(__name__)

# No longer needed, will be handled by the client
# openai.api_key = os.getenv("OPENAI_API_KEY")

class AIAgent:
    def __init__(self):
        # Constants
        self.MAX_RETRIES = 3
        self.CONFIDENCE_THRESHOLD = 0.7
        # --- Constants for RAG ---
        self.FAISS_INDEX_PATH = "faiss_index.idx"
        self.TEXT_CHUNKS_PATH = "text_chunks.pkl"
        self.KNOWLEDGE_TOP_K = 3  # Number of top chunks to retrieve from PDF knowledge
        # --- End Constants ---
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.faiss_index = None
        self.text_chunks = None
        self.load_knowledge_base()
        self.conversations: Dict[str, deque] = {}

    def load_knowledge_base(self):
        try:
            if os.path.exists(self.FAISS_INDEX_PATH) and os.path.exists(self.TEXT_CHUNKS_PATH):
                self.faiss_index = faiss.read_index(self.FAISS_INDEX_PATH)
                with open(self.TEXT_CHUNKS_PATH, 'rb') as f:
                    self.text_chunks = pickle.load(f)
                logger.info(f"Successfully loaded FAISS index ({self.faiss_index.ntotal} vectors) and text chunks.")
            else:
                logger.warning("FAISS index or text chunks file not found. PDF knowledge base will be unavailable.")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.faiss_index = None
            self.text_chunks = None

    def get_embedding_for_query(self, text, model="text-embedding-ada-002"):
        """Generates embedding for a single query string."""
        try:
            res = self.client.embeddings.create(input=[text], model=model)
            return res.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding for query: {e}")
            return None

    def retrieve_from_pdf_knowledge(self, query_text: str, top_k: int = 3) -> List[str]:
        """Retrieves top_k relevant text chunks from the PDF knowledge base."""
        if not self.faiss_index or not self.text_chunks:
            logger.warning("Attempted to retrieve from PDF knowledge, but index or chunks are not loaded.")
            return []
        
        query_embedding = self.get_embedding_for_query(query_text)
        if query_embedding is None:
            return []
        
        query_embedding_np = np.array([query_embedding]).astype('float32')
        
        try:
            distances, indices = self.faiss_index.search(query_embedding_np, top_k)
            retrieved_chunks = [self.text_chunks[i] for i in indices[0] if i < len(self.text_chunks)]
            # Log distances for diagnostics if needed: logger.debug(f"Distances: {distances[0]}, Indices: {indices[0]}")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []

    def preprocess_query(self, query: str) -> str:
        """Clean and standardize the query"""
        query = ' '.join(query.split())
        query_lower = query.lower()
        if 'malawi' not in query_lower and 'lilongwe' not in query_lower:
            query = f"{query} (for Lilongwe, Malawi context)"
        return query

    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Generate response using OpenAI GPT"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=temperature,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            return "⚠️ Service is currently busy. Please try again in a few moments."
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "⚠️ AI service temporarily unavailable. Please try again later."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    def parse_answer_from_response(self, raw_response: str) -> str:
        """Extracts the content from between <answer> tags."""
        try:
            if "<answer>" in raw_response and "</answer>" in raw_response:
                start_tag = "<answer>"
                end_tag = "</answer>"
                start_index = raw_response.find(start_tag) + len(start_tag)
                end_index = raw_response.find(end_tag, start_index)
                # Remove the initial "Here's my advice..." part if it exists for cleaner output
                answer_content = raw_response[start_index:end_index].strip()
                if answer_content.lower().startswith("here's my advice for farming in lilongwe, malawi:"):
                    answer_content = answer_content[len("here's my advice for farming in lilongwe, malawi:"):].strip()
                return answer_content
            else:
                # Fallback if tags are missing, return the whole response
                return raw_response
        except Exception as e:
            logger.error(f"Failed to parse answer from response: {e}")
            return raw_response # Return raw response on parsing error

    def ask(self, query: str, chat_id: str) -> str:
        logger.info(f"Processing query for chat_id {chat_id}: {query}")

        if chat_id not in self.conversations:
            self.conversations[chat_id] = deque(maxlen=10)

        self.conversations[chat_id].append({"role": "user", "content": query})

        processed_query = self.preprocess_query(query)
        source_used = "ai_fallback"

        # Step 1: Retrieve context from PDFs and online search
        pdf_context_chunks = self.retrieve_from_pdf_knowledge(processed_query)
        online_search_results = search_online(processed_query)

        # Step 2: Construct the full context string
        pdf_context_str = ""
        if pdf_context_chunks:
            pdf_context_str = "PDF Document Context:\n" + "\n---\n".join(pdf_context_chunks)
            source_used = "pdf_knowledge"
        
        online_context_str = ""
        if online_search_results and online_search_results != "No information found":
            online_context_str = "Online Search Context:\n" + online_search_results
            source_used = "online_search" if source_used == "ai_fallback" else "pdf_and_online"

        full_context = f"{pdf_context_str}\n\n{online_context_str}".strip()
        if not full_context:
            full_context = "No context information was available."

        # Step 3: Populate the new prompt template
        prompt_template = """You are an expert agricultural advisor specializing in farming practices in Lilongwe, Malawi. Your task is to provide practical, actionable advice to farmers based on their questions, considering the local climate, soil conditions, and common farming practices in the area.

First, carefully read and analyze the following context information:

<context>
{{CONTEXT}}
</context>

Use this context as the primary source for your advice. Pay close attention to specific details about Lilongwe's climate, soil conditions, and local farming practices mentioned in the context.

When formulating your response:
1. Use simple, easy-to-understand language suitable for local farmers.
2. Include specific timing for agricultural activities when relevant.
3. Describe techniques in a step-by-step manner when appropriate.
4. Consider and mention local considerations that may affect farming practices.
5. Format your response using bullet points for clarity.
6. Use relevant emojis at the beginning of each bullet point to make the advice more engaging and easier to remember.

If the context does not provide sufficient information to answer the question confidently, state that the information is limited and provide a general response based on common agricultural practices, clearly indicating that it's not specific to Lilongwe.

Here is the farmer's question:

<question>
{{QUESTION}}
</question>

Please provide your expert advice in response to this question, following the guidelines above. Begin your response with "Here's my advice for farming in Lilongwe, Malawi:" and enclose your entire answer within <answer> tags."""
        
        system_prompt = prompt_template.replace("{{CONTEXT}}", full_context).replace("{{QUESTION}}", query)
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(list(self.conversations[chat_id]))

        # Step 4: Generate and parse the response
        logger.info("Generating AI response using new prompt template.")
        raw_response = self.generate_response(messages, temperature=0.2)

        final_response = None
        if raw_response:
            final_response = self.parse_answer_from_response(raw_response)
            log_query(query, source_used)
            self.conversations[chat_id].append({"role": "assistant", "content": final_response})
        else:
            logger.error("AI generation failed.")
            self.conversations[chat_id].append({"role": "assistant", "content": "AI generation failed."})


        # Step 5: Final fallback message
        if not final_response:
            final_response = (
                "🚫 I apologize, but I'm having trouble processing your request at the moment. "
                "Please try rephrasing your question or contact local agricultural extension services "
                "for immediate assistance."
            )
            self.conversations[chat_id].append({"role": "assistant", "content": final_response})


        return final_response

# Reminder: Ensure .env has OPENAI_API_KEY
# If you decide to use the old search_db or save_to_db, uncomment their imports and usage.
#
# process_query function has been replaced by the AIAgent class.
# You will need to instantiate the agent and call the `ask` method.
# e.g.
# agent = AIAgent()
# response = agent.ask("your query", "some_chat_id")
#
# All the helper functions have been moved into the AIAgent class.
# The global `faiss_index` and `text_chunks` are now instance variables.
# The loading of the knowledge base is done in the constructor.
# The `process_query` function is now the `ask` method of the `AIAgent` class.
# The `generate_response` function now takes a list of messages instead of a single prompt.
# A dictionary `self.conversations` is added to store conversation history for each chat_id.
# It uses a `deque` with `maxlen=10` to store the last 10 messages.

def process_query(query: str) -> str:
    # This function is now deprecated. Instantiate AIAgent and use the .ask() method.
    raise NotImplementedError("process_query is deprecated. Please use AIAgent().ask(query, chat_id)") 