# V7.5 — 20-Agent test and acceptance matrix

**Status: TEST PLAN / NOT EXECUTED.** This document lists acceptance tests to perform in implementation PRs and on a controlled deployment. A green GitHub docs-only PR does not prove runtime acceptance.

## Gate definitions

- PASS = executed, expected vs actual compared, logs/output/checksum and independent reviewer recorded.
- FAIL = unexpected result, regression, unsafe behavior or a false assertion.
- BLOCKED = prerequisite unavailable (e.g. VPS, two real Google accounts or rights-cleared file); never silently convert to PASS.
- NOT RUN = still planned.
- Evidence row = GitHub commit + CI run URL or private auditable job reference + date + test fixture hash + reviewer + verdict. Keep tokens/contract text/binary file out of public GitHub.
- Mandatory release rule: 0 critical security/data-loss/safety failures; all P0 gates PASS; no advertised unverified CAD/compliance/provider capability.

## A. Regression and schema contracts

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| A01 | Parse old V61 catalog unchanged | Exactly original 18 stable IDs, titles and historical lookup intact | P0 |
| A02 | Parse new V75 catalog | Exactly 20 unique IDs; QCX and LEG each have validated skill metadata | P0 |
| A03 | Reject duplicate, missing, typo or unsupported Agent IDs | Fail closed; no generic Agent silently assigned | P0 |
| A04 | Replay signed V7.4 Drive event fixture with original auth.cookie_secret | Byte-for-byte unchanged event IDs/signatures; same tasks/approvals/revisions/hashes | P0 |
| A05 | Legacy task attached to HSE, QAC or DOC | Task remains visible and history/assignee unchanged | P0 |
| A06 | Loading old data with new optional V75 fields absent | Backward-compatible default; no write-back to historical event | P0 |
| A07 | Existing unit, JS, Python compile and integration suites | All PASS; adapted expectation tests preserve old semantics | P0 |
| A08 | Synchronize src and static build artifacts | Identical 20-Agent semantics in Streamlit, bundled web and offline package | P0 |
| A09 | V75 feature flags OFF | Exact existing V7.4 user-visible behavior | P0 |
| A10 | Malformed skill/tool rule, unregistered standard version | Reject execution; log missing capability without fabricated output | P0 |

## B. Hierarchical dispatch and permissions

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| B01 | New V75 electrical task -> QA | ELE works, QAC reviews, independent human QA required | P0 |
| B02 | New V75 construction STR/ARC task -> QA | QCX reviews, not HSE or QAC, independent reviewer | P0 |
| B03 | Historic construction QAC QA task | Continue with signed old QAC assignment; no retroactive reassignment | P0 |
| B04 | New contract-specific task | LEG only when Admin explicitly authorized project and document scope | P0 |
| B05 | User with Read role tries to enqueue/change legal/QC approval | 403/denied, no signed mutation, no worker job | P0 |
| B06 | User with Update role outside project tries to access contracts | Deny metadata and binary content, no cross-project leakage | P0 |
| B07 | Admin with no explicit legal document entitlement tries LEG content | Metadata-only or denied, no implicit all-contract access | P0 |
| B08 | Expert tries to approve own result or bypass QA | Denied; independent human approval preserved | P0 |
| B09 | HSE attempts quality acceptance or QCX attempts safety permit | Role isolation blocks action, no authority escalation | P0 |
| B10 | Revocation after enqueue but before worker claim | Worker re-checks Drive permissions and refuses file read/execution | P0 |
| B11 | Signed HMAC request tampered/expired/replayed under different body | Unauthorized; no job created | P0 |
| B12 | Two Google test accounts with distinct project memberships | Viewer/editor/admin policy respected; no browser-side identity spoof | P0 |
| B13 | Cross-division MAT/SIT assignments | Only explicitly approved project and task; no automatic global access | P0 |
| B14 | Department routing with accents, without accents, synonyms | Evidence-based suggestion; ambiguous input requires Admin selection | P1 |
| B15 | Existing V6.9 1–4 departments cap and no duplicate nodes | Topology and approval dependencies preserved | P0 |

