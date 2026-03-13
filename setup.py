from setuptools import setup, find_packages

setup(
    name="kalshi-trading-bot",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["config"],
    install_requires=[
        "websockets",
        "requests",
        "python-dotenv",
        "cryptography",
        "certifi",
        "prometheus_client"
    ]
)
