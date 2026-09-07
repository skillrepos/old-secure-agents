"""
Lab 4 - Hardened RAG (SKELETON)

Add a SecurityGuard with defense in depth, in front of the SAME Chroma vector
database used by the vulnerable version:
  1. Source allowlist  - only trust chunks from known PDFs
  2. Injection detection - block chunks with override/jailbreak patterns
  3. Relevance threshold - drop low-confidence (low-similarity) chunks
  4. Output scanning    - redact phishing URLs / sensitive-data requests

NOTE: incomplete. Merge in the logic from
extra/rag_hardened_complete.txt before running.
"""
import re
from kb import kb_stats, retrieve, rag_answer   # provided: the Chroma retriever + answerer


# ===========================================================================
#  HOW A QUESTION FLOWS THROUGH THIS FILE
#
#      question -> retrieve() top-3 chunks from Chroma
#               -> SecurityGuard.filter_chunks()   1. source allowlist
#                                                  2. injection patterns
#                                                  3. relevance threshold
#               -> rag_answer() with ONLY the surviving chunks
#               -> SecurityGuard.scan_output()     4. redact bad output
#               -> printed answer  (+ 'report' shows every guard event)
# ===========================================================================

# ---------------------------------------------------------------------------
#  THE FOUR POLICIES - plain data the guard checks against
# ---------------------------------------------------------------------------

# TODO (merge): TRUSTED_SOURCES allowlist
TRUSTED_SOURCES = set()

# TODO (merge): INJECTION_PATTERNS, BAD_OUTPUT_PATTERNS, RELEVANCE_MIN
INJECTION_PATTERNS = []
BAD_OUTPUT_PATTERNS = []
RELEVANCE_MIN = 0.0


# ---------------------------------------------------------------------------
#  THE GUARD - filter_chunks() before the model, scan_output() after it
# ---------------------------------------------------------------------------
class SecurityGuard:
    def __init__(self):
        self.events = []

    def log(self, kind, detail):
        self.events.append((kind, detail))

    def filter_chunks(self, chunks):
        """Apply all input-side checks; return only chunks that pass."""
        # TODO (merge): allowlist + injection + relevance checks with logging
        raise NotImplementedError("filter_chunks not implemented yet")

    def scan_output(self, text):
        """Redact dangerous content the LLM may still have produced."""
        # TODO (merge): redact BAD_OUTPUT_PATTERNS
        raise NotImplementedError("scan_output not implemented yet")

    def report(self):
        print("\n=== SECURITY GUARD REPORT ===")
        if not self.events:
            print("  No security events.")
        for kind, detail in self.events:
            print(f"  [{kind}] {detail}")


# ---------------------------------------------------------------------------
#  THE QUESTION LOOP (provided) - type a question, 'report', or 'quit'
# ---------------------------------------------------------------------------
def main():
    count, sources = kb_stats()
    guard = SecurityGuard()
    print("=== HARDENED RAG (defense in depth) ===")
    for s in sources:
        tag = "[TRUSTED]" if s in TRUSTED_SOURCES else "[UNKNOWN]"
        print(f"  {tag} {s}")
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
        safe = guard.filter_chunks(hits)
        print("\nSOURCES (after filtering):")
        for h in safe:
            print(f"  [{h['relevance']}] {h['source']}")
        answer = rag_answer(q, safe)
        answer = guard.scan_output(answer)
        print("\nANSWER:")
        print(answer)


if __name__ == "__main__":
    main()
