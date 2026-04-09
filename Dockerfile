FROM python:3.11-slim

WORKDIR /app

# install dependencies first
COPY backend/requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# copy project files
COPY . .

# run server
CMD ["bash", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
