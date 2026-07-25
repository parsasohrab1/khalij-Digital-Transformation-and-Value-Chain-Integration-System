FROM python:3.10-slim

WORKDIR /app

COPY services/command-center/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared ./shared
COPY services/command-center/app ./app
COPY services/command-center/static ./static

ENV PYTHONPATH=/app
EXPOSE 8010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
