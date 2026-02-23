FROM python:3.11-slim
WORKDIR /app
COPY services/common/ /app/common/
COPY services/tester/ /app/
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
