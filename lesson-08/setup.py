"""
CryptoAutoTrader 설치 스크립트
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="crypto-auto-trader",
    version="1.0.0",
    author="CryptoAutoTrader Team",
    description="암호화폐 자동매매 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/crypto-auto-trader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.3.2",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "requests>=2.31.0",
        "pyupbit>=0.2.31",
        "PyYAML>=6.0.1",
        "python-telegram-bot>=20.4",
        "matplotlib>=3.7.2",
    ],
)

