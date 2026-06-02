from retrieval import search

results = search("transformers", k=5)

for r in results:
    print(r)