"""
Lab 4 - Hardened RAG

A SecurityGuard with defense in depth, in front of the SAME Chroma vector
database the vulnerable version uses:
  1. Source allowlist    - only trust chunks from known documents
  2. Injection detection - drop chunks that carry override/jailbreak phrases
  3. Relevance threshold - drop low-similarity chunks
  4. Output scanning     - redact phishing URLs / sensitive-data requests

    question -> retrieve() -> guard.filter_chunks() [1,2,3] -> rag_answer()
             -> guard.scan_output() [4] -> answer     ('report' lists events)

Run it:  python rag_hardened.py   (kb.py does retrieval + answering - provided)
"""
import re
from kb import kb_stats, retrieve, rag_answer
from labkit import blue, green, red   # provided (kb.py puts common/ on the path)


# ===========================================================================
#  THE FOUR POLICIES - plain data the guard checks against
# ===========================================================================
# TODO (merge): the four policies -
#   TRUSTED_SOURCES (allowlist), INJECTION_PATTERNS, RELEVANCE_MIN, BAD_OUTPUT_PATTERNS
TRUSTED_SOURCES = set()
INJECTION_PATTERNS = []
RELEVANCE_MIN = 0.0
BAD_OUTPUT_PATTERNS = []


# ===========================================================================
#  THE GUARD - filter_chunks() before the model, scan_output() after it
# ===========================================================================
class SecurityGuard:
    def __init__(self):
        self.events = []

    def log(self, kind, detail):
        self.events.append((kind, detail))

    def filter_chunks(self, chunks):
        """Apply all input-side checks; return only chunks that pass."""
        # TODO (merge): allowlist -> injection -> relevance, logging each drop
        raise NotImplementedError("filter_chunks not implemented yet")

    def scan_output(self, text):
        """Redact dangerous content the LLM may still have produced."""
        # TODO (merge): replace any BAD_OUTPUT_PATTERNS match with [REDACTED]
        raise NotImplementedError("scan_output not implemented yet")

    def report(self):
        print("\n=== SECURITY GUARD REPORT ===")
        if not self.events:
            print("  No security events.")
        for kind, detail in self.events:
            red(f"  [{kind}] {detail}")


# ===========================================================================
#  THE QUESTION LOOP (provided) - type a question, 'report', or 'quit'
# ===========================================================================
def main():
    count, sources = kb_stats()
    guard = SecurityGuard()
    print("=== HARDENED RAG (defense in depth) ===")
    for s in sources:
        if s in TRUSTED_SOURCES:
            green(f"  [TRUSTED] {s}")
        else:
            red(f"  [UNKNOWN] {s}")
    print("\nType a question, 'report', or 'quit'.")

    while True:
        try:
            q = input("\n> ").strip()
        except EOFError:
            break
        if q.lower() in ("quit", "exit"):
            break
        if q.lower() == "report":
            guard.report()
            continue
        if not q:
            continue
        hits = retrieve(q, k=3)
        safe = guard.filter_chunks(hits)          # checkpoint 1: before the model
        print()
        blue("SOURCES (after filtering):")
        for h in safe:
            print(f"  [{h['relevance']}] {h['source']}")
        answer = rag_answer(q, safe)
        answer = guard.scan_output(answer)        # checkpoint 2: after the model
        print("\nANSWER:")
        print(answer)


if __name__ == "__main__":
    main()
