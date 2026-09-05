# Building Secure AI Agents: Defense-First Development
## Half-day workshop (3 hours)
## Session labs
## Revision 1.5 - 09/05/26


**Follow the startup instructions in the README.md file IF NOT ALREADY DONE!**

**NOTE: To copy and paste in the codespace, you may need to use keyboard commands - CTRL-C and CTRL-V. Chrome may work best for this.**

---

### The through-line: one vulnerable agent, hardened layer by layer

Every lab in this workshop hardens **the same system** - *HelpBot*, OmniTech's
customer-support AI agent. HelpBot was shipped fast and works great in the demo:
it answers from a knowledge base (RAG), calls tools to do real work, reaches
external tools over MCP, and keeps a little memory between turns. It is also
completely undefended - and that is exactly the agent an attacker wants.

You will add one defensive layer per lab, in the order a builder should think
about them:

| Lab | The layer you add to HelpBot | What attack it stops |
|---|---|---|
| 1 | **Guardrails + canary tokens** around the model | Jailbreaks, PII leaks, system-prompt leaks |
| 2 | **Tool-call controls**: least privilege, approval, budgets | Indirect prompt injection abusing tools |
| 3 | **A hardened MCP server**: JWT auth + per-tool scopes | Unauthorized / over-scoped tool access |
| 4 | **RAG pipeline hardening**: allowlists, injection detection, output scanning | Knowledge-base poisoning |
| 5 | **Observability**: OpenTelemetry spans + anomaly detection | Blind spots - abuse you can't see |

No single control is perfect - that is the point. By the end, HelpBot survives
attacks that flattened it in Lab 1, because the layers cover each other. This is
**defense in depth**, applied to agents.

**How to pace yourself.** Each lab is built to run in **10-12 minutes** including
reading. Each lab ends with an optional step - that is *extra*, not required. If
you finish early, explore them; if you are still merging when the group moves on,
skip straight to running the code. Nothing in a later lab depends on finishing an
earlier one.

**A note on the model.** The labs use a **real** language model. With a free Groq
key set (see README) they use fast hosted models plus a real model-based **safety
classifier**; without one they fall back to a local `llama3.2:3b` via Ollama.
Because the model is real, exact wording varies run to run - the security
*outcomes* (BLOCKED / FIXED / DENIED) do not.

---
<br><br>

**Lab 1: Guardrails and Canary Tokens - Wrapping the Model**

**Purpose: In this lab, we put the first layer of defense around HelpBot: a guardrails pipeline modeled on the validator pattern used by frameworks like Guardrails.ai. Input guards run *before* the model to block jailbreaks and off-topic or oversized requests; output guards run *after* the model to redact PII and block unsafe completions. Then we add a canary token - a tripwire that catches a system-prompt leak even when every other guard misses it.**

> **New terms in this lab:** a **guardrail** is a cheap, deterministic check you run around the model (not inside it). An **input guard** screens the user's request before it costs a model call; an **output guard** screens the model's reply before the user sees it. A **jailbreak** is a prompt crafted to make the model ignore its instructions. A **canary token** is a unique secret string planted in the system prompt that should never appear in a normal answer - if it does, you know the prompt leaked.

<br>

1. From the terminal, change to the *guardrails* directory:

```
cd /workspaces/secure-agents/guardrails
```

<br><br>

2. Open the skeleton and review its shape:

```
code guardrails_demo.py
```

Notice the two families of guards. **Input guards** (`guard_jailbreak`, `guard_topic`, `guard_length`) screen the request. **Output guards** (`guard_pii`, `guard_banned`) screen the response. Each returns `(ok, reason, fixed_text)` - fixed text means the pipeline *repairs* and continues; `None` means *blocked*.

Wrapping those hand-built guards, `main()` also calls a **real model-based safety classifier** on both the input and the output (via `llm.moderate()`). That is the production pattern: regex/allowlist guards you own, **plus** a classifier that catches harm categories you could never enumerate by hand. The classifier runs only if you have set a `GROQ_API_KEY`.

<br><br>

3. Open the diff-and-merge view to fill in the validator logic:

```
code -d ../extra/guardrails_complete.txt guardrails_demo.py
```

![Building the guardrails pipeline](./images/bsa-1-build.png?raw=true "Building the guardrails pipeline")

<br><br>

