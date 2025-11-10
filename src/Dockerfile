FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install gunicorn for production server
RUN pip install --no-cache-dir gunicorn

# copy application files
# copy gunicorn configuration file also
COPY src/ /app/

# expose port 8765
CMD [ "gunicorn","backend_app:app","-k","uvicorn.workers.UvicornWorker","-c","gunicorn.conf.py"]
