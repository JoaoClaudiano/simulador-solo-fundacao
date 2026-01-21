"""
Exemplo de uso das funções de cálculo de fundações
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src import foundation_calculations as fc
import numpy as np

print("=" * 60)
print("EXEMPLO DE CÁLCULO DE FUNDAÇÕES")
print("=" * 60)

# Exemplo 1: Sapata
print("\n1. SAPATA QUADRADA")
print("-" * 40)

c = 10  # kPa
phi = 30  # graus
gamma = 18  # kN/m³
B = 1.5  # m
L = 1.5  # m
D_f = 1.0  # m

q_ult, (Nc, Nq, Nγ) = fc.bearing_capacity_terzaghi(
    c, phi, gamma, B, L, D_f, 'square'
)

print(f"Parâmetros do solo: c={c} kPa, φ={phi}°, γ={gamma} kN/m³")
print(f"Geometria: B={B}m, L={L}m, Df={D_f}m")
print(f"\nResultados:")
print(f"  Capacidade última: {q_ult:.1f} kPa")
print(f"  Fatores: Nc={Nc:.2f}, Nq={Nq:.2f}, Nγ={Nγ:.2f}")

# Exemplo 2: Estaca
print("\n\n2. ESTACA CRAVADA")
print("-" * 40)

# Camadas de solo
soil_layers = [
    {'depth_top': 0, 'depth_bottom': 5, 'c': 5, 'phi': 28, 'gamma': 18},
    {'depth_top': 5, 'depth_bottom': 15, 'c': 8, 'phi': 32, 'gamma': 19},
    {'depth_top': 15, 'depth_bottom': 25, 'c': 15, 'phi': 35, 'gamma': 20}
]

pile_dia = 0.6  # m
pile_length = 20  # m

total_capacity, shaft_capacity, tip_capacity = fc.pile_ultimate_capacity(
    soil_layers, pile_dia, pile_length, 'driven'
)

print(f"Estaca: diâmetro={pile_dia}m, comprimento={pile_length}m")
print(f"\nResultados:")
print(f"  Capacidade total: {total_capacity:.0f} kN")
print(f"  Atrito lateral: {shaft_capacity:.0f} kN ({shaft_capacity/total_capacity*100:.1f}%)")
print(f"  Ponta: {tip_capacity:.0f} kN ({tip_capacity/total_capacity*100:.1f}%)")

# Verificação
load_applied = 1200  # kN
FS, is_safe = fc.safety_factor(total_capacity, load_applied, 2.0)

print(f"\nVerificação para carga de {load_applied} kN:")
print(f"  Fator de segurança: {FS:.2f}")
print(f"  Seguro: {'SIM' if is_safe else 'NÃO'}")

print("\n" + "=" * 60)
print("Exemplo concluído com sucesso!")