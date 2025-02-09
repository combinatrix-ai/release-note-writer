FROM python:3.11-slim

# Install Git (and any other system dependencies if needed)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /action

# Copy the entire project context
COPY . .

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Ensure the entrypoint script is executable
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/action/entrypoint.sh"]