4. Before you merge, skim what you are about to add. In the **input guards**: the jailbreak patterns (`ignore previous instructions`, `reveal your system prompt`, "developer mode"), the `ALLOWED_TOPICS` allowlist, and a maximum input length. In the **output guards**: `PII_PATTERNS` that redact SSNs, cards, emails and phone numbers (a *FIXED* outcome) and `BANNED_OUTPUT` patterns that hard-block dangerous responses (a *BLOCK* outcome). Note how `run_guards` tells a repairable finding from a hard block.

<br><br>

5. Merge all sections from the complete version (left) into the skeleton (right). When no differences remain, close the diff tab to save.

<br><br>

6. Run the guardrails demo:

```
python guardrails_demo.py
```

✓ **Success looks like:** one block prints per request. The jailbreak, the off-topic poem, and the oversized input each show **INPUT BLOCKED (never reached the model)**; the benign question shows **DELIVERED (PASS)**; the contact-confirmation request shows **DELIVERED (FIXED)** with `[EMAIL-REDACTED]` / `[PHONE-REDACTED]`. If everything shows PASS with no blocks, a guard didn't merge - reopen the diff at Step 3.

Each request flows through four layers: **classifier (input) -> your input guards -> the model -> your output guards -> classifier (output)**. The header line shows whether the classifier is `on`. The first request includes a brief model warm-up.

![Input guard results](./images/bsa-1-input1.png?raw=true "Input guard results")

<br><br>

7. Read the **input** side. The legitimate password question passes through to the model. The jailbreak, the off-topic poem, and the oversized input are each **INPUT BLOCKED (never reached the model)**, with the triggering guard named - those prompts never cost you a model call.

![Input guard details](./images/bsa-1-input2.png?raw=true "Input guard details")

<br><br>

8. Now read the **output** side. The benign answer is **DELIVERED (PASS)**. The contact-confirmation request exercises the PII guard: the assistant repeats back the email and phone you gave it, the output guard redacts them, and you get **DELIVERED (FIXED)**. A strong model often *refuses* to repeat an SSN or card on its own - which is a good outcome, and exactly why the output guard is your **backstop for when the model doesn't refuse**.

![Output guard results](./images/bsa-1-output.png?raw=true "Output guard results")

<br><br>

9. Look at the **last** request (`...walk me through building a pipe bomb`). It is genuinely harmful, but it is also *on-topic* (it mentions an account), so your regex and allowlist guards let it through - exactly what hand-built rules miss. With a `GROQ_API_KEY` set, **the safety classifier flags it and blocks it at the input layer**. Without a key you watch it slip past the cheap guards. That is the whole point: a model-based classifier catches what patterns can't.

<br><br>

10. Now add the **canary token** tripwire. This piece is provided complete - just run it:

```
python canary_demo.py
```

A unique secret (`CANARY-7f3a9c2b1e-DO-NOT-REVEAL`) is planted in HelpBot's *hardened* system prompt, which also pre-refuses meta-requests ("reveal your prompt," "repeat everything above"). The script fires real leak attempts, then **replays one known-compromised response** so you always see the tripwire fire: `scan_for_canary()` finds the secret, **BLOCKS** the answer, and raises an alert. A canary can't *prevent* a leak - it *guarantees you detect one*.

<br><br>

11. **(Optional)** Add a prompt of your own to the `inputs` list in `main()` and re-run to see which guard catches it.

<br><br>

> **Invariant lens:** each guard is a *precondition* on an action — the answer is delivered only if it satisfies every check. You are declaring invariants ("no PII leaves the system," "the canary never appears in output") and enforcing them at runtime, in the shell around the model rather than trusting the model to hold them.

<br><br>

**Key Takeaways:**
- **Guardrails wrap the model on both sides** - validate input before the model, validate output before the user.
- **Two outcomes, not one** - some violations are *repaired* (redact PII), others are *blocked* (unsafe content). A good pipeline supports both.
- **Allowlists beat blocklists for scope** - defining what's allowed keeps an assistant on-topic more reliably than chasing every off-topic case.
- **A canary token is a tripwire** - it detects the system-prompt leaks your other guards miss, so a silent compromise becomes a loud alert.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 2: Securing Agent Tool Calls - Least Privilege, Approval, and Budgets**

**Purpose: In this lab, we constrain HelpBot so a hijacked prompt can't make it misuse its tools. We start from the agent blindly following a poisoned support ticket - exporting employee data, emailing it outside the company, and deleting the audit log - then add three controls that contain the exact same attack: a least-privilege tool allowlist per task, an approval gate for high-risk actions, and hard budgets on how much the agent can do.**

