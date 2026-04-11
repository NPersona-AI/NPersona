# NPersona Library – Final Plan

## 🎯 Goal

Turn the core persona generation engine of **NPersona Friday** into a **reusable Python library** that generates **full user‑centric and adversarial personas** (including names, roles, emotional states, conversation trajectories, scores, etc.) – without the web UI, database, or API server.

The library will be **fast, cheap, flexible, and easy to integrate** into CI/CD pipelines, test frameworks, CLI tools, and serverless functions.

---

## ✅ What the Library Will Do

- Parse AI system documentation (PDF, DOCX, MD, TXT) → plain text.
- Build a **knowledge graph** (agents, capabilities, data, guardrails, attack surfaces) using an LLM.
- Generate **full personas** (matching your `personas.json` schema) in **two modes**:
  - **Default: single‑prompt batch generation** – one LLM call for all user personas, one for all adversarial → fast & cheap.
  - **Optional: multi‑turn refinement** – higher quality, iterative improvement (slower, more expensive).
- Score personas by **novelty, coverage, risk**.
- Return personas as plain Python dicts / Pydantic models – no database, no web server.
- Support multiple LLM providers: Groq, OpenAI, Gemini, Azure OpenAI, and local models (Ollama).
- Allow users to skip expensive fields (`conversation_trajectory`, `playbook`, `scoring`) for speed.

---

## 🧱 Architecture (from existing code)

```
Input Document (PDF/DOCX/TXT/MD)
        ↓
[Document Parser] → plain text
        ↓
[Graph Builder] → LLM extracts nodes/edges → Knowledge Graph (cached)
        ↓
[Persona Generator] → LLM (single‑prompt or multi‑turn) → full personas
        ↓
[Scoring Engine] (optional) → novelty, coverage, risk, composite scores
        ↓
Output: list of persona dicts (JSON‑serializable)
```

**Caching**: Knowledge graphs are cached by document hash to avoid re‑extraction when reusing the same document.

---

## 📦 Public API (for users)

### Simple one‑shot generation

```python
import npersona

personas = npersona.generate(
    document="path/to/ai_spec.pdf",        # or raw text string
    num_user_personas=5,
    num_adversarial_personas=5,
    llm_provider="groq",                   # "openai", "gemini", "ollama"
    api_key="...",
    output_format="full",                  # or "minimal" (skip heavy fields)
)
```

### Advanced usage with caching & multi‑turn

```python
client = npersona.Client(llm_config={"provider": "groq", "api_key": "..."})

# Build graph once
graph = client.build_graph(document_text)

# Generate personas multiple times from the same graph
personas = client.generate_personas(
    graph=graph,
    mode="multi_turn",
    refinement_rounds=2,
    diversity_check=True,
)
```

### CLI tool (included)

```bash
npersona generate --doc ai_spec.pdf --num-user 5 --num-adv 5 --output personas.json
```

---

## ⚙️ Key Design Decisions (from our discussion)

| Decision | Rationale |
|----------|-----------|
| **Generate full personas** (not just prompts) | Matches your existing schema; users get rich metadata for testing. |
| **Single‑prompt batch generation by default** | 2 LLM calls → 10 personas → fast (<15s) and cheap (<$0.05). |
| **Multi‑turn refinement optional** | For power users who need highest quality or custom feedback. |
| **No database, no web server** | Pure Python – runs anywhere, no infrastructure overhead. |
| **Cached knowledge graphs** | Avoid re‑extracting graph when generating multiple persona sets from same doc. |
| **Configurable output fields** | `output_format="minimal"` skips `conversation_trajectory`, `playbook`, scoring – saves time & tokens. |
| **Pluggable LLM providers** | Users choose based on cost, speed, privacy (local Ollama). |

---

## 🚀 What Is Required to Build (Implementation Steps)

