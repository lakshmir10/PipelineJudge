FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . .

CMD bash -c "python startup.py && cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
