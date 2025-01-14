# ChatBot with Neo4j Knowledge Graph and RAG System

A cutting-edge chatbot system that combines the power of Neo4j Knowledge Graphs and Retrieval-Augmented Generation (RAG) to deliver highly contextual and intelligent responses. This project leverages the strengths of graph-based knowledge representation and retrieval-based AI to enhance chatbot performance and ensure accurate, relevant, and dynamic interactions.

<h3>Features</h3>
<ol>
  <li><b>Neo4j Knowledge Graph Integration:</b> Organizes and manages structured knowledge for enhanced context-awareness.</li>
  <li><b>Retrieval-Augmented Generation (RAG):</b> Employs a hybrid approach by retrieving knowledge graph data and combining it with generative AI for robust responses.</li>
  <li><b>Scalable Architecture:</b> Designed to scale with data size and complexity for enterprise applications.</li>
  <li><b>Dynamic Querying:</b> Uses Cypher queries to extract relevant knowledge graph data in real-time.</li>
  <li><b>API Integration:</b> Includes APIs for seamless integration with web and mobile applications.</li>
</ol>


<h3>Prerequisites</h3>
<ul>
  <li>Python 3.9 or 3.9+</li>
  <li>Libraries Installation</li>
  <li>PostgreSQL</li>
  <li>Neo4j</li>
</ul>


<h3>Installation</h3>
<ul>
  <li>Clone the repository:</li>

  ```bash
git clone https://github.com/Bikas0/ChatBot-with-Neo4j-Knowledge-Graph-RAG-System.git
cd ChatBot-with-Neo4j-Knowledge-Graph-RAG-System
```
</ul>

<h3>Docker Compose</h3>

```bash
docker-compose up --build -d
```

<h3>Usage</h3>

<b>Interact with the chatbot:</b>

```bash
http://localhost:5508
```

Send a message and receive intelligent responses enriched with knowledge graph data.


<h3>Architecture</h3>
<ol>
  <li><b>Input Processing:</b> User queries are processed and analyzed for intent and entity extraction.</li>
  <li><b>Knowledge Retrieval:</b> Cypher queries dynamically retrieve relevant data from the Neo4j Knowledge Graph.</li>
  <li><b>Response Generation:</b> Combines retrieved data with a generative AI model for context-rich responses.</li>
  <li><b>Output Delivery:</b> Delivers the final response to the user via API or front-end application.</li>
</ol>


<h3>License</h3>

This project is licensed under the Apache License 2.0 . See the LICENSE file for details.

<h3>Acknowledgments</h3>
<ul>
  <li>Neo4j</li>
  <li>LangChain</li>
  <li>Llama3.2</li>
</ul>









