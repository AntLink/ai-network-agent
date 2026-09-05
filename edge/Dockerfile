# Minimal production-shaped Edge image. Runtime identity and credentials are
# mounted separately; no certificates, keys, or keystore are baked into it.
# GNS3 Docker bootstrap expects a minimal POSIX userspace and a root user
# (it invokes its init wrapper through `su`). The Edge binary remains a
# statically linked Go executable; Alpine is only the audited runtime shell.
FROM alpine:3.20
COPY ainet-edge-linux /ainet-edge
ENTRYPOINT ["/ainet-edge"]
