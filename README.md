# Building Secure AI Agents: Defense-First Development

## Half-day workshop (3 hours) &mdash; Revision 1.13

These instructions will guide you through configuring a GitHub Codespaces
environment that you can use to run the workshop labs.

This workshop is for **agent builders**. Across five labs you take one
deliberately vulnerable AI support agent and harden it, layer by layer:
guardrails and canary tokens, least-privilege tool controls, a scoped MCP
server, RAG poisoning defenses, and observability. The final lab
(observability) is designed to also work as post-class homework if time runs
short.

### Prerequisites

Experience building AI agents (via the AI Accelerator, an agents workshop, or
equivalent), comfort with Python, and a basic understanding of agent
architectures (ReAct, tool calling, MCP). No prior security background is
assumed &mdash; every term is defined as it comes up.

<br><br>

**1. Change your codespace's default timeout from 30 minutes to longer.**
When logged in to GitHub, go to https://github.com/settings/codespaces and
scroll down to the *Default idle timeout* section. Adjust the value as desired.

![Changing codespace idle timeout value](./images/31ai5.png?raw=true "Changing codespace idle timeout value")

<br><br>

**2. Click on the button below to start a new codespace from this repository.**

Click here ➡️  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/skillrepos/secure-agents?quickstart=1)

<br><br>

**3. Then click on the option to create a new codespace.**

![Creating new codespace from button](./images/bsa1.png?raw=true "Creating new codespace from button")

This will run for a long time while it gets everything ready. Leave it building
and set up your Groq key (step 4) while you wait.

**4. Set up your Groq API key (for the cloud LLM).**
 
This enables the more powerful models and the real model-based gpt-oss-safeguard safety classifier used in Lab 1.  Create your free Groq key now (while your codespace finishes building) and set it. Follow the directions below.
 
A. Go to [https://console.groq.com](https://console.groq.com) and sign up or log in. No credit card is required for the free tier.

![groq console](./images/v3appb33.png?raw=true "groq console")
 
<br><br>

B. Navigate to [https://console.groq.com/keys](https://console.groq.com/keys) and click *Create API Key*.

![groq api keys](./images/v3appb34.png?raw=true "groq api keys")
 
<br><br>

C. Give it a name, create it, and copy the key value. Save it somewhere — you won't be able to view it again.

![groq api keys](./images/v3appb35.png?raw=true "groq api keys")

![groq api keys](./images/v3appb36.png?raw=true "groq api keys")
 
The labs can still run without a key &mdash; they fall back to the local Ollama model
&mdash; but a Groq key makes them faster and unlocks the model-based safety classifier.

<br><br>

**5. Ensure the codespace is done setting up.** 
After the initial startup, it will run a script to setup the python environment and install needed python pieces. This will take several more minutes to run. It will look like this while this is running.

![Final prep](./images/31ai2.png?raw=true "Final prep")

The codespace is ready to use when you see a prompt like the one shown below in its terminal.

![Ready to use](./images/31ai3.png?raw=true "Ready to use")


<br><br>

**6. Set your Groq key in the codespace.**
In the codespace **TERMINAL**, run the command below, paste your key when
prompted, and hit *Enter*:

```
source scripts/setup-key.sh
```

You should see that `AGENT_PROVIDER` and `GROQ_API_KEY` are set.

<br><br>

**7. Run the warm-up script for faster first responses.**

```
python scripts/warmup_ollama.py
```

<br><br>

**8. Open `labs.md`** and follow along. You can open it in the codespace
(right-click > *Open Preview*) or in a separate browser tab.

**Now you are ready for the labs!**

<br><br>

### The five labs

| Lab | Focus | Directory |
|---|---|---|
| 1 | Prompt-injection defense: guardrails, PII redaction, canary tokens | `guardrails/` |
| 2 | Securing agent tool calls: least privilege, approval gates, budgets | `agents/` |
| 3 | Hardening MCP servers: JWT auth + per-tool scopes | `mcp/` |
| 4 | RAG pipeline hardening: source allowlists, injection detection, output scanning | `rag/` |
| 5 | Auditing & observability: OpenTelemetry spans + anomaly detection *(homework-capable)* | `observability/` |

<br><br>

### Reopening a timed-out codespace

1. Go to https://github.com/codespaces
2. Find the codespace, right-click, and select *Open in browser*
3. Repeat steps 6 & 7 above to set the Groq key and re-run the warm-up.

<br><br>

## Troubleshooting

- **A lab reports it cannot reach Ollama** &mdash; the server isn't running. Run `bash scripts/startup_ollama.sh --skip-pull` from the repo root, then retry. Check `/tmp/ollama.log` if it persists.
- **The first model call is slow (~30-60s)** &mdash; run `python scripts/warmup_ollama.py` once, then retry. Later calls in the same session are fast.
- **Groq returns 429 (rate limit)** &mdash; you've exceeded the free tier. Wait a few seconds and retry, or `export LLM_BACKEND=ollama` to switch to the local model. Each person should use their own key.
- **Groq returns 401 / invalid key** &mdash; `GROQ_API_KEY` is missing or wrong. Re-copy it from console.groq.com, or unset it to fall back to Ollama.
- **A `python` command "hangs"** &mdash; the RAG and MCP labs use interactive prompts or run servers. Follow the lab's stop instruction (`quit` or `Ctrl+C`).
- **`Address already in use` in Lab 3** &mdash; a previous server is still running. Stop it with `Ctrl+C`, or `kill $(lsof -t -i:8000)`.
- **`ModuleNotFoundError`** &mdash; run `pip install -r requirements.txt` from the repo root (inside the `py_env` virtualenv).
- **Skeleton file errors before merging** &mdash; skeletons are completed via the `code -d` diff-merge step first. Each lab tells you when to merge.

## License and attribution

For educational use only by the attendees of our workshops.

&copy; 2026 Tech Skills Transformations and Brent C. Laster. All rights reserved.
