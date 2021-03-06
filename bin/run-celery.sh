#!/usr/bin/env bash
set -e

CONCURRENCY="${CONCURRENCY:-2}"

echo "Start celery with CONCURRENCY: $CONCURRENCY"

exec celery -A glitchtip worker -l info --concurrency=$CONCURRENCY