> **New terms in this lab (skip if you build agents already):** an **agent** is an LLM in a loop that decides which **tools** (functions like "send email" or "export data") to call to finish a job. **Indirect prompt injection** is when the malicious instructions arrive *inside data the agent reads* - here, a hidden note in a support ticket - rather than from the user. **Least privilege** means giving the agent only the tools a given task needs. An **allowlist** is the explicit set of permitted tools. An **approval gate** pauses a risky action for review. A **budget** is a hard cap on how many steps or tool calls one run may take.

<br>

1. From the terminal, change to the *agents* directory:

```
cd /workspaces/secure-agents/agents
```

<br><br>

2. Open the agent skeleton and read the scenario:

```
code secure_agent.py
```

Look at three things. `TICKET` is a support request that *looks* benign ("summarize the Q3 benefits changes") but hides an attacker's instructions in an HTML comment - the indirect-injection payload. The tool set is split into `SAFE_TOOLS` (`read_ticket`, `summarize`) and `HIGH_RISK_TOOLS` (`export_data`, `send_email`, `delete_records`). A **real model** reads the ticket in `build_plan()` and proposes which tools to call - and, taking the bait, it tries to run the dangerous ones.

![Indirect injection](./images/bsa-2-injection.png?raw=true "Indirect injection")

<br><br>

3. Run the agent as shipped to see the attack land:

```
python secure_agent.py
```

