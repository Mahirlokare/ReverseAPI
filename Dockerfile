FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY apiscope ./apiscope
RUN pip install --no-cache-dir fastapi 'uvicorn[standard]' python-multipart
EXPOSE 8000
CMD ["uvicorn","apiscope.main:app","--host","0.0.0.0","--port","8000"]