#!/usr/bin/env python
"""Setup script for NPersona package."""

from setuptools import setup, find_packages
import os

# The actual package is in npersona/npersona/
setup(
    name="npersona",
    version="1.0.4",
    packages=find_packages(where="npersona", include=["npersona", "npersona.*"]),
    package_dir={"": "npersona"},
    install_requires=[
        "pydantic>=2.0",
        "litellm>=1.40.0",
        "httpx>=0.27.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "tenacity>=8.2.0",
    ],
    extras_require={
        "pdf": ["pypdf>=4.0.0"],
        "docx": ["python-docx>=1.1.0"],
        "all": ["pypdf>=4.0.0", "python-docx>=1.1.0"],
        "deepeval": ["deepeval>=0.21.0"],
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=5.0.0",
            "ruff>=0.4.0",
            "mypy>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "npersona=npersona.cli:main",
        ],
    },
    python_requires=">=3.9",
    author="NPersona-AI",
    author_email="npersona.ai@gmail.com",
    description="AI Security Testing Framework - Comprehensive adversarial testing for AI systems",
    long_description=open("README.md", encoding="utf-8").read() if False else "AI Security Testing Framework",
    long_description_content_type="text/markdown",
    url="https://github.com/NPersona-AI/NPersona",
    project_urls={
        "Repository": "https://github.com/NPersona-AI/NPersona.git",
        "Issues": "https://github.com/NPersona-AI/NPersona/issues",
        "Documentation": "https://github.com/NPersona-AI/NPersona#documentation",
        "Discussions": "https://github.com/NPersona-AI/NPersona/discussions",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
    ],
    keywords=[
        "ai",
        "security",
        "testing",
        "adversarial",
        "llm",
        "prompt-injection",
        "jailbreak",
    ],
)
