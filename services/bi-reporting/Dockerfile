FROM python:3.10-slim

WORKDIR /app

COPY services/bi-reporting/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared ./shared
COPY services/bi-reporting/app ./app
COPY data ./data
COPY scripts/ensure_seed_data.py ./scripts/ensure_seed_data.py
COPY data/generate_value_chain_data.py ./data/generate_value_chain_data.py

RUN python scripts/ensure_seed_data.py || true

ENV PYTHONPATH=/app
ENV SYNTHETIC_DATA_PATH=/app/data/digital_value_chain_data_10k.csv
EXPOSE 8005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
