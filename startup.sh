#!/bin/bash

echo "=== Travel Planner Agent Startup ==="
echo "Timestamp: $(date)"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Available memory: $(free -h 2>/dev/null || echo 'Memory info not available')"
echo "Environment PORT: ${PORT:-8080}"

echo "=== Running startup tests ==="
python test_startup.py
if [ $? -ne 0 ]; then
    echo "Startup tests failed, but continuing anyway..."
fi

echo "=== Starting gunicorn server ==="
exec gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT:-8080} --timeout 300 --keep-alive 2 --log-level info app:app