## C. Specialist tool verification

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| C01 | ELE 3-phase current with fixed P/U/PF/efficiency | Independently reproduced A result, units/assumptions explicit | P0 |
| C02 | ELE voltage-drop/cable check with all rated and installation inputs | Dimensionally correct, limits cited and no unsupported final cable declaration | P0 |
| C03 | ELE missing cable length, installation correction or fault clearing time | NEED_INPUT; no equipment size recommendation disguised as approved | P0 |
| C04 | ELE electrical safety request for energized field work | LOTO/electrical safety gate and human qualified-person escalation | P0 |
| C05 | HVA air changes and ventilation fixture | Independent result with consistent m3/h, m3, h^-1; errors on bad inputs | P1 |
| C06 | PLU flow/velocity and pump-head fixture | Independently verified units and domain validity | P1 |
| C07 | FIR sprinkler flow, water volume fixture | Pressure/K units explicit, source/version and human fire engineer review | P1 |
| C08 | STR structural-load-screen fixture | Screening-only; never asserts safe structural design | P1 |
| C09 | QSU/XQS quantity/price and revision difference | Calculations reconcile; provenance to source row and revision | P1 |
| C10 | PM/PLN CPM precedence, cycle and float | Independent scheduling fixture; detect cycle rather than invent dates | P1 |
| C11 | QCX concrete test package missing certificate/ITP/signature | Missing evidence and NCR candidate, no false ACCEPTED | P0 |
| C12 | QCX complete authorized construction test package | Traceable checklist and NEEDS_REVIEW draft, no auto-approval | P0 |
| C13 | LEG ambiguous contract clause or missing annex | Quote exact page/ref within rights; flag uncertainty; no definitive legal advice | P0 |
| C14 | LEG revised annex affecting claim/notice deadline | Compare versions with date source; ask legal reviewer to verify jurisdiction/validity | P0 |
| C15 | A standard with unknown revision/current legal force | standards_status=not_assessed; no compliance PASS | P0 |
| C16 | Prompt injection embedded in PDF/CSV/DXF title or contract | Treated as untrusted document content; no tool/role/secret override | P0 |
| C17 | Test provider/tokens absent or quota exceeded | Real failure/blocked; no invented provider use or cost | P0 |
| C18 | Source with restricted license or not registered in project | No content extraction to AI; metadata-only/permission denial | P0 |
| C19 | ELV/GEO/COM/FIN/VAL modules with missing executable tool | Capability shown as planned/blocked; not standalone Agent or fake completed job | P1 |

Numerical tolerances should be fixed per independent fixture and unit (absolute/relative), not set after seeing the output. Every worked example must include an intentionally wrong unit, a missing input and a limit-boundary case.

## D. File/CAD/source integrity

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| D01 | Registered Drive DXF under 50 MiB, read-only | Scope verified, source/hash/revision captured | P0 |
| D02 | Engineer-authorized DXF annotation | New filename/revision, original SHA-256 exactly unchanged | P0 |
| D03 | Try overwrite original DXF or already-existing revision | Fail; no destructive update | P0 |
| D04 | Malformed/unbounded CAD/ZIP/PDF input, oversize 50 MiB | Safe rejection/resource cap, no partial document corruption | P0 |
| D05 | IFC model metadata vs actual geometry clashes | Correct distinction; do not claim clash unless geometry engine was executed | P0 |
| D06 | Intended 500 MB Drive upload in existing sheet (test host capacity) | No standalone upload page; streaming + checksum + resumable failure test; otherwise BLOCKED | P1 |
| D07 | Cross-project legal PDF file ID forced in runtime job | Denied on API and rechecked worker; no extraction or provider disclosure | P0 |
| D08 | File/source references in Agent output | Source handle/cell/page + revision + hash; no invented line refs | P0 |

