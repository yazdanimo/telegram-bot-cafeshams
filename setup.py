from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cafe-shams-news-bot",
    version="1.0.0",
    author="Cafe Shams",
    author_email="info@cafeshams.com",
    description="Automated news aggregation bot for Cafe Shams",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cafeshams/telegram-bot-cafeshams",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cafe-shams-bot=main:main",
        ],
    },
    keywords="telegram bot news rss automation cafe shams",
    project_urls={
        "Bug Reports": "https://github.com/cafeshams/telegram-bot-cafeshams/issues",
        "Source": "https://github.com/cafeshams/telegram-bot-cafeshams",
        "Channel": "https://t.me/cafeshamss",
    },
)
