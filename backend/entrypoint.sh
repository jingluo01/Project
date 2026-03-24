#!/bin/bash
set -e

# Wait for MySQL to be ready
echo "Waiting for MySQL to start..."
while ! nc -z mysql 3306; do
  sleep 1
done
echo "MySQL is up and running!"

# Run migrations/initializations
echo "Checking if database needs initialization..."
# python init_school_db.py
python init_db.py

# Execute the CMD passed into the Docker container
echo "Starting Gunicorn server..."
exec "$@"
