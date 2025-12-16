# ---

**RAG Architecture: LiteLLM vs. LangChain Chat Models**

Date: December 17, 2025
Topic: Selecting the Generation Method for RAG Implementation
Context: Comparing direct LangChain Chat Models against LiteLLM, and implementing Memory/History in a hybrid setup.

## ---

**1\. Executive Summary**

When building Retrieval-Augmented Generation (RAG) pipelines, the choice between **LiteLLM** and **LangChain Chat Models** is often misunderstood. They are not mutually exclusive alternatives, but rather complementary layers of the stack.

* **LiteLLM** is an **I/O & Reliability Layer**. It acts as a universal proxy to standardize API calls, handle errors, and manage costs across 100+ providers.
* **LangChain Chat Models** are an **Orchestration Layer**. They provide the framework (Runnable interface) to connect models with vector stores, memory, and tools.

**Best Practice:** The most robust architecture uses **LiteLLM wrapped inside LangChain**.

## ---

**2\. Detailed Comparison**

| Feature | LiteLLM | LangChain Chat Models |
| :---- | :---- | :---- |
| **Primary Function** | **Model Gateway / Proxy** | **Application Framework** |
| **Role in RAG** | Ensures the API call succeeds. Handles rate limits, fallbacks, and cost tracking. | Orchestrates the flow: Retrieval $\\to$ Prompt $\\to$ Generation $\\to$ Parser. |
| **Interchangeability** | **High.** Switch from OpenAI to Vertex/Anthropic by changing one string. | **Medium.** Requires changing class imports (e.g., ChatOpenAI to ChatAnthropic) unless using wrappers. |
| **Error Handling** | **Excellent.** Built-in logic for retries, timeouts, and model fallbacks. | Basic. Relies mostly on the underlying provider's SDK or manual logic. |
| **Standardization** | Normalizes inputs/outputs to OpenAI format for all providers. | Normalizes interaction patterns (invoke, stream, batch) for application logic. |

### **The "Hybrid" Approach (Recommended)**

By using the ChatLiteLLM class within LangChain, you gain the orchestration powers of LangChain (chains, memory, retrievers) backed by the reliability infrastructure of LiteLLM (fallbacks, routing, unified API keys).

## ---

**3\. Implementation Guide**

### **A. Prerequisites**

Bash

pip install langchain langchain-community langchain-openai litellm chromadb

### **B. Basic Setup (The Hybrid Model)**

Instead of importing ChatOpenAI, we import ChatLiteLLM from the community package.

Python

from langchain\_community.chat\_models import ChatLiteLLM
from langchain\_core.prompts import ChatPromptTemplate

\# Initialize the model with LiteLLM features
chat\_model \= ChatLiteLLM(
    model="gpt-4o",          \# Primary model
    temperature=0,
    max\_tokens=500,
    \# LiteLLM specific: Automatic fallback if GPT-4 fails
    fallbacks=\["claude-3-sonnet", "gpt-3.5-turbo"\]
)

\# Use standard LangChain prompting
prompt \= ChatPromptTemplate.from\_template("Tell me a joke about {topic}")
chain \= prompt | chat\_model

\# Execution
response \= chain.invoke({"topic": "AI engineers"})
print(response.content)

## ---

**4\. Implementing Memory (Chat History)**

In RAG, memory is critical for follow-up questions. Since ChatLiteLLM adheres to the LangChain Runnable interface, we use standard LangChain memory tools.

### **A. The Challenge with RAG Memory**

You cannot simply inject chat history into the final prompt.

1. **User:** "Who is the CEO of Apple?" \-\> **RAG:** Retrieves Tim Cook docs.
2. **User:** "How old is he?" \-\> **RAG:** Searches for "How old is he?". **Fails.**

**Solution:** You need a **History-Aware Retriever**. This step uses an LLM to rewrite the query ("How old is Tim Cook?") *before* searching the vector database.

### **B. Full Code Example: RAG with Memory & LiteLLM**

This example demonstrates a production-ready setup where LiteLLM handles both the query rewriting (cheap model) and final answer generation (smart model).

Python

import os
from langchain\_community.chat\_models import ChatLiteLLM
from langchain\_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create\_history\_aware\_retriever, create\_retrieval\_chain
from langchain.chains.combine\_documents import create\_stuff\_documents\_chain
from langchain\_community.vectorstores import Chroma
from langchain\_openai import OpenAIEmbeddings
from langchain\_core.runnables.history import RunnableWithMessageHistory
from langchain\_community.chat\_message\_histories import ChatMessageHistory

\# \--- 1\. Setup Models via LiteLLM \---

\# Model A: Fast/Cheap model for Query Rewriting
rewriter\_llm \= ChatLiteLLM(model="gpt-3.5-turbo", temperature=0)

\# Model B: Smart model for Final Answer Generation
generator\_llm \= ChatLiteLLM(model="gpt-4o", temperature=0)

