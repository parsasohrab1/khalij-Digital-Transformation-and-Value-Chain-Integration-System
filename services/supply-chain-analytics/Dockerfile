FROM python:3.10-slim

WORKDIR /app

COPY services/supply-chain-analytics/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared ./shared
COPY services/supply-chain-analytics/app ./app
COPY data ./data

ENV PYTHONPATH=/app
EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
