"""
Lab 1 - Guardrails + Canary Token

The guards that wrap HelpBot. INPUT guards run BEFORE the model and block bad
requests; OUTPUT guards run AFTER it and fix or block bad replies. The CANARY
is a secret planted in the system prompt - if it ever shows up in a reply,
the prompt leaked and guard_canary blocks the reply.

Every guard has the same shape:
    guard_x(text) -> (ok, reason, fixed_text)
      ok=True                    pass
      ok=False, fixed_text=None  hard BLOCK
      ok=False, fixed_text="..." repair the text and keep going (FIXED)

Run it:  python guardrails_demo.py   (pipeline.py does the running - provided)
"""
import re
import pipeline


# ===========================================================================
#  THE CANARY + THE HARDENED SYSTEM PROMPT
# ===========================================================================
# TODO (merge): the CANARY secret, and ASSISTANT_SYSTEM hardened to name it
#               as confidential and pre-refuse the classic leak tricks.
CANARY = ""
ASSISTANT_SYSTEM = ("You are OmniTech's support assistant. Answer briefly and "
                    "only about OmniTech accounts, billing, orders, refunds, and support.")


# ===========================================================================
#  INPUT GUARDS - screen the REQUEST before it costs a model call
# ===========================================================================
# TODO (merge): three policies + three guards -
#   JAILBREAK_PATTERNS / ALLOWED_TOPICS / MAX_INPUT_CHARS
#   guard_length, guard_jailbreak, guard_topic  (each is a hard BLOCK)


# ===========================================================================
#  OUTPUT GUARDS - screen the REPLY before the user sees it
# ===========================================================================
# TODO (merge): two policies + three guards -
#   PII_PATTERNS (redact = FIXED) / BANNED_OUTPUT (hard BLOCK)
#   guard_canary (the tripwire), guard_pii, guard_banned


# ===========================================================================
#  THE GUARD CHAINS - order matters: cheapest checks first
# ===========================================================================
# TODO (merge): list the guards in the order they should run
INPUT_GUARDS = []
OUTPUT_GUARDS = []


if __name__ == "__main__":
    pipeline.main(INPUT_GUARDS, OUTPUT_GUARDS, ASSISTANT_SYSTEM, CANARY)
