from retrieval import search

results = search("""
#ml
AI Agents are software applications built on generative AI that reason over and generate natural language, automate tasks using tools, and take appropriate action based on contextual conditions.

3 key elements:

- [[Large Language Models (LLMs)]] - Agent's brain for language understanding and reasoning
- Instructions - System [[Prompts]] that define agent's role and behavior
- Tools - allow agents to interact with their "world"
	- Knowledge tools like search engines provide access to information
	- Action tools enable agent to perform task like an IDE
""", k=5)

for r in results:
    print(r)