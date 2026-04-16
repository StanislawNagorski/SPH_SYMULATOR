# External Integrations

**Analysis Date:** 2025-01-31

## APIs & External Services

**None detected.**

This project is a self-contained local simulation. It makes no HTTP requests, calls no external APIs, and uses no third-party SDKs.

## Data Storage

**Databases:**
- None — no database connections of any kind

**File Storage:**
- None — no file I/O; all simulation state is held in memory during execution
- Output is written only to `stdout` (human-readable table or JSON)

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- Not applicable — no user authentication, no identity provider, no sessions

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- `stdout` only — results printed at end of simulation run
- Verbose mode (`--verbose`) prints per-100-cycle sampling inline
- JSON mode (`--json`) emits structured output to `stdout` for downstream parsing

## CI/CD & Deployment

**Hosting:**
- Not applicable — local command-line script

**CI Pipeline:**
- None detected (no `.github/`, `.gitlab-ci.yml`, or similar)

## Environment Configuration

**Required env vars:**
- None — zero environment variable dependencies

**Secrets location:**
- Not applicable — no secrets, credentials, or API keys in use

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## AI / Agent Integration

**Consumer:** `PROMPT_DLA_AGENTA.txt`

This project is explicitly designed to be consumed by an AI agent (e.g., LLM). The prompt document:
- Describes the full simulation model and mathematical constraints
- Lists all 5 available strategies and their parameters
- Provides baseline benchmark results to beat
- Requests the AI agent output a single ready-to-run CLI command
- Requests a GSD framework summary (planning, execution, verification roles)

The AI agent acts as an external optimizer — it reads the prompt, reasons about the game-theoretic model, and emits a `python sph_sim.py ...` command. The simulator then runs fully offline.

---

*Integration audit: 2025-01-31*
