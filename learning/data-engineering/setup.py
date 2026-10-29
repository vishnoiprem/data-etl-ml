from setuptools import setup, find_packages

setup(
    name="scb_aml_platform",
    version="1.0.0",
    description="SCB AML Platform — End-to-End Anti-Money Laundering Data Platform",
    author="Prem Vishnoi",
    author_email="prem.vishnoi@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0",
        "numpy>=1.24",
        "jellyfish>=0.11",
        "fuzzywuzzy>=0.18",
        "faker>=19",
        "loguru>=0.7",
        "fastapi>=0.103",
        "uvicorn>=0.23",
        "pyarrow>=12",
    ],
)
