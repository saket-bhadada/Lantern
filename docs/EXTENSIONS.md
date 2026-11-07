# Extension contract (how to add to Lantern without breaking it)

Design rule: the core is a small pipeline. Everything else plugs in through five interfaces. An add-on = one new file plus one line in `src/lantern/registry.py`. Add-ons must not change core files otherwise.

Pipeline: `ChatEvent -> Guard -> Router -> (CommandHandler | Brain) -> Postprocessors -> send`

## Interfaces (Python Protocols; sketch, Phase 2 turns these into code)
```python
class Brain(Protocol):            # local or cloud model
    name: str
    tier: Literal["local","cloud"]
    async def complete(self, messages: list[Msg], schema: dict | None) -> Completion: ...
    async def healthy(self) -> bool: ...

class CommandHandler(Protocol):   # "status", "rules", "forget", future commands
    trigger: str                  # exact word or regex
    approvers_only: bool
    async def handle(self, ev: ChatEvent, ctx: Ctx) -> Reply | None: ...

class Postprocessor(Protocol):    # provenance footer, risk caution, queueing
    order: int
    async def run(self, reply: Reply, ev: ChatEvent, ctx: Ctx) -> Reply: ...

class Verifier(Protocol):         # second-opinion judge
    async def judge(self, question: str, answer: str) -> Verdict: ...  # confirmed|minor_issue|incorrect

class RuleStore(Protocol):        # git-backed by default
    def propose(self, text: str, source: str) -> Rule: ...
    def approve(self, rule_id: str, approver: str) -> Rule: ...
    def forget(self, rule_id: str, approver: str) -> None: ...
    def active(self, scope: str) -> list[Rule]: ...
```
`ChatEvent`, `Reply`, `Rule`, `Verdict` are pydantic models in `src/lantern/models.py`.

## Rules for add-ons
1. One file in `src/lantern/addons/`, one registry line, one test file, one section in this doc.
2. Config via env or `config.yaml` keys prefixed with the add-on name; defaults must make it a no-op when unset.
3. Must degrade gracefully offline; declare `needs_internet = True/False`.
4. Must not execute shell, file, or network actions triggered by chat text.
5. Structured LLM output only, validated by pydantic.
6. Log with the structured logger; never log secrets or full user messages above debug level.

## How an improving agent should work
- Read this file, then the one interface involved. Do not scan the repo.
- Write the test first (mock the Brain), then the add-on, then register it.
- Record the add-on in the table below and tick/add a task in tasks/TASKS.md.

## Add-on registry (append rows)
| Name | Interface | needs_internet | Config keys | Status |
|---|---|---|---|---|
| ollama_brain | Brain | no | OLLAMA_URL, LANTERN_LOCAL_MODEL | planned (P2) |
| cloud_brains | Brain | yes | GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY | planned (P3) |
| status_cmd | CommandHandler | no | none | planned (P3) |
| provenance | Postprocessor | no | none | planned (P2) |
| risk_caution | Postprocessor | no | LANTERN_RISK_PATTERNS | planned (P3) |
| git_rules | RuleStore | no | LESSONS_DIR | planned (P4) |
