from retrieval import search

results = search(""" Helps differentiating multiple documents within same corpus
	- Compares how often a term appears in a specific document compared to its general frequency across the entire collection of documents
	- Formula used to calculate IDF is idf(t) = log(N / df(t))
	- TF - IDF = tf(t, d) * log(N / df(t))
	- High TF-IDF score means word appears more often in one document but rarely in others.


#ml""", k=5)

for r in results:
    print(r)