from prometheus_client import start_http_server

from app import create_app
from flask_migrate import Migrate
from app.models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    start_http_server(8000)
    app.run(host='0.0.0.0', port=5003)
