# V7.5 — Implementation plan for 20 specialist AI Agents (OPTION B)

**Status: PROPOSAL / PLAN ONLY — NOT IMPLEMENTED OR ACCEPTED.**  
**Date:** 2026-11-17. **Repository:** Manhhung114/Cong_ty_XD_3D, main.  
**Inspected main HEAD:** 3c066d0951418f8b783746a6b3bafaaefcdd6d6c.  
**V7.4 code CI baseline:** f18062493035530a706da443598c5e29496cba10.  
**Inputs:** the user's nine-page "Danh mục chi tiết 18 Agent AI" and the V7.5 specialist-skill evaluation document; V7.4 handoff, VERSION_MANIFEST.json and V740_INTEGRATED_AGENT_RUNTIME.md.  
**Rule:** implementation PRs must re-fetch main HEAD, run tests, show evidence and preserve existing signed Google Drive records.

## 1. Scope and non-negotiable constraints

- Add only **QCX (QA/QC Xây dựng)** and **LEG (Pháp chế/Hợp đồng)**; keep the 18 existing immutable IDs: CEO, PM, ELE, HVA, PLU, FIR, BIM, QSU, QAC, DOC, ARC, STR, XBI, XQS, PLN, SIT, HSE, MAT.
- **20 logical Agent identities is not 20 concurrent Celery workers.** The V7.4 live PostgreSQL/Redis/Celery stack is not yet production-accepted. Runtime availability, heartbeat and load are separately gated.
- Keep Google OIDC, Read/Update/Admin project access, admin-only secrets, shared encrypted AI vault and its existing cookie signing secret, signed Drive event journal, file originals, historical task approvals, V6.9 hierarchy, 16-room 3D headquarters and V7.4 queue state semantics.
- Never rotate auth.cookie_secret merely for the Agent upgrade. Never write OAuth tokens, API keys, HMAC keys, Google Drive binary files or customer contract content into the repository, issue, PR, logs or test fixtures.
- Human engineer/QC/legal reviewer owns professional signoff. AI outputs are evidence-linked **DRAFT / NEEDS_REVIEW**; never auto-sign, auto-certify TCVN/QCVN, issue a legal opinion as authoritative or perform dangerous live electrical operations.
- No production data migration, data deletion or changing previously signed HMAC events. Existing job IDs, source hashes, revision IDs and approved audit events retain their meaning.
- Requirements for registered Drive input analysis (<=50 MiB) and intended sheet-local Drive upload (500 MB) are distinct; do not claim either was live accepted without tests.

## 2. Exact organization design (Option B)

### 2.1 Preserve original 18 Agent IDs

| Group | Agent IDs | Main V7.5 specialist extension |
|---|---|---|
| Leadership | CEO, PM | Risk and portfolio evidence; WBS, dependency cycles and CPM |
| MEP | ELE, HVA, PLU, FIR | Unit-aware electrical, HVAC, hydraulic, fire protection verification calculators |
| MEP coordination | BIM, QSU, QAC, DOC | IFC/revision issue checking, BOQ lineage, independent MEP QC, immutable document revision |
| Building/design | ARC, STR, XBI, XQS | Dimension/interface checks, structural input screening, BIM delta/BCF, construction quantity reconciliation |
| Operations | PLN, SIT, HSE, MAT | CPM and schedule recovery; both-division site reporting; HSE-only JSA/PTW; both-division procurement/submittals |

### 2.2 Two new independent Agents

**QCX — Construction QA/QC**
- Logical department: xd_qc, business division: construction; physically displayed within an existing construction office (xd_safety room), **without inheriting HSE responsibility**.
- Capabilities: inspection-and-test plan (ITP) completeness; concrete/steel/formwork/finishing checklists; laboratory test certificate correlation to sample, date, work package and revision; NCR/CAR register, deadlines and closure evidence; handover evidence. Sampled file observation only unless an approved external tool actually executes.
- Required input: project scope, inspected activity, drawings and revisions, approved ITP, inspection forms, material certificates, sample/test results and applicable verified standards.
- Outputs: evidence-bound QC observations, deviations, missing tests, NCR/CAR suggestions, engineer-review task. Never certify materials, sign an inspection or self-approve.
- Separation: the QCX human reviewer must be independent of task author and HSE reporter. Existing QAC remains MEP QA.

