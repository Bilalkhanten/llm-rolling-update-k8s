FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# EXEC form on purpose: uvicorn must be PID 1 so it receives SIGTERM directly.
# (Shell form -> /bin/sh -c "..." is PID 1 and never forwards the signal.)
CMD ["uvicorn", "fake_llm:app", "--host", "0.0.0.0", "--port", "8000"]
