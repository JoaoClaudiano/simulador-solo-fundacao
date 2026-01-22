"""
Setup do Simulador Solo-Fundações
"""
from setuptools import setup, find_packages

setup(
    name="simulador-solo-fundacao",
    version="2.3.0",
    author="João Claudiano",
    description="Simulador de Tensões no Solo para Fundações",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "plotly>=5.17.0",
        "matplotlib>=3.7.0",      # ADICIONADO
        "scipy>=1.11.0",
        "scikit-image>=0.21.0",
        "streamlit>=1.28.0",
        "openpyxl>=3.1.0",
    ],
    python_requires=">=3.9",
)
