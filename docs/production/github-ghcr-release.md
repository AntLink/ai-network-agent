# GitHub GHCR Release Signing

Status: workflow scaffold; not executed.

The repository now contains `.github/workflows/release-sign.yml`. It is
manual-only (`workflow_dispatch`) and is intended to run from an approved
release commit. It uses:

- GitHub Container Registry (GHCR) for OCI image storage;
- `GITHUB_TOKEN` for package publishing;
- GitHub OIDC (`id-token: write`) for Cosign keyless signing;
- Syft SBOM generation;
- Cosign signature and CycloneDX attestation verification.

## Operator setup

1. Ensure the repository permits GitHub Actions to write packages.
2. Create or select the approved release commit and tag value.
3. Review the workflow action versions and pin action SHAs according to the
   organization's supply-chain policy.
4. Configure the production gate's release version, commit, GHCR image
   digests, SBOM hash, and licensing approval reference from workflow evidence.
5. Dispatch `Release build, SBOM and signing` manually with an immutable
   release tag. The workflow accepts only `vMAJOR.MINOR.PATCH` tags and checks
   that the checked-out commit exactly matches that tag. This comparison uses
   the checked-out commit, not the dispatch ref's `GITHUB_SHA`.
6. Confirm the workflow's signer identity and OIDC issuer match the release
   policy before deployment.

The workflow does not contain registry passwords, private keys, or device
credentials. It does not sign local Docker tags. It signs the immutable digest
returned by GHCR and verifies that digest immediately afterward.

## Current limitations

- The workflow has not been executed because no approved release tag or GHCR
  release approval exists.
- The workflow now checks out the supplied immutable release tag and publishes,
  signs, verifies, and attests both Central and Edge images. A signed combined
  release manifest is still required before production approval. Each run now
  uploads a generated manifest evidence file containing immutable image
  references and SBOM hashes; operator approval and licensing fields remain
  intentionally unconfigured.
- Signature and attestation verification each have a 180-second timeout with
  explicit image progress output, so a registry or transparency-log stall
  fails diagnostically instead of hanging indefinitely. The timeout now uses a
  SIGKILL fallback, and the complete release job is capped at 30 minutes.
- Production gate remains fail-closed until workflow evidence is attached.
