#!/bin/bash

# Start generating dummy orders
echo "🛒 Starting live order generation..."
pip install psycopg2-binary faker
python dashboard/data_generator.py