**LEG — Contract and legal advisory**
- Logical department: legal, business division: shared; physically shown at the director office with distinct Agent identity and access boundary.
- Capabilities: contract clause inventory and version comparison; linked obligations, notice periods, variations/change orders, claims and milestone matrix; identify risk and missing supporting documents; prepare draft correspondence with clause/page citations.
- Required input: project-accessible registered contract/revisions, annexes, authorization and applicable laws verified for effective date.
- Outputs: draft issue register, obligation calendar, clause-to-source trace and messages for human legal review. **No binding interpretation, contract signature, admission of liability, legal representation, amendment or payment authorization.**
- Contract access requires a further document classification/ACL gate, not merely an arbitrary user-supplied Agent ID or department. In absence of that protection LEG is **metadata-only and feature-disabled**.

### 2.3 Modules, not extra agents

ELV (LAN/CCTV/access control) and lightning/earthing are ELE skills; GEO/foundations are STR skills; commissioning/as-built is coordinated among QAC/QCX/DOC plus specialist owner; finance/payment data review is QSU/XQS + LEG, without approving payment; independent design review is a QA workflow, not a self-approving VAL Agent. MAT and SIT cover both MEP and construction via project-scoped task roles.

### 2.4 16 rooms, 20 Agents

**Separate logical department from physical room**. Add an explicit office_room_id/roomId per Agent or equivalent mapping rather than automatically creating two additional 3D rooms. QCX -> xd_safety existing room; LEG -> director existing room. Enforce separate logical authorization and agent ID. Update the WebGL position/selection algorithm for rooms with >2 agents and SVG fallback; never call a missing room's coordinates. Do not silently alter current 16 room positions, floor proportions or header art.

## 3. Prompt/skill and tool contract (all 20)

A skill has an immutable id, version, objective, task scope, required input schema with units, allowed tools, input/source permission, output schema, blocking conditions, review owner, evaluation cases and audited tool results. Extend the catalog with (minimum) capabilities, calculators, standards_pack, input_template, output_template, eval_cases, agent_role_scope, office_room_id, skill_version and feature_flags. Keep schema parsing strict (unknown fields/IDs fail appropriately, no unvalidated tool execution).

Each result must include source locator (file ID, revision, SHA-256, page/table/cell/DXF handle/IFC GlobalId where applicable), observations versus hypotheses, assumptions, units, calculation method and version, references and their effective-date validation, unresolved input, review_status, tool invocation success/failure, provider and audit attempt ID. Never claim the tool ran if the call did not execute. Do not allow prompt injection in user files to override system/developer/tool permission rules.

**ELE as the pilot:** power/load-current/voltage-drop/thermal cable check and preliminary fault screening with independently tested Python equations; SLD from registered content, read-only DXF inspection and human-authorized output as a NEW revision. Cable decisions require installation, correction factors, protection coordination, fault energy and standards applicability; missing data returns NEED_INPUT. LOTO and appropriate electrical safety procedure are mandatory. Other numeric modules can follow the same engine with domain-specific dimension/validity tests.

Sources: versioned standards in a licensed/reference register with source, jurisdiction and effective date; lexical retrieval is current V7.4 functionality, not proven semantic RAG or standards compliance. Actual IFC clash, full shopdrawings, direct DWG/RVT/ETAP/Revit execution are OUT OF SCOPE unless separate tools are integrated and independently accepted.

## 4. Code change map (implementation PRs, NOT performed in this plan)

