import os

from dotenv import load_dotenv

CONFIG_DIR = os.path.dirname(__file__)

# Loads backend/config/.env for local dev (gitignored). Does nothing if the file
# doesn't exist, e.g. on a production server, where these are set as real env vars instead.
load_dotenv(os.path.join(CONFIG_DIR, ".env"))

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": int(os.environ["DB_PORT"]),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "database": os.environ["DB_NAME"],
    # if you want to enable SSL, uncomment the following lines, comment out the ssl_disabled line,
    # and ensure the DB_SSL_CA_PATH environment variable is set to the correct path of the CA certificate.
    # "ssl_ca": os.path.join(CONFIG_DIR, os.environ["DB_SSL_CA_PATH"]),
    # "ssl_verify_cert": True,
    # "use_pure": True,
    "ssl_disabled": True,
}
