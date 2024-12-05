FROM python:3.9-slim

WORKDIR /app

# Copy the requirements.txt file first to leverage Docker's caching mechanism
COPY requirements.txt /app/requirements.txt

# Install the dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app

EXPOSE 5000

CMD ["python", "main.py"]