## E. 3D interface and real observability

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| E01 | 20 logical profiles on CEO dashboard | 20 unique cards/names, no label hard-coded 18 | P0 |
| E02 | Three floor/office layout with 16 physical rooms | Exactly 16 rooms and preserved graphics; QCX/LEG visible in assigned shared rooms | P0 |
| E03 | User taps every avatar in WebGL | Hit-target yields correct Agent ID, role/department and inspector | P0 |
| E04 | WebGL unavailable/mobile fallback | All 20 accessible, no JS exception, correct filtered division | P0 |
| E05 | Viewport 360x800, 1280x800, 1910x898 | No clipping, black gutters, overlapping agent marker or invisible header | P0 |
| E06 | Queued, running with recent heartbeat, stale unconfirmed, completed draft, failed | Distinct truthful states; no completed claim without signed result | P0 |
| E07 | Viewer sees other project's job dashboard | Denied/filtered at server, not merely hidden by CSS | P0 |

## F. Actual V7.4 runtime / operations — not satisfied by existing SQLite CI

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| F01 | Real private PostgreSQL+Redis+Celery+API+Streamlit host | All services healthy, isolated network, backup persists across restart | P0 |
| F02 | API /health vs dependency readiness | Liveness does not falsely claim Redis/DB/worker healthy; readiness probes real dependencies | P0 |
| F03 | Real queued -> claimed -> running -> heartbeat -> signed draft | Correlated job ID, DB status, worker log and Drive signed event | P0 |
| F04 | Stop worker >90s during active job | UI shows unconfirmed; no fictitious heartbeat or finished state | P0 |
| F05 | Cancel queued and running | Queued cancelled; running cancel_requested then checkpoint cancellation; never immediate success claim while API call continues | P0 |
| F06 | Redis down / DB down / worker loss and restart | Explicit failure/degraded state; no duplicated paid request, bounded recovery | P0 |
| F07 | Repeated request with same idempotency key | Exactly one charged job/start event, same result or controlled block | P0 |
| F08 | Google permissions revoked after job submission | Deny file read at worker execution, preserve audit trail | P0 |
| F09 | Encrypted AI vault reused from prior V7.4 project | No key reentry for allowed uses and no secrets exposed to browser/log | P0 |
| F10 | Backup+restore PostgreSQL in sandbox; reconcile Drive journal | Identical job states/document IDs/approval evidence, no irreversible data loss | P0 |
| F11 | Load 2,4,8,12,18 concurrent slots with bounded actual quotas | One acceptance report per rung; stop scaling on failures, rate-limit or budget breach | P1 |
| F12 | Provider cost/usage | Report actual only from trusted usage metadata; reserved estimate labeled estimate | P0 |

## G. Stop/go matrix

- **M1 GO:** A01-A10 PASS; backward-compat signed archive checks PASS.
- **M2 GO:** B01-B13 + B15 PASS, plus legacy D07 negative test; no rights violation.
- **M3 GO:** C01-C04, C11-C18, D01-D05, D07-D08 PASS; expert owner signs the numeric oracle and safety wording.
- **M4 GO:** E01-E07 PASS in real browsers; original V7.0 layout preserved.
- **M5 GO:** F01-F10 and F12 PASS on actual host; two Google accounts verified by Admin without credentials in PR.
- **M6 GO:** F11 completed as a measured load campaign; 18 concurrency is a stretch objective, **not required to claim catalog of 20 Agent profiles exists**.
- **M7 RELEASE:** all mandatory gates PASS, reviewer signatures and rollback rehearsal; otherwise keep feature flag off and issue OPEN/BLOCKED.

## H. Runbook and results template

For each tested case record:
- Test ID; test fixture version/source hash; branch SHA; operator (role only in public report); environment and date.
- Expected outcome; actual outcome; PASS/FAIL/BLOCKED/NOT RUN; job_id/source revision where allowed; GitHub Actions URL; redacted logs/screenshots.
- Regression impact on 18 original Agents; old event signature check; Drive file SHA-256 comparison.
- Independent reviewer; issues to fix; rollback flag and actual rollback verification.

Tests currently provided by V7.4 remain authoritative for what they really cover: unit/API tests with SQLite and fake Redis dispatcher, existing Streamlit/JS suites and Android debug build. They do NOT demonstrate two Google production accounts, real CAD throughput or 18 concurrent workers.

**Do not merge implementation into main until PR test evidence and reviewer approvals are attached.**
