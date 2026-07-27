FROM python:3.10-slim
WORKDIR /app
COPY services/customer-portal/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY shared ./shared
COPY services/customer-portal/app ./app
COPY services/customer-portal/static ./static
ENV PYTHONPATH=/app
EXPOSE 8011
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
