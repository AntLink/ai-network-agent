# Release Signing and Verification Runbook

Status: not executable for production until an approved OCI registry and
signing identity are supplied.

## Inputs required from the operator

- OCI registry/repository approved for Central, Edge and terminator images.
- Immutable image references and the release commit.
- Signing mode: keyless CI identity/issuer or managed KMS key.
- Cosign version and verified tool digest.
- SBOM paths and SHA-256 values.
- Approval/change reference and license review reference.

Do not place registry passwords, private keys, OIDC tokens, or KMS credentials
in this repository or in session logs.

## Candidate release flow

1. Build Central and Edge from the approved commit and pinned base images.
2. Push images to the approved registry using a release tag.
3. Resolve the immutable registry digest and compare it with the build record.
4. Sign the image digest with the approved Cosign identity.
5. Attach the CycloneDX/SPDX SBOM as an attestation or approved OCI artifact.
6. Verify the signature and attestation from a clean verification environment.
7. Record image digest, signature/bundle reference, SBOM hash, signer identity,
   issuer, and verification output in the release manifest.
8. Run `tools/validate_release_evidence.py` and the full production gate.

## Verification contract

The verification command must target an immutable registry digest, not a local
Docker tag. The policy must constrain both signer identity and OIDC issuer (or
the approved KMS key), and must verify that the signed digest matches the
deployment digest.

Illustrative commands after operator configuration:

```text
cosign verify REGISTRY/IMAGE@sha256:DIGEST \
  --certificate-identity REGEX_OR_IDENTITY \
  --certificate-oidc-issuer REGEX_OR_ISSUER

cosign verify-attestation REGISTRY/IMAGE@sha256:DIGEST \
  --type cyclonedx \
  --certificate-identity REGEX_OR_IDENTITY \
  --certificate-oidc-issuer REGEX_OR_ISSUER
```

The exact command, tool digest and clean-environment output become release
evidence. A local-only signature is not sufficient for production approval.

## Current state

- Local Central and Edge candidate images have SBOMs and selected-scope scans.
- No approved registry or signing identity is configured.
- No signed release artifact or attestation is recorded.
- Production gate must remain FAIL.

GitHub implementation scaffold: `.github/workflows/release-sign.yml`.
Operator instructions: `docs/production/github-ghcr-release.md`.
