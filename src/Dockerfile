FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install gunicorn for production server
RUN pip install --no-cache-dir gunicorn

# copy application files
COPY src/ /app/

# copy gunicorn configuration file
COPY gunicorn.config.py /app/

# expose port 8765
CMD [
    "gunicorn",
    "app.main:app",
    "-k","uvicorn.workers.UvicornWorker",
    "-w","8",
    "-b","0.0.0.0:8765",
    "--timeout","30",
    "--keep-alive","5",
    "--backlog","4096",
]