\# \--- 2\. Setup Vector Store (Mock) \---
\# In production, connect to your actual Pinecone/Milvus/Pgvector instance
embeddings \= OpenAIEmbeddings()
vectorstore \= Chroma.from\_texts(
    \["LiteLLM is a proxy server for LLMs.", "LangChain is a framework for LLM apps."\],
    embedding=embeddings
)
retriever \= vectorstore.as\_retriever()

\# \--- 3\. Create History-Aware Retriever \---
\# This chain rewrites the user query to be standalone
contextualize\_system\_prompt \= (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize\_prompt \= ChatPromptTemplate.from\_messages(\[
    ("system", contextualize\_system\_prompt),
    MessagesPlaceholder("chat\_history"),
    ("human", "{input}"),
\])

\# Uses the cheap 'rewriter\_llm'
history\_aware\_retriever \= create\_history\_aware\_retriever(
    rewriter\_llm, retriever, contextualize\_prompt
)

\# \--- 4\. Create the QA Chain \---
\# This chain actually answers the question using retrieved docs
qa\_system\_prompt \= (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise.\\n\\n"
    "{context}"
)

qa\_prompt \= ChatPromptTemplate.from\_messages(\[
    ("system", qa\_system\_prompt),
    MessagesPlaceholder("chat\_history"),
    ("human", "{input}"),
\])

\# Uses the smart 'generator\_llm'
question\_answer\_chain \= create\_stuff\_documents\_chain(generator\_llm, qa\_prompt)

\# \--- 5\. Combine into Final RAG Chain \---
rag\_chain \= create\_retrieval\_chain(history\_aware\_retriever, question\_answer\_chain)

\# \--- 6\. Manage State (Session History) \---
store \= {}

def get\_session\_history(session\_id: str):
    if session\_id not in store:
        store\[session\_id\] \= ChatMessageHistory()
    return store\[session\_id\]

conversational\_rag\_chain \= RunnableWithMessageHistory(
    rag\_chain,
    get\_session\_history,
    input\_messages\_key="input",
    history\_messages\_key="chat\_history",
    output\_messages\_key="answer",
)

\# \--- 7\. Usage \---
\# Turn 1
response1 \= conversational\_rag\_chain.invoke(
    {"input": "What is LiteLLM?"},
    config={"configurable": {"session\_id": "user\_1"}}
)
print(f"AI: {response1\['answer'\]}")

\# Turn 2 (Testing Memory context)
response2 \= conversational\_rag\_chain.invoke(
    {"input": "What is it a proxy for?"}, \# "it" refers to LiteLLM
    config={"configurable": {"session\_id": "user\_1"}}
)
print(f"AI: {response2\['answer'\]}")

## ---

**5\. Strategic Benefits of this Architecture**

1. **Cost Optimization:**
   * By splitting the rewriter\_llm and generator\_llm, you can use a cheap model (e.g., Haiku, GPT-3.5) for the mechanical task of rewriting queries, and only pay for the expensive model (GPT-4, Opus) when generating the final answer.12

2. **Resilience:34**

   * If OpenAI goes down, LiteLLM (in the background) can route traffic to Anthropic or Azure without the LangChain application code crashing.56

3. **Observability:7**

   * LangSmith (via LangChain)8 tracks the chain execution.

   * LiteLLM tracks the token spend and raw API latency.

## **6\. Conclusion**

For a production RAG system:

1. Use **LangChain** to define the *structure* (Chains, Memory, Retrievers).
2. Use **ChatLiteLLM** to define the *engine* (Model access, Fallbacks, Routing).

This combination provides the highest level of flexibility and reliability currently available in the LLM tech stack.

**Sources**
1\. [https://medium.com/@enricdomingo/deploy-a-streamlit-llm-app-on-azure-web-app-gpt-4o-azure-openai-and-sso-auth-b58d3095371d](https://medium.com/@enricdomingo/deploy-a-streamlit-llm-app-on-azure-web-app-gpt-4o-azure-openai-and-sso-auth-b58d3095371d)
2\. [https://muhammad--ehsan.medium.com/retrieval-augmented-generation-using-your-data-with-llms-81bce2c195ae](https://muhammad--ehsan.medium.com/retrieval-augmented-generation-using-your-data-with-llms-81bce2c195ae)
3\. [https://muhammad--ehsan.medium.com/retrieval-augmented-generation-using-your-data-with-llms-81bce2c195ae](https://muhammad--ehsan.medium.com/retrieval-augmented-generation-using-your-data-with-llms-81bce2c195ae)
4\. [https://medium.com/@sonali.chowdhury.2013/leveraging-llms-for-intelligent-information-access-97aaa8b16fa4](https://medium.com/@sonali.chowdhury.2013/leveraging-llms-for-intelligent-information-access-97aaa8b16fa4)
5\. [https://github.com/googleapis/langchain-google-alloydb-pg-python](https://github.com/googleapis/langchain-google-alloydb-pg-python)
6\. [https://github.com/googleapis/langchain-google-alloydb-pg-python](https://github.com/googleapis/langchain-google-alloydb-pg-python)
7\. [https://medium.com/feed/@vikrambhat2](https://medium.com/feed/@vikrambhat2)
8\. [https://medium.com/feed/@vikrambhat2](https://medium.com/feed/@vikrambhat2)
