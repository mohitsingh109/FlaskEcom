FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh

EXPOSE 5003

ENTRYPOINT ["./entrypoint.sh"]
