FROM python:3.12-slim
WORKDIR /app
ARG INSTALL_PLAYWRIGHT=0
COPY pyproject.toml ./
COPY apiscope ./apiscope
RUN pip install --no-cache-dir .
RUN if [ "$INSTALL_PLAYWRIGHT" = "1" ]; then pip install --no-cache-dir playwright && playwright install --with-deps chromium; fi
EXPOSE 8000
CMD ["uvicorn", "apiscope.main:app", "--host", "0.0.0.0", "--port", "8000"]
