from setuptools import setup, find_packages

setup(
    name="distributed-crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests==2.31.0',
        'beautifulsoup4==4.12.2',
        'python-memcached==1.59',
        'redis==5.0.1',
        'pybloom-live==2.3.1',
        'python-dotenv==1.0.0',
        'aiohttp==3.9.1'
    ],
    entry_points={
        'console_scripts': [
            'crawler=crawler.crawler:main'
        ]
    }
)
