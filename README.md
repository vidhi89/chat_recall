# ChatRecall

> **Search your chat by what you remember, not what was written.**

ChatRecall is a semantic search engine for messy group conversations.

Instead of requiring exact keywords, ChatRecall lets you search a group chat using the meaning of what you remember.

For example:

> **"Which room did everyone agree to use?"**

can retrieve:

> **"Let's do the seminar hall."**

even though the query and answer do not share the important words.

---

## Why ChatRecall?

Group chats are difficult to search.

People remember:

- what the group decided
- what a particular person said
- what happened around a certain time
- the general meaning of a conversation

But chat search usually depends heavily on exact words.

ChatRecall focuses on **semantic retrieval** and adds awareness of:

- conversation intent
- participants
- time ranges
- topics
- decisions
- surrounding conversation context

---

## Key Features

### Semantic Search

Find messages based on meaning rather than exact keyword matching.

### Decision-Aware Retrieval

Final decisions are ranked above long discussions and intermediate suggestions.

Examples:

- "Where did we finally decide to go?"
- "Which room did everyone agree to use?"
- "What technologies did we settle on?"

### Person-Aware Search

Search for what a particular participant said or asked.

Example:

> "What did Karan ask about the projector?"

### Time-Aware Search

Search within natural-language time ranges.

Example:

> "What did we discuss last month?"

### Conversation Context

Results include surrounding messages instead of displaying only an isolated matching message.

### Hinglish / Messy Chat

The synthetic corpus intentionally contains:

- Hinglish
- typos
- short replies
- emojis
- forwarded messages
- media placeholders
- informal conversation

---

## Architecture

```text
                         CHATRECALL
                             |
              +--------------+--------------+
              |                             |
          Frontend                       Backend
        HTML/CSS/JS                    FastAPI
              |                             |
              |                    +--------+--------+
              |                    |                 |
              |              Query Engine       Data Layer
              |                    |              chat.json
              |                    |
              |              Retrieval Engine
              |
              +----------- REST API -------------+

---

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/vidhi89/chat_recall.git
cd chat_recall