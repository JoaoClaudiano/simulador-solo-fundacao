#!/bin/bash
# Script de instalação do Simulador Solo-Fundações

echo "🔧 Instalando dependências do Simulador Solo-Fundações..."

# Atualizar pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instalar dependências básicas
echo "📊 Instalando numpy, pandas, scipy..."
pip install numpy>=1.24.0 pandas>=2.0.0 scipy>=1.11.0

# Instalar visualização
echo "📈 Instalando plotly e matplotlib..."
pip install plotly>=5.17.0 matplotlib>=3.7.0

# Instalar scikit-image para 3D
echo "🌐 Instalando scikit-image para visualização 3D..."
pip install scikit-image>=0.21.0

# Instalar Streamlit e dependências web
echo "🌐 Instalando Streamlit..."
pip install streamlit>=1.28.0

# Instalar utilitários de exportação
echo "📤 Instalando utilitários de exportação..."
pip install openpyxl>=3.1.0 reportlab>=4.0.0

# Verificar instalação
echo "✅ Verificando instalação..."
python -c "import numpy, pandas, plotly, matplotlib, scipy, streamlit; print('✅ Todas as dependências instaladas com sucesso!')"

echo ""
echo "🎉 INSTALAÇÃO COMPLETA!"
echo "Para executar o aplicativo:"
echo "   streamlit run app.py"