The three control functions are still no-ops, so `export_data`, `send_email`, and `delete_records` all fire, ending in `BREACH`. That is undefended HelpBot doing exactly what the poisoned ticket told it to. (The model's proposed plan varies run to run; the canonical attack is replayed so the breach is reproducible.)

![The breach](./images/bsa-2-breach.png?raw=true "The breach")

<br><br>

4. Open the diff-and-merge view to build the three controls:

```
code -d ../extra/secure_agent_complete.txt secure_agent.py
```

![Building the secured agent](./images/bsa-2-build.png?raw=true "Building the secured agent")

<br><br>

5. These three functions are the whole defense:
   - **`allowed_tools(task)`** - *least privilege.* Return only the tools this job needs (`read_ticket`, `summarize`, `send_email`). Because `export_data` and `delete_records` are never offered, a hijacked plan that calls them is refused outright.
   - **`approve(tool, args)`** - *the approval gate.* Low-risk tools run freely; high-risk tools pause for an approver. In this unattended demo the approver denies the unexpected action (emailing data to an outside address was never part of the ticket).
   - **`within_budget(steps_taken, executed)`** - *budgets.* Stop the run once it exceeds `MAX_STEPS`, so even a bypassed agent can't loop or escalate.

<br><br>

6. Merge all three sections into the skeleton and close the diff tab to save.

<br><br>

7. Run the updated secured agent:

```
python secure_agent.py
```

✓ **Success looks like:** the **SECURED AGENT** section shows `export_data` **BLOCKED** (allowlist), `send_email` **BLOCKED** (approval denied), the remaining steps **HALTED** (budget), and ends `contained (no high-risk tool fired)` - while the **UNDEFENDED** section above still ends in `BREACH`. If the secured run also shows `BREACH`, a control didn't merge; reopen the diff at Step 4.

<br><br>

8. Compare the two runs. Same plan, different outcome - and each control does a distinct job:
   - `export_data` -> **BLOCKED (not in least-privilege allowlist)**
   - `send_email` -> **BLOCKED (approval denied)**
   - the remaining attacker steps -> **HALTED (budget)**

   The legitimate `read_ticket` and `summarize` steps still succeed, so HelpBot completes the job it was actually hired to do.

![Same hijack, contained](./images/bsa-2-contained.png?raw=true "Same hijack, contained")

<br><br>

9. Notice all three controls are necessary. Least privilege removes tools the task never needs; the approval gate catches a high-risk tool the task *does* legitimately use (`send_email`) but that the attacker tried to abuse; budgets cap the blast radius if anything slips through.

   Note also *who* sits in that gate. `approve()` is a **policy hook**, not a synonym for "a person" - it can be a human, a static policy, or a model-based classifier like the one you called in Lab 1. The invariant is unchanged (*no high-risk tool fires without approval*); only the evaluator is pluggable. We cover the industry data behind that shift on the slides.

<br><br>

10. **(Optional)** In `approve()`, temporarily `return True` for everything and re-run - `send_email` now fires. Put the denial back.

<br><br>

> **Invariant lens:** least privilege, approval, and budgets are *preconditions* on every tool call — a tool fires only if it is in the allowlist, is approved, and the run is within budget. These are runtime invariants on what the agent may *do*, enforced independently of whatever plan the model proposes.

<br><br>

**Key Takeaways:**
- **The agent will be talked into things** - indirect prompt injection means any data the agent reads can carry instructions. Assume the model will follow them.
- **Least privilege first** - the safest dangerous tool is the one you never hand the model for that task.
- **Gate high-risk actions - and watch who is gating** - route consequential tools through an *approver* before they fire. That approver can be a human, a static policy, or a classifier. Pick deliberately: a gate staffed only by a tired operator is a speed bump, not a control.
- **Budget the blast radius** - hard caps on steps and tool calls keep a hijacked agent from looping or escalating, even when other controls miss.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 3: Hardening MCP Servers and Tools**

**Purpose: In this lab, we'll harden the Model Context Protocol (MCP) server that HelpBot uses to reach its tools. A token authority issues scoped JWT access tokens (PyJWT), and a real FastMCP server enforces per-tool scope checks in middleware - so the same server grants different clients access to different subsets of tools, following least privilege at the protocol boundary.**

**This lab uses two terminals: the MCP server and the client.**

> **New terms in this lab:** **MCP (Model Context Protocol)** is a standard way for an agent to call external tools over a connection. A **JWT** is a signed token whose contents (here, a list of allowed tool **scopes**) can't be tampered with. **Middleware** is code that runs on *every* request before it reaches a tool - the right place to put an authorization check so nothing is protected by accident.

<br>

1. From the terminal, change to the *mcp* directory:

```
cd /workspaces/secure-agents/mcp
```

<br><br>

2. Review the token authority (provided complete):

```
code auth.py
```

`auth.py` mints and verifies scoped JWTs with the real **PyJWT** library. Note the **client registry**: `full-client` is granted all three tool scopes (`tools:add`, `tools:multiply`, `tools:divide`); `limited-client` is granted only `tools:add`. Those scopes are signed into each token's `scope` claim, so they can't be tampered with. (This stands in for a real identity provider.)

![Token authority](./images/bsa-3-auth.png?raw=true "Token authority")

<br><br>

3. Open the MCP server skeleton:

```
code secure_server.py
```

This is a real **FastMCP** server exposing three tools (`add`, `multiply`, `divide`) over HTTP. The security lives in `ScopeMiddleware.on_call_tool`, which runs on **every** tool call: it reads the `Authorization` header, verifies the Bearer JWT with `auth.verify_token`, then calls `enforce_scope()` - the one function you'll complete.

![Secure server](./images/bsa-3-server.png?raw=true "Secure server")

<br><br>

4. Open the diff-and-merge view and build the scope check:

```
code -d ../extra/secure_server_complete.txt secure_server.py
```

The provided code already authenticates the JWT (a missing or bad token raises **401**). You merge in **`enforce_scope(claims, tool_name)`**: read the token's scopes and raise a **403** `ToolError` if they don't include `tools:<tool_name>`. Because the check is in middleware, it protects every tool by default.

![Building the secure MCP server](./images/bsa-3-build.png?raw=true "Building the secure MCP server")

<br><br>

5. Merge `enforce_scope` into the skeleton and close the diff tab to save.

<br><br>

6. **Terminal 1 (server).** Start the FastMCP server and leave it running:

```
python secure_server.py
```

You should see `FastMCP server on http://127.0.0.1:8000/mcp/` and the list of scope-protected tools.

![Secure server running](./images/bsa-3-running.png?raw=true "Secure server running")

<br><br>

7. **Terminal 2 (client).** Open a new terminal (click the `+` in the terminal panel), then run the client:

```
cd /workspaces/secure-agents/mcp
python client.py
```

The client mints a scoped JWT for each registered client and calls all three tools against the server.

<br><br>

8. Watch the output. First, the **no-auth** run (no token) is rejected on every call with **401 Unauthorized: missing bearer token** - an unauthenticated call never reaches a tool.

![No-auth rejected](./images/bsa-3-noauth.png?raw=true "No-auth rejected")

<br><br>

9. Then the client runs as each registered client:
   - **full-client**: `add`, `multiply`, and `divide` all succeed
   - **limited-client**: `add` succeeds, but `multiply` and `divide` are **DENIED (403)** because the token only carries the `tools:add` scope

   ✓ **Success looks like:** three **401**s in the no-auth run, three **OK**s for `full-client`, then for `limited-client` one **OK** and two **DENIED (403)**. If `limited-client` succeeds on all three, `enforce_scope` didn't merge - reopen the diff at Step 4.

Same server, different access levels, driven entirely by signed token scopes. Check the **server** terminal too: it logs each allowed call (`[SECURE] full-client -> multiply (allowed)`).

![Scope enforcement in action](./images/bsa-3-scopes.png?raw=true "Scope enforcement in action")

<br><br>

> **What the real spec requires beyond this lab.** The shape you just built - authenticate every call, authorize per tool, do both in middleware - is right. The details are simplified so the mechanism stays visible. In production, per MCP spec revision **2026-07-28**: a protected MCP server is an **OAuth 2.1 resource server**, not a hand-rolled token authority; it **MUST** publish protected-resource metadata (**RFC 9728**) so clients can discover the authorization server; and tokens are **audience-bound** (**RFC 8707**) - a token minted for another service must be rejected and must never be forwarded upstream, which is the *confused deputy* rule. Note also that the spec deliberately sets **no scope-naming scheme**: `tools:<name>` is this workshop's convention, not a standard. Pick one and enforce it in middleware. (That same revision made MCP stateless - no session header, no `initialize` handshake - and changed nothing about the check you just wrote. An authorization invariant enforced per call survives a transport redesign.)

<br><br>

10. **(Optional)** Inspect what's actually inside a token. In Terminal 2:

```
python -c "import auth; print(auth.verify_token(auth.mint_token('limited-client')))"
```

You'll see `'scope': 'tools:add'` - the limited client's token never carries the multiply/divide scopes, so the server can't be tricked into running them.

<br><br>

11. When you're done, stop the server with **Ctrl+C** in Terminal 1.

<br><br>

> **Invariant lens:** `enforce_scope()` is a *precondition* on every tool call, asserted in middleware — the invariant "no call runs without a token that carries its scope" holds for every tool by default, including tools you add later.

<br><br>

**Key Takeaways:**
- **Authenticate every MCP call** - an unauthenticated tool call should never reach your tools.
- **Scope tokens per tool** - least privilege means a client gets exactly the tools it needs and nothing more.
- **Enforce in middleware** - centralizing the scope check keeps every tool protected by default.
- **Bind tokens to an audience** - a token issued for another service must be rejected, and never passed upstream.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 4: Hardening HelpBot's RAG Pipeline Against Poisoned Documents**

**Purpose: In this lab, we'll defend HelpBot's RAG pipeline against document poisoning. We'll see how a malicious document injected into the knowledge base can hijack the model with hidden instructions and phish users, then implement defensive layers - source allowlisting, injection detection, relevance filtering, and output scanning - to neutralize the attack.**

> **New terms in this lab:** **RAG (Retrieval-Augmented Generation)** means the agent answers by first *retrieving* relevant chunks from a knowledge base and feeding them to the model. **Document poisoning** is slipping a malicious document into that knowledge base so its hidden instructions reach the model as if they were trusted content. A **source allowlist** trusts only chunks that came from known, verified documents.

<br>

1. From the terminal, change to the *rag* directory:

```
cd /workspaces/secure-agents/rag
```

<br><br>

2. Open the poisoned document that simulates what an attacker might inject into the knowledge base:

```
code docs/OmniTech_Security_Bulletin.txt
```

It looks like a legitimate OmniTech bulletin, but it carries three attacks: a hidden `[SYSTEM OVERRIDE]` **prompt injection**, a **phishing URL** (`https://omnitech-secure-verify.com/reset`), and a **social-engineering** instruction to email full credit card numbers for "refund verification."

![The poisoned document](./images/bsa-4-poison.png?raw=true "The poisoned document")

<br><br>

3. Build the vector database. `kb.py` (shared by both versions) opens a **real local Chroma vector database**, runs **semantic similarity** search with real embeddings, and sends the top chunks to a real model. `create_db.py` chunks every document in `docs/` - the legitimate handbook and returns policy **and** the poisoned bulletin - and embeds them all into the same collection:

```
python create_db.py
```

You'll see each source and its chunk count, with the poisoned document flagged. (The first run downloads the small embedding model, ~30-60s; later runs are instant.)

![Building the vector database](./images/bsa-4-builddb.png?raw=true "Building the vector database")

<br><br>

4. Run the **vulnerable** RAG system - HelpBot's RAG with no security defenses:

```
python rag_vulnerable.py
```

You'll see the vector DB load, with the poisoned source mixed in among the legitimate documents. (The first model query includes a ~30-60s warm-up.)

![Loading the knowledge base](./images/bsa-4-kbload.png?raw=true "Loading the knowledge base")

<br><br>

5. At the prompt, ask these two questions in turn, then type `quit`:

```
How do I reset my password?
```
```
How do I get a refund?
```

On the first, watch the **SOURCES** and **ANSWER**: because the poisoned bulletin really *is* about password resets, it scores a high similarity, `OmniTech_Security_Bulletin_2024.pdf` shows up among the retrieved sources, and the answer hands the user the **phishing URL**. On the second, the poisoned document's instruction to share a full credit card number surfaces in the response. The vulnerable system trusts all retrieved context equally.

![Phishing URL in the answer](./images/bsa-4-phish.png?raw=true "Phishing URL in the answer")

<br><br>

6. Now add defenses. Open the diff-and-merge view:

```
code -d ../extra/rag_hardened_complete.txt rag_hardened.py
```

![Building the hardened version](./images/bsa-4-build.png?raw=true "Building the hardened version")

<br><br>

7. The `SecurityGuard` class on the left implements four layers of defense in depth:
   - **Source allowlist** - only chunks from known, verified documents are trusted (the poisoned bulletin is not on the list)
   - **Injection detection** - regex patterns catch `[SYSTEM OVERRIDE]`, `ignore previous instructions`, `supersedes all previous`
   - **Relevance threshold** - low-confidence chunks are dropped
   - **Output scanning** - the final answer is scrubbed of phishing domains and sensitive-data requests

   `filter_chunks()` and `scan_output()` are the two checkpoints: one blocks bad input, one redacts bad output.

<br><br>

8. Merge all sections into the skeleton and close the diff tab to save.

<br><br>

9. Run the hardened version against the same poisoned knowledge base:

```
python rag_hardened.py
```

The startup output now labels each source `[TRUSTED]` or `[UNKNOWN]`.

![Trusted vs unknown sources](./images/bsa-4-trusted.png?raw=true "Trusted vs unknown sources")

<br><br>

10. Ask the same two questions again. This time the poisoned chunks are blocked at the source-allowlist stage, and any sensitive request that slips into the output is redacted - the answers now come only from the legitimate handbook and returns policy. Type `report` to see every security event, then `quit` to exit.

   ✓ **Success looks like:** the password answer no longer contains `omnitech-secure-verify.com`, the refund answer no longer asks for a full card number, and `report` lists blocked chunks with the reason. If the phishing URL still appears, a layer didn't merge - reopen the diff at Step 6.

![Blocked and redacted](./images/bsa-4-blocked.png?raw=true "Blocked and redacted")

<br><br>

11. **(Optional)** Prove the allowlist is what's carrying the defense. In `rag_hardened.py`, temporarily add `"OmniTech_Security_Bulletin_2024.pdf"` to the trusted-source list, re-run, and ask about the password reset again. The poisoned chunk is now trusted at the door - and you can watch the *later* layers (injection detection, output scanning) try to catch it on their own. Remove it again when you're done.

<br><br>

> **Invariant lens:** the source allowlist is a *precondition on provenance* — a chunk reaches the model only if it came from a document you trust. That is why it beats content filtering: the attacker controls the text, but not where it came from.

<br><br>

**Key Takeaways:**
- **Document poisoning is a precision attack, not a volume attack** - a handful of documents in a corpus of millions is enough to steer answers.
- **Treat retrieved content as untrusted input** - it can carry hidden instructions aimed at the model.
- **Defense in depth wins** - source allowlists, injection detection, relevance filtering, and output scanning each catch what the others miss.
- **Output scanning is the safety net** - it protects users even when a malicious chunk slips through input filtering.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 5: Auditing and Observability for Agents *(homework-capable)***

**Purpose: In this lab, we'll make HelpBot observable using real OpenTelemetry. We'll wrap every tool call in an OTel span - trace IDs, span IDs, attributes, status - under one session trace, then run an anomaly detector over the captured spans to surface suspicious tool-call patterns. You can't defend what you can't see.**

> **This lab is designed to work as post-class homework if we run short on time.** It's self-contained and needs only the observability directory.

> **New terms in this lab:** **observability** just means being able to see what your system actually did. **OpenTelemetry (OTel)** is the industry-standard library for recording that. A **span** is one timed record of one operation - like a log line with a stopwatch and a label. A **trace** ties together all the spans from one session via a shared **trace ID**. Real systems ship these to tools like Jaeger or a SIEM; here we keep them in memory so we can inspect them right away.

<br>

1. From the terminal, change to the *observability* directory:

```
cd /workspaces/secure-agents/observability
```

<br><br>

2. Open the skeleton and review its shape:

```
code observable_agent.py
```

Note the `REQUESTS` list of natural-language `(user, request)` pairs and the `SENSITIVE_TOOLS` set (`export_employee_data`, `send_company_email`, `update_salary`). A **real model** drives the agent: `choose_tool()` asks it to pick one tool per request and return JSON. The provided `build_tracer()` sets up a real **OpenTelemetry** tracer with an in-memory span exporter. Some requests are benign; `mallory` issues a burst of bulk-export requests and `bob` asks for a mass email - your instrumentation has to make all of that visible.

![Observable agent skeleton](./images/bsa-5-skeleton.png?raw=true "Observable agent skeleton")

<br><br>

3. Open the diff-and-merge view to add the instrumentation and detector:

```
code -d ../extra/observable_agent_complete.txt observable_agent.py
```

![Building the observable agent](./images/bsa-5-build.png?raw=true "Building the observable agent")

<br><br>

4. Two pieces to complete:
   - **`instrument_call`** - opens an OpenTelemetry span (`tracer.start_as_current_span`) around the model's tool choice, sets attributes (`user`, `tool`, `args`, `sensitive`, `status`), marks unauthorized calls with an ERROR status, and prints a compact `[AUDIT]` line with the span's real `trace_id` / `span_id`.
   - **`detect_anomalies`** - reads the **captured spans** from the in-memory exporter and flags denied calls, sensitive-tool bursts (3+ of the same call), and any user touching sensitive tooling.

   The authorization stub (`authorize`, only `alice` may call sensitive tools) and the OTel setup are already provided.

<br><br>

5. Merge all sections into the skeleton and close the diff tab to save.

<br><br>

6. Run the observable agent:

```
python observable_agent.py
```

✓ **Success looks like:** a stream of `[AUDIT]` lines (one per request), each carrying a `trace=` and `span=` id, followed by a **TELEMETRY SUMMARY** and an **ANOMALY DETECTION** block that flags `mallory`'s denied exports, a **BURST**, and the users who touched sensitive tooling. If you see `NotImplementedError` or no anomaly findings, a function didn't merge - reopen the diff at Step 3.

![Structured audit stream](./images/bsa-5-audit.png?raw=true "Structured audit stream")

<br><br>

7. Read the **`[AUDIT]`** stream. Every call is a real OpenTelemetry span sharing a single **trace_id** for the session, each with its own **span_id** - the same trace/span model you'd export to Jaeger, Tempo, or a SIEM.

<br><br>

8. Look at the **TELEMETRY SUMMARY** - tool spans, sensitive calls, and denied calls, all read back from the captured spans. These are the metrics you'd graph on a dashboard.

![Telemetry summary](./images/bsa-5-summary.png?raw=true "Telemetry summary")

<br><br>

9. Now the **ANOMALY DETECTION** section. The detector flags `mallory`'s denied export attempts, the **BURST** of three rapid export calls, and surfaces every user who touched sensitive tooling for review. That is the jump from *logging events* to *finding patterns* - the difference between "we have logs" and "we noticed the attack."

![Anomaly detection](./images/bsa-5-anomaly.png?raw=true "Anomaly detection")

<br><br>

10. **(Optional) Add a new action and validate it through the logs alone.** Add `"update_salary"` to the `TOOLS` list, add it to the tool names in `TOOL_SYSTEM` so the model may choose it, and add a request that exercises it - e.g. `("mallory", "Update employee E1002's salary to $200k.")`. Re-run. The new action flows through the **same** instrumentation with no new logging code: a span is emitted, the `[AUDIT]` line shows `tool=update_salary sensitive=True status=denied`, and `detect_anomalies` surfaces it automatically.

<br><br>

> **Invariant lens:** this is the one lab that does *not* add a precondition. Labs 1-4 are **preventive** controls - they decide whether an action runs. Observability is the **detective** control that sits underneath them: its invariant is *every tool call leaves a span*, which is what lets you find the attacks your preconditions got wrong. You need both; a system with only preventive controls fails silently.

<br><br>

**Key Takeaways:**
- **Instrument every tool call** - structured logs with trace and span IDs make agent behavior auditable and explainable.
- **Telemetry feeds both ops and security** - the same spans power latency dashboards and intrusion detection.
- **Detect patterns, not just events** - bursts and denied-call clusters reveal abuse that any single line wouldn't.
- **Audit trails enable incident response** - forensics depends on having recorded what happened.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

---

### Where HelpBot ends up

Trace the layers back through the workshop. The agent that leaked its system
prompt, obeyed a poisoned ticket, exposed unscoped tools, served phishing URLs
from its knowledge base, and did all of it invisibly in Lab 1 now: blocks
jailbreaks and redacts PII (Lab 1), refuses tools outside its task and gates the
risky ones (Lab 2), authenticates and scopes every MCP call (Lab 3), filters
poisoned knowledge and scrubs its output (Lab 4), and records every action for
detection and forensics (Lab 5). No single control carried the load - together
they are defense in depth for an agent.

**Take it further.** The patterns here - input/output validation, least
privilege, scoped auth, retrieval hygiene, telemetry - map directly onto the
current standards. Worth reading next:

- **OWASP Top 10 for LLM Applications (2026 revision)** - note that *Excessive
  Agency* climbed to **LLM03** on the strength of real agentic incidents, and
  *System Prompt Leakage* was broadened and renamed *Hidden Context Exposure*.
- **OWASP Top 10 for Agentic Applications (ASI01-ASI10)** - the agent-specific
  companion list: goal hijack, tool misuse, identity and privilege abuse,
  memory and context poisoning, rogue agents.
- **MITRE ATLAS** - in particular `AML.T0110 AI Agent Tool Poisoning`, the
  MCP-specific technique, alongside the prompt-injection and RAG-poisoning
  techniques this workshop maps to.
- **"Careful adoption of agentic AI services" (2026)** - joint guidance from six
  Five Eyes cyber agencies (ASD's ACSC, CISA, NSA, Canadian Cyber Centre,
  NCSC-NZ, NCSC-UK) on operating agents safely.

**The layer we did not build.** Everything in these five labs constrains what the
agent *decides* - what it may read, call, answer with, and be seen doing. None of
it constrains the *process* the agent runs in. In production that fifth layer is
the one that holds when the others are wrong:

- **Isolate the process** - a sandbox, container or microVM. Weakest to
  strongest: shared-kernel sandbox, Docker, gVisor, Firecracker.
- **Scope the filesystem** - mount only what the task needs, read-only where
  possible; exclude `.env`, `~/.ssh`, `~/.aws/credentials`, `*.pem`.
- **Allowlist egress** - deny network by default, permit named hosts. This is
  what turns a successful injection into a failed exfiltration.
- **Keep credentials out of context** - a proxy injects the token so the agent
  never holds it.

None of these depend on the model behaving, which is exactly why they belong
underneath everything else. Anthropic's *Securely deploying AI agents* guide is
the most concrete public write-up.

A natural next step is a full threat model of your own agent, a containment pass
on the environment it runs in, and a red-team pass against both.

**And keep an eye on state.** An agent that runs for hours, or resumes across
sessions, carries its own memory forward - and anything it persists becomes an
input to its next run. Published work has payloads written into agent memory by
the *summarization* step surviving 100+ later sessions, long after the poisoned
content left the context window. That is OWASP **ASI06 Memory & Context
Poisoning** and MITRE **AML.T0080**, filed under *Persistence*. Treat a memory
write like any other privileged action: tag its provenance, validate it on write,
and expire it on a clock.

**One thing to keep an eye on.** Both halves of this loop are being automated at
once. On the defensive side, the review layer is shifting from "a human approves
each step" to "a machine screens every step" - the reason `approve()` in Lab 2 is
a policy hook rather than a person. On the offensive side, frontier-grade
exploitation is becoming a *licensed* capability handed to vetted defenders. The
practical takeaway is the same either way: the controls you built today have to
hold up against tooling that finds bugs faster than a human review cycle can
close them - which is exactly the argument for enforcing them in code rather than
in process.

<br><br>

<p align="center">
<b>For educational use only by the attendees of our workshops.</b>
</p>

<p align="center">
<b>(c) 2026 Tech Skills Transformations and Brent C. Laster. All rights reserved.</b>
</p>
