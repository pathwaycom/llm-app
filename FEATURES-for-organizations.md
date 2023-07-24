# LLM App - Features for Organizations

![LLM App architecture diagram](https://github.com/pathwaycom/llm-app/assets/15914792/217b3687-6a30-4929-b378-41fcdd73a682)

This feature list is created to facilitate the launching of projects based on LLM App in discussions within larger teams.

## 1. Data Sources

Connects to AWS S3, Azure data lake storage, Google Cloud Storage.

Extend the application to connect to live data feeds (REST API’s, RSS, message queues).

## 2. Data Privacy

Purpose built for Data privacy so that you can use your own LLMs and embedding code.

Set-up allows to avoid any external API calls.

## 3. Indexing

Document pipeline tested for indexing large document sets - 100,000+.

Incremental Indexing - New documents are indexed without rebuilding the whole index ensuring index freshness.

Document base changes reflected in LLM answers with a latency between 100ms and 10s, depending on setup.

Support for distributed indexes with sharding.

Storage of feature indexes (in cold storage) for fault-tolerance and fast resume.

Indexing along with security context.

## 4. Vector Database capabilities

LLM App architecture relies on existing enterprise document storage - no disk copies are created, no vector database is needed.

Built-in in-memory vector index, scales automatically with query volumes, persisted to cold storage as needed.

Reduced infrastructure complexity and costs. Guaranteed synchronization with document corpus.

## 5. Document formats

CSV, JSON supported by standard connectors.

PDF, Doc, HTML, etc. can be imported using standard Python libraries.

## 6. Contextual augmentation with Enterprise data

Retrieved documents provide relevant context to improve LLM output. 

Contextual retrieval and selected index can be specific to querying user, etc.

Further augmentation can happen with database lookups and joining stream data. 

Late stage security augmentation is supported for restricting access for documents.

## 7. Document Retrieval

Index-based. Optimized approximate nearest neighbor search and customizable relevancy ranking enables sub-second retrieval of correct context information.

Contextual retrieval based on user roles.

## 8. Reduced hallucination

Grounding with enterprise documents, dynamic context building from existing enterprise data.

Custom prompts composed in Python.

## 9. Real-time queries

Sub-second end-to-end query with low retrieval latency with large indexes enables real-time experiences.

## 10. Developer capacity

Programmatically interface with the application (Python API) to describe LLM application architecture.

Interface with external API’s (use or provide).

Interface with file storage, batch, and enterprise streaming data sources.

## 11. Reduced dependencies

Runs on Pathway engine.

Connects to LLM model - on a local machine or via API (HuggingFace, OpenAI).

Relies on local Python libraries or API for document embedding.

Typically eliminates need for: vector databases (Pinecone/Weaviate), additional cache (Redis), typically eliminates need for Langchain.

## 12. Extensions: Features which can be added independently into the LLM App template by Developers

### Feedback loops

Analyze LLM responses to improve results quality over time.

Suggest questions based on user roles.

### LLMOps - Monitoring

Track query latency, precision/recall, index coverage and contextual retrieval quality, and document pipeline throughput.

### LLMOps - A/B testing

Experiment with different models, prompts, indexing methods.


