import importlib
import sys

def check_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError:
        print(f"❌ {module_name} - NÃO INSTALADO")
        return False

print("🔍 VERIFICANDO DEPENDÊNCIAS DO SIMULADOR")
print("=" * 40)

modules = [
    "numpy",
    "pandas",
    "plotly",
    "matplotlib",  # ESSENCIAL!
    "scipy",
    "skimage",     # scikit-image
    "streamlit",
    "openpyxl",
]

all_installed = True
for module in modules:
    if not check_module(module):
        all_installed = False

print("=" * 40)
if all_installed:
    print("🎉 TODAS AS DEPENDÊNCIAS ESTÃO INSTALADAS!")
    print("Execute: streamlit run app.py")
else:
    print("⚠️  ALGUMAS DEPENDÊNCIAS FALTANDO")
    print("Execute: pip install -r requirements.txt")
