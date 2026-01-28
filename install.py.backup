#!/usr/bin/env python3
"""
Script de instalação das dependências do Simulador Solo-Fundações
"""

import subprocess
import sys

def install_packages():
    """Instala todas as dependências do projeto"""
    
    packages = [
        "numpy>=1.24.0,<2.0.0",
        "pandas>=2.0.0,<3.0.0",
        "scipy>=1.11.0,<2.0.0",
        "plotly>=5.17.0,<6.0.0",
        "scikit-image>=0.21.0,<0.22.0",
        "streamlit>=1.28.0,<2.0.0",
        "streamlit-aggrid>=0.3.0,<0.4.0",
        "streamlit-option-menu>=0.3.0,<0.4.0",
        "openpyxl>=3.1.0,<4.0.0",
        "reportlab>=4.0.0,<5.0.0",
        "typing-extensions>=4.5.0,<5.0.0",
        "python-dateutil>=2.8.2,<3.0.0",
        "pytz>=2023.3,<2024.0",
        "packaging>=23.0,<24.0"
    ]
    
    print("🔧 Instalando dependências do Simulador Solo-Fundações...")
    
    for package in packages:
        print(f"📦 Instalando: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ Todas as dependências instaladas com sucesso!")

if __name__ == "__main__":
    install_packages()
