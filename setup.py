from setuptools import setup, find_packages

setup(
    name="sync_project",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary",
        "oracledb",
    ],
    entry_points={
        "console_scripts": [
            "sync-project=sync_project.sync:main",
        ],
    },
)
