#!/bin/bash

# Run Celery worker for lecture processing
celery -A src.4_infrastructure.queue.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=lecture_processing
