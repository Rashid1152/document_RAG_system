FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# # Install build-essential for hnswlib/ChromaDB
# RUN apt-get update && apt-get install -y build-essential \
#     && pip install --no-cache-dir -r requirements.txt \
#     && apt-get remove -y build-essential \
#     && apt-get autoremove -y \
#     && rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY ./app/static /app/static

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 