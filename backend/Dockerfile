# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs.
ENV PYTHONUNBUFFERED=True
ENV APP_HOME=/app
ENV APP_VERSION=dev

WORKDIR $APP_HOME

# Install production dependencies first to maximize Docker layer reuse.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application source.
COPY . .
RUN chmod +x ./docker-entrypoint.sh

# Allow the deployment pipeline to inject the real application version even
# when the Docker build context is limited to the backend directory.
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

# Run the web service on container startup. Cloud Run provides PORT.
CMD ["./docker-entrypoint.sh"]
