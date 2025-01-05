FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh

# Expose the port the app runs on
EXPOSE 5001

ENTRYPOINT ["./entrypoint.sh"]
