FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e .

COPY --chown=appuser:appuser entrypoint.sh .
RUN chmod +x entrypoint.sh

COPY --chown=appuser:appuser src/ ./src/

USER appuser

CMD ["./entrypoint.sh"]
