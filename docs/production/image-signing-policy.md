# Image and Edge Artifact Signing Policy

Status: policy template; production signing is not configured.

## Required artifact controls

- Every Central, mTLS terminator, Nginx, and Edge release artifact must be
  addressed by an immutable digest.
- Container signatures must be attached to an approved OCI registry reference
  and verified against the release policy before deployment.
- Edge binaries must have a detached signature or attestation bound to the
  exact SHA-256 recorded in the release manifest.
- SBOMs must be attached as release evidence and their hashes must match the
  release manifest.
- Verification must check artifact digest, signer identity, issuer/fulcio
  identity where keyless signing is used, and the transparency-log/bundle
  evidence required by the selected signing policy.

## Fail-closed rules

Deployment must stop when any of the following is missing or mismatched:

- approved registry reference;
- immutable image digest;
- valid signature/bundle or approved key reference;
- signer identity and issuer policy;
- SBOM hash or license review;
- release manifest and production gate evidence.

Local Docker tags such as `latest` or `security-candidate-*` are never proof of
release signing. Do not create a local key, signature, or approval reference
just to satisfy the production gate.

## Current blocker

The current candidates exist only in the local Docker daemon. No registry,
signing identity, signature bundle, attestation, or deployment verification
evidence is configured. The policy therefore remains `NOT_READY`.

Official workflow reference: [Sigstore Cosign container signing](https://docs.sigstore.dev/cosign/signing/signing_with_containers/).
