from prometheus_client import start_http_server

from app.routes import app

if __name__ == "__main__":
    start_http_server(8000)
    app.run(host="0.0.0.0", port=5000)
