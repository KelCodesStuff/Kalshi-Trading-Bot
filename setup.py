from setuptools import setup, find_packages

setup(
    name="kalshi-trading-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "websockets",
        "requests",
        "python-dotenv",
        "cryptography",
        "certifi",
        "prometheus_client"
    ]
)