| Priority | Existing/new files | Required changes |
|---|---|---|
| P0 | data/agents_v61.json; NEW data/agents_v75.json; drive_storage/company_agents.py | Preserve V61 original as a compatibility fixture; introduce V75 catalog of precisely 20 unique stable IDs; validate required skill metadata; do NOT merely remove the exact-count guard |
| P0 | drive_storage/expert_rules.py; NEW drive_storage/agent_skills/* | Register QCX/LEG domains and quality gates, deterministic module dispatch, typed input validation, bounded file/source parsing and evidence schema |
| P0 | drive_storage/hierarchy.py; drive_storage/hierarchy_ui.py | Route construction QA to QCX for NEW V75 trees only; old QAC nodes remain untouched; LEG is explicit project-scoped specialist, not auto-granted approval; preserve idempotent DAG and 1–4 specialist limit unless separately changed |
| P0 | drive_storage/shared_workspace.py; drive_storage/access_control.py; drive_storage/workspace_ui.py | Add logical departments xd_qc/legal; deny by default; enforce stage-specific QA roles, independent reviewers, document category restriction for contracts, project and Google account checks at write AND read |
| P0 | src/core/config.js, static/src/core/config.js, src/3d/scene.js, static/src/3d/scene.js | 20 Agent cards; 16 physical rooms preserved; room mapping, avatars, hit-testing, responsive and fallback visuals; generated static assets kept in sync by existing build pipeline |
| P0 | src/core/hq_dashboard.js, static/src/core/hq_dashboard.js; drive_storage/monitoring.py | Replace hard-coded "18" labels with catalog-derived count; show queued/running/unconfirmed/completed/failed from signed evidence; no fictitious activity |
| P1 | drive_storage/company_agents.py; drive_storage/expert_orchestrator.py; agent_runtime/worker.py | Prompt layering + explicit allowed tool dispatch, cost/consent/size gates, specialist evidence, no self-approval, no replay of paid requests |
| P1 | agent_runtime/api.py; agent_runtime/queue.py; agent_runtime/models.py; docker-compose.v74.yml | Real Redis/PostgreSQL/Celery integration, liveness vs readiness, worker heartbeat, cancellation, identity revalidation, crash recovery under deployment tests; production secrets stay outside Git |
| P1 | agent_runtime/cad_tools.py, agent_runtime/standards.py, drive_storage/expert_tools.py | Read-only source + copied DXF revision, safe citations and source licensing, limited engineering computation |
| P0 | tests/*, agent_runtime/tests/*, .github/workflows/* | 20-Agent contract tests; original 18 backward compatibility; auth, hierarchy, API, CAD, frontend visual and worker integration acceptance |

**Existing constraints discovered in V7.4:**
- company_agents.py asserts exactly 18 and schema XD_MEP_AGENTS_V61;
- hierarchy.py hardcodes all QA nodes to QAC;
- shared_workspace.py and workspace_ui.py enforce department whitelists and special roles;
- src/core/config.js and the static mirror list 18 Agents;
- src/3d/scene.js looks up Agent coordinates via physical DEPARTMENTS and assumes at most two occupants;
- hq_dashboard.js contains a literal "18 Agent" label;
- some tests assert 18 exact IDs and construction QA legacy QAC behavior;
- agent_runtime/tests/test_runtime.py uses SQLite + fake dispatcher; not live production evidence.

## 5. Backward-compatible data strategy

1. Before any deployment: document exact git HEAD, snapshot read-only Drive event inventory/count and newest audit ID; verify immutable event HMAC with existing key. Export admin metadata backup and independently snapshot binary Drive files according to retention policy (metadata-only export is NOT a binary backup). Test restore on a separate sandbox, not production.
2. Keep the historical V61 JSON, V7.4 task DAG and existing HMAC event action/payload encoding readable. **Never re-sign, rename, edit or retroactively convert old events**. New fields are optional on old snapshots. Unknown historical agent IDs remain visible in their original reports.
3. Version NEW V75 plans explicitly (catalog_version and hierarchy_policy_version). Only newly approved proposals after Admin opt-in route construction QA to QCX. Prior QAC construction history is always replayed unchanged. No automatic bulk reassignment.
4. Make database changes additive and reversible (new nullable fields/tables/indexes; use a reviewed migration for PostgreSQL). Retain original Drive root, OAuth refresh token and auth.cookie_secret; re-use existing vault without exposing provider keys to browsers or workers beyond scoped use.
5. Deploy with flags V75_CATALOG=false, V75_QCX=false, V75_LEG=false by default (exact names to be standardized during implementation); stage dry-run against cloned/non-sensitive fixtures, verify parity, then enable for an allowed test project before general release.
6. Roll back by disabling V75 UI and new-job routing and redeploying the last accepted artifact; preserve new versioned artifacts and all immutable events. No destructive downgrade. If a new ledger action is necessary, implement a V7.4-compatible reader or leave it disabled until replay compatibility is proven.
7. Preflight the **2500-event Drive journal limit**: if near cap, BLOCK rollout until an integrity-preserving archive/reconciliation migration has been implemented and exercised.

## 6. Phased PR implementation with objective exit gates

| Phase / PR | Work package | Required evidence / acceptance |
|---|---|---|
| M0 / PLAN | Approve scope, baseline, safe migration and test matrix | This documentation PR; no source changes, no claim of production readiness |
| M1 / CATALOG-COMPAT | V75 catalog 20 IDs, schema contract, backwards reader and 16-room mapping model | Unit tests: exactly 20; all old IDs unchanged; previous 18 data and audit events still parse; missing/malformed skills fail closed |
| M2 / ORG-RBAC | QCX and LEG roles, QA separation, project/document ACL, signed audit, hierarchy policy version | Cross-project and two-account negative tests; construction NEW QA=QCX, MEP QA=QAC, all OLD trees unchanged; no self-approval |
| M3 / EXPERT-SKILLS | ELE pilot + 20 specialist prompt contracts; deterministic tools, provenance; QCX ITP/NCR, LEG contracts | Independent engineering fixtures; no invented compliance, tool audit and permissions; malicious/missing data gets NEED_INPUT/BLOCKED |
| M4 / 3D-UI | 20 visible Agent characters, 16 rooms, catalog-driven badges, scope-filtered monitoring | JS regression, 3 viewport sizes, real browser/WebGL and fallback screenshots; no overlap/black gutters; no fake running state |
| M5 / V74-RUNTIME | Actual Docker PostgreSQL, Redis, Celery, worker monitoring and recovery, read-only Drive integration | CI integration with real containers; deployment host smoke logs; 2 live Google accounts, cancel, heartbeat and failure cases; restore drill |
| M6 / LOAD-ACCEPT | Load 2 -> 4 -> 8 -> 12 -> 18 concurrent worker slots under provider quotas; full cross-discipline signoff | Real traces, CPU/RAM, latency, API 429/timeout, data provenance, zero duplicate paid calls, cost reports; **not the same as 20 Agents all running** |
| M7 / RELEASE | Canary test project -> rollback rehearsal -> promotion to main after review | Every gate PASS, evidence artifact IDs, manual signoff, monitoring alerts, new manifest and handoff docs |

Phases M1-M4 may be implemented in parallel only when dependency-compatible and every PR passes review. M5 is a blocking infrastructure gate before claiming live execution, regardless of 20-Agent catalog readiness.

## 7. Release criteria

- **Product scope**: 20 distinct Agent IDs and skill profiles, all 18 original IDs stable, 16 rooms unaffected, no missing dashboards.
- **Functional truthfulness**: Agent skill advertised only when tool and approved source are available. Outputs have DRAFT/human review and source lineage; if not proven, label PENDING/BLOCKED. No "20 Agent currently running" marketing claim.
- **Authorization**: two real Google test users with distinct permissions, project scoping, contract document ACL, negative and revoked-access scenarios; no leakage in API or browser.
- **Data**: old signed event replay and revision/hash reconciliation equal before/after; immutable Drive binary files untouched; encrypted API vault still usable without re-entering keys; tested recovery.
- **Quality**: all current and new CI PASS; review of real CAD file WITHOUT overwriting; independent calculator oracles; zero critical/high safety/security failures.
- **Infrastructure**: real service logs rather than mocked success; isolated PostgreSQL/Redis; worker health and heartbeat; crash/restart/cancel; controlled concurrency load with measured resources.
- **Review**: engineering lead for ELE/HVA/PLU/FIR/STR; construction QC for QCX; designated legal reviewer for LEG; Admin release review; approval is human-owned.

## 8. Commands and evidence checklist

Local / CI regression (no real AI cost):
- python -m unittest discover -s tests -p 'test_*.py' -v
- python -m unittest discover -s agent_runtime/tests -p 'test_*.py' -v
- npm test
- python -m compileall -q agent_runtime drive_storage streamlit_app.py
- Docker integration must use actual ephemeral PostgreSQL/Redis/Celery services, not the current fake dispatcher; capture job IDs and logs.

For **each implementation PR** attach base SHA, file diff, test names/counts, CI run URLs, open defects and rollback switch. Only a human reviewer merges the relevant PR; CI of a plan-only docs PR does not prove any code, deployment or runtime acceptance.

**Risk priority P0:** (a) old signed-event replay, (b) cross-project/contract leakage, (c) QAC->QCX new-tree-only routing, (d) 3D room mapping, (e) Redis/worker unavailable reflected honestly, (f) data backup/restore and journal cap, (g) real tool safety, (h) provider keys excluded from source.

**Next engineering deliverable after accepting this plan:** M1 catalog/compatibility change with strict contract tests, not a production rollout. See accompanying V750_20_AGENT_ACCEPTANCE_MATRIX.md.
