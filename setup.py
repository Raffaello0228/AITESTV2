from setuptools import setup, find_packages

setup(
    name="ai_test",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "pandas",
        "pymysql",
        "sqlalchemy",
        "openpyxl",
        "requests",
    ],
)
