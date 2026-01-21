"""
Testes unitários para funções de fundações
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from src import foundation_calculations as fc

def test_bearing_capacity_terzaghi():
    """Teste da capacidade de carga de Terzaghi"""
    # Valores conhecidos para φ=30°
    c = 0
    phi = 30
    gamma = 18
    B = 1.0
    L = 1.0
    D_f = 0
    
    q_ult, (Nc, Nq, Nγ) = fc.bearing_capacity_terzaghi(
        c, phi, gamma, B, L, D_f, 'strip'
    )
    
    # Verificar fatores (valores teóricos para φ=30°)
    assert abs(Nq - 18.40) < 0.1  # Nq teórico = 18.40
    assert abs(Nγ - 22.40) < 0.1  # Nγ teórico ≈ 22.40
    
def test_safety_factor():
    """Teste do cálculo do fator de segurança"""
    # Caso seguro
    FS, is_safe = fc.safety_factor(300, 100, 2.0)
    assert FS == 3.0
    assert is_safe == True
    
    # Caso não seguro
    FS, is_safe = fc.safety_factor(150, 100, 2.0)
    assert FS == 1.5
    assert is_safe == False
    
def test_pile_capacity():
    """Teste simplificado da capacidade de estaca"""
    soil_layers = [
        {'depth_top': 0, 'depth_bottom': 10, 'c': 10, 'phi': 30, 'gamma': 18}
    ]
    
    total_capacity, shaft_capacity, tip_capacity = fc.pile_ultimate_capacity(
        soil_layers, 0.5, 10, 'driven'
    )
    
    # Verificar se os valores são positivos e razoáveis
    assert total_capacity > 0
    assert shaft_capacity >= 0
    assert tip_capacity >= 0
    assert abs(total_capacity - (shaft_capacity + tip_capacity)) < 0.01

def test_elastic_settlement():
    """Teste do cálculo de recalque elástico"""
    settlement = fc.elastic_settlement(
        q=200,  # kPa
        B=1.5,  # m
        Es=50000,  # kPa
        mu=0.3,
        foundation_shape='rectangular',
        L_over_B=1.0
    )
    
    # Verificar se o recalque é positivo e razoável
    assert settlement > 0
    assert settlement < 0.1  # Menos que 10 cm

if __name__ == "__main__":
    # Executar testes
    test_bearing_capacity_terzaghi()
    test_safety_factor()
    test_pile_capacity()
    test_elastic_settlement()
    print("✅ Todos os testes passaram!")