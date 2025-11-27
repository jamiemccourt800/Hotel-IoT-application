#!/bin/bash
# runs the sample data script after a short delay to ensure MongoDB is ready
sleep 5
python3 /docker-entrypoint-initdb.d/sample-data.py