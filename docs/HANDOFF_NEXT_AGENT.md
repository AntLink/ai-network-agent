# AI Network Agent — Next-Agent Handoff

Last updated: 2026-09-05

## Start here

Read these files in order:

1. `docs/session-logs/2026/09/2026-09-03_1957_phase-04_five-block-production-hardening.md`
2. `docs/traceability/requirements-matrix.md`
3. `docs/production/production-gate.json`
4. `docs/evidence/pki-overlay/README.md`
5. `docs/runbooks/deployment-runbook.md`
6. `deploy/mtls/revocation_gateway.py`
7. `deploy/mtls/nginx_crl_reload.py`
8. `tools/test_nginx_tls_revocation.py`

Do not infer status from filenames. Rerun the validators and use the latest
timestamped production-gate report.

## Verified state

- FastAPI and React/Vite remain canonical.
- Redis is active for Edge session coordination.
- PostgreSQL `ainet_agent` is configured in `backend/.env`; the API uses the
  PostgreSQL TaskAttempt backend.
- PostgreSQL migration, atomic claim, renewal, expiry fencing, restore drill,
  and live Edge-2 facts dispatch are verified.
- Native Edge-1 -> R1 and Edge-2 -> R2 both work with management IP
  `192.168.1.1` in separate customer/site scopes.
- Private ZeroTier controller/client deauthorization is verified: client gets
  `ACCESS_DENIED` and loses its assigned overlay IP.
- Disposable Docker Nginx test is verified: valid client gets `HTTP 200`,
  revoked client gets `HTTP 400`, and only the valid request reaches upstream.

## Blockers

- `LIVE-PKI-OVERLAY` remains fail-closed because disposable lab Nginx is not
  the approved persistent production terminator.
- Release version, exact git commit, and licensing decision are unset.
- Central multi-node HA/control-channel routing is not live-proven.
- Full controller/PKI/application DR and live Edge update/rollback remain.

## First next action

Select an approved persistent production-equivalent TLS terminator. Configure
client certificate verification and CRL, connect revocation publication to
`deploy/mtls/nginx_crl_reload.py`, then run:

```text
python tools/test_nginx_tls_revocation.py
python tools/validate_pki_overlay_evidence.py
python .agents/skills/ainet-zerotier-platform/scripts/production_gate.py --config docs/production/production-gate.json --report-dir docs/evidence/production-gates
```

Do not set production evidence to `PASS` based only on lab results.

## Safety and handoff rules

- Never print or commit passwords, tokens, certificates, private keys, or
  device secrets. `backend/.env` remains local.
- Use disposable identities for revoke/deauthorization tests and restore them
  afterward.
- Do not globally route overlapping customer LANs into Central.
- Do not add a second task/job subsystem or arbitrary command API.
- Update the session log, traceability, and redacted evidence after every
  production-significant action.
