# Use Python's official image from the Docker registry
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Run the application using Gunicorn
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5004"]
