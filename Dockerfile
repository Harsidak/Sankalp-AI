# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME Sankalp

# Run with Gunicorn (Optimized for Cloud Run)
# Workers = 1 (Cloud Run handles scaling instances)
# Threads = 8 (Handle concurrent requests per instance)
# Timeout = 0 (Cloud Run handles timeouts)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app
