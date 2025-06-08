# Project Plan: Implement Message History

This document outlines the plan for implementing message history for the bot.

### 1. Analyze Existing Codebase
- **Goal:** Understand the current message processing flow.
- **Action:** Examine `ai_agent.py` and `main.py`.
- **Outcome:** A clear understanding of how to integrate the new feature.

### 2. Implement Message Store
- **Goal:** Create a mechanism to store conversation history.
- **Action:** Use a dictionary in `ai_agent.py` to store the last 10 messages for each `chat_id`.
- **Data Structure:** `{ "chat_id": [{"role": "user", "content": "..."}, ...] }`

### 3. Modify `AIAgent`
- **Goal:** Update the AI agent to handle conversation history.
- **Actions:**
    - Refactor `ai_agent.py` from functions to an `AIAgent` class.
    - The `__init__` method will initialize a dictionary to store conversations.
    - The `ask` method will:
        - Accept `query` and `chat_id`.
        - Retrieve and update the conversation history for the given `chat_id`.
        - Limit the history to the last 10 messages using `collections.deque(maxlen=10)`.
        - Pass the conversation history to the OpenAI API.
        - Store the assistant's response in the history.

### 4. Update `main.py`
- **Goal:** Adapt the main application to use the new `AIAgent`.
- **Actions:**
    - Instantiate `AIAgent` in `main.py`.
    - Pass the `chat_id` from the Telegram update to the `agent.ask()` method.

### 5. Update `test_bot.py`
- **Goal:** Ensure tests are up-to-date with the changes.
- **Actions:**
    - Modify `test_openai` and `test_query_processing` to use the new `AIAgent` class and its methods.
    - Use a dummy `chat_id` for testing purposes. 