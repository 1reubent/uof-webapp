import os

# Copy this file to "db_config.py" (same folder) and fill in real values.
# Get these from the Aiven Console -> your MySQL service -> Overview -> Quick connect
# NEVER commit the real db_config.py file - it's already in .gitignore.

CONFIG_DIR = os.path.dirname(__file__)

DB_CONFIG = {
    "host": "your-service-name.aivencloud.com",
    "port": 12691,
    "user": "avnadmin",
    "password": "your-aiven-password",
    "database": "uof_project",
    # Aiven requires SSL. Download the CA cert from the service's Overview page
    # in the Aiven Console and save it as ca.pem in this same directory.
    "ssl_ca": os.path.join(CONFIG_DIR, "ca.pem"),
    "ssl_verify_cert": True,
    # The C extension (_mysql_connector) calls SSL_CTX_set_default_verify_paths()
    # unconditionally, which fails on macOS since it lacks the Linux-style default
    # cert store paths. use_pure avoids that call and uses ssl_ca directly.
    "use_pure": True,
}
