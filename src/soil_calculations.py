"""
Cálculos básicos de mecânica dos solos
"""
import numpy as np

def shear_strength(c, phi, sigma_n):
    """
    Calcula a resistência ao cisalhamento τ = c + σ*tan(φ)
    
    Args:
        c: coesão (kPa)
        phi: ângulo de atrito (graus)
        sigma_n: tensão normal (kPa)
    
    Returns:
        τ: resistência ao cisalhamento (kPa)
    """
    return c + sigma_n * np.tan(np.radians(phi))

def bearing_capacity_terzaghi(c, phi, gamma, B, D_f=0):
    """
    Capacidade de carga de Terzaghi para sapata contínua
    """
    Nq = np.exp(np.pi * np.tan(np.radians(phi))) * (np.tan(np.radians(45 + phi/2)))**2
    Nc = (Nq - 1) / np.tan(np.radians(phi)) if phi > 0 else 5.14
    Nγ = 2 * (Nq + 1) * np.tan(np.radians(phi))
    
    q_ult = c*Nc + gamma*D_f*Nq + 0.5*gamma*B*Nγ
    return q_ult, (Nc, Nq, Nγ)