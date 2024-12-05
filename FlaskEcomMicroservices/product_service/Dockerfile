# Use a Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the application files
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Set the environment variable for Flask
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Run the app with Gunicorn
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5001"]
