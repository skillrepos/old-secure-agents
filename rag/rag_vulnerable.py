"""
Lab 4 - Vulnerable RAG (provided complete, NO defenses).

Semantically retrieves from the Chroma vector database (which contains a
poisoned document) and feeds every retrieved chunk straight to the LLM. Run
create_db.py first, then run this and ask the questions in the lab to watch
the poisoned content reach the answer.
"""
from kb import kb_stats, retrieve, rag_answer, llm
from labkit import blue, red   # provided (kb.py puts common/ on the path)


def main():
    count, sources = kb_stats()
    print("=== VULNERABLE RAG (no security) ===")
    print(f"Vector DB loaded: {count} chunks from {len(sources)} sources")
    for s in sources:
        print(f"  - {s}")

    # Warm up the LLM backend so the first user question is less likely to time out.
    print("\nWarming up LLM backend...")
    try:
        llm.complete("Reply with OK.", prefer="strong", max_tokens=32)
        print("LLM warm-up complete.")
    except Exception as e:
        print(f"LLM warm-up skipped: {e}")

    print("\nType a question (or 'quit').")

    while True:
        try:
            q = input("\n> ").strip()
        except EOFError:
            break
        if q.lower() in ("quit", "exit"):
            break
        if not q:
            continue
        hits = retrieve(q, k=3)
        print()
        blue("SOURCES:")
        for h in hits:
            print(f"  [{h['relevance']}] {h['source']}")
        print("\nANSWER:")
        try:
            print(rag_answer(q, hits))
        except Exception as e:
            print(f"[error] Could not generate answer: {e}")
            print("Try starting/restarting Ollama with: bash scripts/startup_ollama.sh")


if __name__ == "__main__":
    main()
