FROM python:3.11-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install git (required for installing from GitHub)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

COPY neo_app.py /app/

# Install dependencies
RUN pip install fastapi
RUN pip install redis
RUN pip install uvicorn==0.15.0
RUN pip install "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git@v2.0.0#egg=neo_api_client"

EXPOSE 8001

CMD ["uvicorn", "neo_app:app", "--host", "0.0.0.0", "--port", "8001"]
