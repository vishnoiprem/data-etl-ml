# Run complete pipeline (generates data and creates reports)
python run_pipeline.py

# Skip data generation (use existing data)
python run_pipeline.py --no-generate

# Quick test with less data
python run_pipeline.py --quick

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_pipeline.py -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
