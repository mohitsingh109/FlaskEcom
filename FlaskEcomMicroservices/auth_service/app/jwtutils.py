import json
import logging

import jwt
import datetime

SECRET_KEY = "F5DB977622D67F7B78647F828D385"
ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_token(identity):
    payload = {
        "sub": json.dumps(identity),  # Serialize identity as JSON string
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded["sub"] = json.loads(decoded["sub"])  # Deserialize JSON string to dict
        return decoded
    except jwt.ExpiredSignatureError:
        logging.error("Token expired")
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        logging.error(f"Invalid token: {e}")
        return {"error": "Invalid token"}
