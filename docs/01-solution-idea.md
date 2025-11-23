I'm going to implement a knowledbase management application is RAG based that may have following requirements

RAG based with optional BM25 and graph based RAG, metadata search

backend: python or Golang, frontend nextJS/nodeJS

document storage: MinIO each Knowledge base in separate bucket

Database postgresql

Vector database: Qdrant

Can build from scratch base on: langgraph, llamaindex, google Agent Development Kit (ADK) or can leverage existing opensoure project in github, text splitter agent, embedder agent, retriever agent, document store management agent

can support: cloud base model OpenAI, Gemini, claude or local model in Ollama, LLM.cpp or other

Headless architecture, modulear or agent based, each agent responsible for one task: knowledbase management agent , user and RBAC management agent

API first with security: JWT, user authentication

Container based solution, all componebnt is opesource, community no commercial

Performance metrics , tracing, logs

knowledge base management: can manage multiple knowledge bases,

user management: users, roles, groups

users, group only can access to granted knowledge bases

use can chat with granted knowledge base,

system need to maintain user chat history

System with parameter and highly configurable

User with can upload document into knowledbase: single file or batch
you may consult https://github.com/infiniflow/ragflow/tree/main/docker for more information

please brainstorm to complete solution ideate
