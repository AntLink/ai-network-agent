# PKI and Overlay Evidence

Required evidence: certificate serial/fingerprint revocation, active-session
disconnect, future handshake rejection, and overlay member deauthorization.

Current status: **NOT READY**. Central application-layer certificate
invalidation is proven with a disposable mTLS certificate, the dynamic
gateway harness closed a revoked connection before HTTP without a restart,
and the private controller/client test observed `ACCESS_DENIED` with no
assigned overlay IP after deauthorization. A disposable Nginx deployment test
did not reject the same CRL certificate and forwarded the request, so the
production TLS-terminator deployment remains unproven.

Controller evidence is available at
`zerotier-controller-ubuntu1-20260905.json`: the private controller is ready
on the GNS3 VM and Ubuntu1 is an authorized online member with an assigned
overlay address. A controlled deauthorization followed by client refresh
observed `ACCESS_DENIED` and removal of the assigned overlay IP; authorization
was then restored and the client returned to `OK`.

The repeatable disposable Nginx test now passes at lab scope: a valid client
reaches the sentinel upstream, while a revoked client receives `HTTP 400` and
does not reach the upstream. This is not yet production integration evidence
because it uses a disposable lab container rather than the approved
production terminator deployment.

Persistent staging evidence is recorded in
`nginx-staging-live-20260906.json`: the `nginx-staging` Compose profile stayed
running, a CRL reload caused the revoked client to receive `HTTP 400`, and a
valid client returned to `HTTP 200` after the lab CRL was restored. This still
does not replace an approved production PKI deployment.

Next-session acceptance sequence:

1. Configure an approved private PKI revocation authority and controller URL;
   never commit tokens or private keys.
2. Register the Edge certificate serial/fingerprint in the durable revocation
   state and connect revoke enforcement to the mTLS handshake path.
3. Revoke a disposable lab Edge, verify active-session disconnect and future
   HELLO rejection, then deauthorize its overlay member. This Central
   application-layer and private-controller/client sequence is now proven;
   TLS-terminator-level rejection remains a separate deployment test.
4. Save redacted evidence under this directory and update
   `docs/production/production-gate.json` only after the live command is
   repeatable.
