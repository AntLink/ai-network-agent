# Licensing and Release Compliance Matrix

Status: engineering evidence collected; commercial/legal approval pending.

This document separates the self-hosted deployment model from the license model. It is not legal advice and does not grant redistribution or commercial rights.

| Component | Version/commit in this repository or lab | How used | Self-hosted role | License/source status | Redistribution/commercial concern | Decision/evidence |
|---|---|---|---|---|---|---|
| ZeroTierOne core daemon | Lab reported `1.16.2`; production pin not selected | Edge overlay client | Private overlay membership and transport support | Core/service code is identified upstream as MPL-2.0; external code retains its own license | Preserve notices and review the exact binary/build inputs | `PENDING_RELEASE_PIN`; official sources: [repository](https://github.com/zerotier/ZeroTierOne), [license files](https://github.com/zerotier/ZeroTierOne/blob/dev/LICENSE-MPL.txt) |
| ZeroTier network controller | Controller used by the GNS3 VM lab; exact build/pin not recorded | Private controller API | Network/member authorization | Upstream documents controller/nonfree portions as source-available/commercially restricted; default binaries may not include controller | Commercial use and redistribution require explicit review; do not assume source availability is permission | `LEGAL_REVIEW_REQUIRED`; [official release notes](https://github.com/zerotier/ZeroTierOne/blob/dev/RELEASE-NOTES.md), [controller source](https://github.com/zerotier/ZeroTierOne/tree/dev/nonfree/controller) |
| Redis server | Runtime image/version is not pinned in repository metadata | Service | Ephemeral presence, session routing, coordination | Version-sensitive: Redis 7.2.x and earlier BSD-3-Clause; Redis 7.4 RSALv2/SSPLv1; Redis 8+ RSALv2/SSPLv1/AGPLv3 | Managed-service and source-disclosure obligations may apply to newer versions; pin and review before distribution | `PIN_REQUIRED`; [official licensing matrix](https://redis.io/legal/licenses/) |
| redis-py | `redis>=5.0,<6.0` | Python library | Central Redis adapter | MIT according to Redis official licensing page | Preserve dependency notices in release artifacts | `APPROVED_FOR_REVIEW`; [official licensing matrix](https://redis.io/legal/licenses/) |
| PostgreSQL | Windows service detected; exact server build must be captured per release | Service | Durable application state and TaskAttempt leases | PostgreSQL License, permissive and BSD/MIT-like | Preserve copyright/license notices | `APPROVED_FOR_REVIEW`; [official license](https://www.postgresql.org/about/licence/) |
| Nginx | `nginx:alpine`-derived staging image; exact digest not pinned | Service/proxy | mTLS terminator and CRL enforcement | Exact base image and Nginx build license must be recorded from release image | Image layers and bundled dependencies need an SBOM/license scan | `PIN_REQUIRED`; [official Nginx license](https://nginx.org/en/license.html) |
| Python dependencies | Unlocked requirements except selected Redis range | Libraries | FastAPI Central services | Mixed third-party licenses | Generate SBOM and retain notices for exact lock set | `PIN_AND_SCAN_REQUIRED` |
| Go dependencies | `golang.org/x/crypto v0.31.0`, `golang.org/x/sys v0.28.0` | Libraries | Production Edge | Upstream license files must be captured with the module graph | Generate SBOM and retain notices | `PIN_AND_SCAN_REQUIRED` |
| Project source | Repository work product | Application | Central, Edge contracts, drivers, safety layers | Project-level license/notice decision is not recorded in this assessment | Define project license and contributor/redistribution policy before external release | `PROJECT_DECISION_REQUIRED` |

## Required release actions

1. Pin exact versions or immutable image digests for ZeroTier, Redis, Nginx, Python, and Go dependencies.
2. Record the exact ZeroTier build flags; a controller/nonfree build must not be treated as equivalent to the MPL core daemon.
3. Generate an SBOM and license notice bundle for the Central image, Edge binary, and deployment images.
4. Obtain an explicit operator/legal decision for ZeroTier controller use, Redis version/license, and project redistribution.
5. Put the approved decision reference and release version/commit into `docs/production/production-gate.json`.

Until these actions are complete, `licensing_decision` must remain unconfigured and the production gate must fail closed.

## Evidence scope

The links above are official upstream references reviewed on 2026-09-06. They are evidence for engineering triage, not a legal opinion. A future release must repeat the review for its exact versions/builds.

The local Docker image observation is recorded separately in
`docs/evidence/release-readiness/image-digests-20260906.json`. Those digests
are lab observations, not approved production release pins.

The current SBOM readiness result is recorded in
`docs/evidence/release-readiness/sbom-gap-20260906.json`. Local CycloneDX
reports were generated, but the result remains partial: Python dependencies
now have a candidate lockfile, but package hashes, clean rebuild verification,
and local image digests do not establish production provenance.

The first Trivy scan found three HIGH advisories for `cryptography==46.0.7`.
The remediation candidate at `50.0.0` passed the repeat scan for the selected
HIGH/CRITICAL scope; exact evidence is in the SBOM gap artifact. This is not a
substitute for the complete production vulnerability policy or legal approval.
