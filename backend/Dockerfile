FROM python:3.10.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN chmod +x run.sh

RUN pip install --no-cache-dir -r requirements.txt
RUN pip uninstall uvcorn
RUN mkdir ../images

EXPOSE 8000

ENV WORKERS=1

CMD ["./run.sh"]
