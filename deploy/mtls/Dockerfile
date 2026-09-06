FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/app /app/app
COPY deploy/mtls/revocation_gateway.py /app/deploy/mtls/revocation_gateway.py

ENV PYTHONPATH=/app
USER 65532:65532
ENTRYPOINT ["python", "-m", "deploy.mtls.revocation_gateway"]