### Phase 1 – Core extraction (2 days)
- [ ] Copy `graph_builder.py`, `persona_generator.py`, `scoring.py`, `llm_client.py` into new `npersona/` folder.
- [ ] Remove all FastAPI, SQLite, SSE, file upload logic.
- [ ] Replace background tasks with plain async/sync functions.

### Phase 2 – Single‑prompt batch generation (1 day)
- [ ] Write a prompt that generates 5‑10 user personas in one LLM call.
- [ ] Write a prompt that generates 5‑10 adversarial personas in one LLM call.
- [ ] Use JSON mode / function calling to parse structured output.

### Phase 3 – Caching & configurable fields (0.5 day)
- [ ] Implement document hash → graph cache (in‑memory or user‑provided file).
- [ ] Add `output_format` parameter to skip `conversation_trajectory`, `playbook`, `scoring`.

### Phase 4 – Multi‑turn refinement (1 day) – optional for v1
- [ ] Generate one persona at a time, keeping history.
- [ ] Add refinement loop: score → ask LLM to improve low‑scoring personas.
- [ ] Avoid duplicates with diversity checks.

### Phase 5 – Pluggable LLM providers (1 day)
- [ ] Abstract `BaseLLM` class.
- [ ] Implement `GroqLLM`, `OpenAILLM`, `GeminiLLM`, `OllamaLLM`.

### Phase 6 – Packaging & distribution (0.5 day)
- [ ] Create `pyproject.toml` with dependencies (`httpx`, `pydantic`, `pypdf2`, `python-docx`).
- [ ] Add CLI entry point (using `click` or `argparse`).
- [ ] Publish to PyPI as `npersona`.

### Phase 7 – Documentation & tests (2 days)
- [ ] Write README (quickstart, API reference, examples).
- [ ] Unit tests (mock LLM responses).
- [ ] Integration tests (real LLM with small document).
- [ ] Jupyter notebook example.

**Total estimated effort: ~8 days for a solid v1.0** (single‑prompt + caching + minimal fields). Multi‑turn can be added later as v1.1.

---

## 🎯 Why This Is Best & Most Efficient for Users

| User Need | How the Library Delivers |
|-----------|--------------------------|
| **Fast integration** | `pip install npersona` and 3 lines of code. |
| **Low cost** | Single‑prompt batch generation → 2 LLM calls for 10 personas. |
| **High quality when needed** | Optional multi‑turn refinement. |
| **Flexible output** | Full personas or minimal (skip expensive fields). |
| **No infrastructure** | Runs in CI, Lambda, Colab, or local terminal. |
| **Private documents** | Works with local Ollama – no data sent to cloud. |
| **CI/CD friendly** | CLI mode, JSON output, non‑zero exit code on error. |

---

## 📁 Suggested Project Structure

```
npersona/
├── __init__.py
├── client.py              # High‑level Client and generate()
├── graph_builder.py       # LLM → knowledge graph
├── persona_generator.py   # Single‑prompt & multi‑turn generation
├── scoring.py             # Novelty, coverage, risk scores
├── llm/
│   ├── base.py
│   ├── groq.py
│   ├── openai.py
│   ├── gemini.py
│   └── ollama.py
├── parsers/
│   ├── pdf.py
│   ├── docx.py
│   └── txt.py
├── models.py              # Pydantic models (Graph, Persona, etc.)
├── cache.py               # Document hash → graph caching
└── cli.py                 # Command‑line interface
```

---

## 🔄 Next Steps for You

1. **Extract** the core logic from your existing backend (skip FastAPI, DB, SSE).
2. **Implement** the single‑prompt batch generation first (fastest path to a usable library).
3. **Test** with a few sample documents and your current persona JSON as expected output.
4. **Publish** to PyPI (test PyPI first) and share with early users.
5. **Iterate** – add multi‑turn, more LLM providers, etc., based on feedback.

---

## 📄 License

Same as your original project (MIT recommended).

---

**Built from the discussion with the NPersona team.**  
*For questions or contributions, open an issue on the repository.*