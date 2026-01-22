from setuptools import setup, find_packages

setup(
    name="simulador-solo-fundacoes",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "pandas>=2.0.0",
        "plotly>=5.17.0",
        "matplotlib>=3.7.0",
        "openpyxl>=3.1.0",
        "reportlab>=4.0.0",
    ],
)