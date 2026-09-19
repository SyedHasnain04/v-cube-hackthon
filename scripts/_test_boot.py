import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from app.rag import retriever
retriever.initialise()

print()
print("--- Integration check ---")
results = retriever.retrieve("What are the overdue fines?")
section = results[0]["section"] if results else "N/A"
score = results[0]["score"] if results else 0
print(f"Query results: {len(results)} chunks")
print(f"Top match: {section} (score {score})")
print(f"Ready flag: {retriever.is_ready()}")
print(f"LRU cache info: {retriever._embed_query_cached.cache_info()}")
