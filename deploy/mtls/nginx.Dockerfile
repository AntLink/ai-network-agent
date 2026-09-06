FROM nginx:alpine

RUN mkdir -p /var/cache/nginx /var/run \
    && chown -R nginx:nginx /var/cache/nginx /var/run

# Master starts as root to initialize cache paths; nginx.conf drops workers to
# the unprivileged nginx user. No Linux capabilities are retained by Compose.
USER root
