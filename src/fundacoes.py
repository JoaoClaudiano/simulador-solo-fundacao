"""
Cálculos para fundações rasas (sapatas) e profundas (estacas)
Versão 3.0 - Corrigido: Validação completa e consistência de unidades
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas as pd

class ValidacaoEntrada:
    """Classe para validação de entradas"""
    
    @staticmethod
    def validar_positivo(nome: str, valor: float, zero_permitido: bool = False) -> None:
        """Valida se valor é positivo"""
        if zero_permitido:
            if valor < 0:
                raise ValueError(f"{nome} não pode ser negativo")
        else:
            if valor <= 0:
                raise ValueError(f"{nome} deve ser positivo")
    
    @staticmethod
    def validar_angulo_atrito(phi: float) -> None:
        """Valida ângulo de atrito"""
        if phi < 0 or phi > 90:
            raise ValueError("Ângulo de atrito deve estar entre 0 e 90 graus")
    
    @staticmethod
    def validar_coeficiente_poisson(mu: float) -> None:
        """Valida coeficiente de Poisson"""
        if mu < 0 or mu >= 0.5:
            raise ValueError("Coeficiente de Poisson deve estar entre 0 e 0.5")

# ====================== FUNDAÇÕES RASAS (SAPATAS) ======================

def bearing_capacity_terzaghi(c: float, phi: float, gamma: float, 
                             B: float, L: float, D_f: float, 
                             foundation_type: str = 'strip') -> Tuple[float, Tuple]:
    """
    Capacidade de carga pela teoria de Terzaghi.
    
    Args:
        c: Coesão (kPa)
        phi: Ângulo de atrito (graus)
        gamma: Peso específico (kN/m³)
        B: Largura da fundação (m)
        L: Comprimento da fundação (m)
        D_f: Profundidade de embutimento (m)
        foundation_type: 'strip' (contínua), 'square' (quadrada), 'circular' (circular)
    
    Returns:
        q_ult: Capacidade de carga última (kPa)
        factors: Tupla com (Nc, Nq, Nγ)
    """
    # Validação de entrada
    ValidacaoEntrada.validar_positivo("Coesão", c, zero_permitido=True)
    ValidacaoEntrada.validar_angulo_atrito(phi)
    ValidacaoEntrada.validar_positivo("Peso específico", gamma)
    ValidacaoEntrada.validar_positivo("Largura", B)
    ValidacaoEntrada.validar_positivo("Comprimento", L)
    ValidacaoEntrada.validar_positivo("Profundidade", D_f, zero_permitido=True)
    
    if foundation_type not in ['strip', 'square', 'circular', 'rectangular']:
        raise ValueError("Tipo de fundação inválido")
    
    phi_rad = np.radians(phi)
    
    # Fatores de capacidade de carga
    if phi > 0:
        Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45 + phi/2)))**2
        Nc = (Nq - 1) / np.tan(phi_rad) if np.tan(phi_rad) > 0 else 5.14
        Nγ = 2 * (Nq + 1) * np.tan(phi_rad)
    else:
        Nc = 5.14
        Nq = 1.0
        Nγ = 0.0
    
    # Fatores de forma (shape factors)
    if foundation_type == 'strip':
        sc, sγ, sq = 1.0, 1.0, 1.0
    elif foundation_type == 'square':
        sc = 1.3
        sq = 1.0
        sγ = 0.8
    elif foundation_type == 'circular':
        sc = 1.3
        sq = 1.0
        sγ = 0.6
    elif foundation_type == 'rectangular':
        sc = 1 + 0.2 * (B/L)
        sq = 1 + 0.1 * (B/L) * np.tan(phi_rad)
        sγ = 1 - 0.4 * (B/L)
    
    # Cálculo da capacidade de carga
    q_ult = c * Nc * sc + gamma * D_f * Nq * sq + 0.5 * gamma * B * Nγ * sγ
    
    return max(q_ult, 0), (Nc, Nq, Nγ)

def elastic_settlement(q: float, B: float, Es: float, mu: float, 
                      foundation_shape: str = 'rectangular', 
                      L_over_B: float = 1.0) -> float:
    """
    Recalque elástico pela teoria da elasticidade.
    
    Args:
        q: Pressão aplicada (kPa)
        B: Largura da fundação (m)
        Es: Módulo de elasticidade do solo (kPa)
        mu: Coeficiente de Poisson do solo
        foundation_shape: 'rectangular', 'circular'
        L_over_B: Razão comprimento/largura (para retangular)
    
    Returns:
        settlement: Recalque (m)
    """
    # Validação de entrada
    ValidacaoEntrada.validar_positivo("Pressão aplicada", q)
    ValidacaoEntrada.validar_positivo("Largura", B)
    ValidacaoEntrada.validar_positivo("Módulo de elasticidade", Es)
    ValidacaoEntrada.validar_coeficiente_poisson(mu)
    
    # Fatores de influência (Is)
    if foundation_shape == 'circular':
        # Para fundação circular rígida
        Is = 0.79  # Fator de influência
        shape_factor = 1.0
    else:
        # Para fundação retangular
        m = L_over_B
        if m >= 10:
            Is = 2.0  # Sapata corrida
        else:
            # Cálculo simplificado do fator de influência
            Is = (1 - mu**2) * (0.73 + 0.27 * np.sqrt(m))
        shape_factor = 1.12  # Para média da distribuição de tensões
    
    settlement = (q * B * Is * shape_factor * (1 - mu**2)) / Es
    return max(settlement, 0)

def stress_bulb(B: float, L: float, depth_ratio: float = 3.0, 
               points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Gera pontos para visualização do bulbo de tensões.
    
    Args:
        B: Largura da fundação (m)
        L: Comprimento da fundação (m)
        depth_ratio: Profundidade máxima em relação a B
        points: Número de pontos para discretização
    
    Returns:
        X, Z, stress_ratio: Grid e valores de Δσ/q
    """
    # Validação de entrada
    ValidacaoEntrada.validar_positivo("Largura", B)
    ValidacaoEntrada.validar_positivo("Comprimento", L)
    ValidacaoEntrada.validar_positivo("Depth ratio", depth_ratio)
    if points < 10 or points > 1000:
        raise ValueError("Número de pontos deve estar entre 10 e 1000")
    
    # Malha de pontos
    x = np.linspace(-2*B, 2*B, points)
    z = np.linspace(0, depth_ratio*B, points)
    X, Z = np.meshgrid(x, z)
    
    # Cálculo simplificado do acréscimo de tensões (Boussinesq simplificado)
    stress_ratio = np.zeros_like(X)
    
    for i in range(points):
        for j in range(points):
            if Z[i,j] == 0:
                stress_ratio[i,j] = 1.0 if abs(X[i,j]) <= B/2 else 0
            else:
                # Distribuição 2:1 simplificada
                spread_dist = Z[i,j] * 0.5  # Propagação 2:1 (vertical:horizontal)
                effective_B = B + spread_dist
                effective_L = L + spread_dist
                
                if abs(X[i,j]) <= effective_B/2:
                    stress_ratio[i,j] = (B * L) / (effective_B * effective_L)
                else:
                    stress_ratio[i,j] = 0
    
    return X, Z, stress_ratio

# ====================== FUNÇÕES AUXILIARES ======================

def safety_factor(q_ult: float, q_applied: float, FS_min: float = 3.0) -> Tuple[float, bool]:
    """
    Calcula o fator de segurança e verifica se é aceitável.
    
    Args:
        q_ult: Capacidade última (kPa ou kN)
        q_applied: Carga aplicada (kPa ou kN)
        FS_min: Fator de segurança mínimo requerido
    
    Returns:
        FS: Fator de segurança calculado
        is_safe: Booleano indicando se é seguro
    """
    # Validação
    ValidacaoEntrada.validar_positivo("Capacidade última", q_ult)
    ValidacaoEntrada.validar_positivo("Carga aplicada", q_applied)
    ValidacaoEntrada.validar_positivo("FS mínimo", FS_min)
    
    if q_applied <= 0:
        return float('inf'), True
    
    FS = q_ult / q_applied
    is_safe = FS >= FS_min
    
    return FS, is_safe

def generate_report(foundation_type: str, params: Dict, results: Dict) -> str:
    """
    Gera um relatório textual com os resultados.
    
    Args:
        foundation_type: 'shallow' ou 'deep'
        params: Dicionário com parâmetros de entrada
        results: Dicionário com resultados calculados
    
    Returns:
        report: String com o relatório formatado
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("RELATÓRIO DE ANÁLISE DE FUNDAÇÃO")
    report_lines.append("=" * 60)
    
    report_lines.append("\n📋 PARÂMETROS DE ENTRADA:")
    for key, value in params.items():
        if isinstance(value, float):
            report_lines.append(f"  {key}: {value:.3f}")
        else:
            report_lines.append(f"  {key}: {value}")
    
    report_lines.append("\n📊 RESULTADOS:")
    for key, value in results.items():
        if isinstance(value, float):
            report_lines.append(f"  {key}: {value:.3f}")
        elif isinstance(value, tuple) and len(value) == 3:  # (Nc, Nq, Nγ)
            Nc, Nq, Nγ = value
            report_lines.append(f"  {key}: Nc={Nc:.2f}, Nq={Nq:.2f}, Nγ={Nγ:.2f}")
        else:
            report_lines.append(f"  {key}: {value}")
    
    # Verificação de segurança
    if 'FS' in results and 'is_safe' in results:
        safety_status = "✅ SEGURO" if results['is_safe'] else "⚠️  ATENÇÃO - Verificar"
        report_lines.append(f"\n🛡️  FATOR DE SEGURANÇA: {results['FS']:.2f} ({safety_status})")
    
    report_lines.append("\n" + "=" * 60)
    
    return "\n".join(report_lines)

# ====================== FUNÇÕES DE CONVERSÃO DE UNIDADES ======================

def kPa_para_kgfcm2(kpa: float) -> float:
    """Converte kPa para kgf/cm²"""
    return kpa / 98.0665

def kgfcm2_para_kpa(kgfcm2: float) -> float:
    """Converte kgf/cm² para kPa"""
    return kgfcm2 * 98.0665

def m_para_cm(m: float) -> float:
    """Converte metros para centímetros"""
    return m * 100

def cm_para_m(cm: float) -> float:
    """Converte centímetros para metros"""
    return cm / 100

def kN_para_tf(kn: float) -> float:
    """Converte kN para tf (tonelada-força)"""
    return kn / 9.80665

def tf_para_kN(tf: float) -> float:
    """Converte tf (tonelada-força) para kN"""
    return tf * 9.80665

# ====================== VALIDAÇÃO DE LIMITES NORMAIS ======================

def verificar_limites_nbr6122(parametros: Dict) -> List[str]:
    """
    Verifica se os parâmetros estão dentro dos limites da NBR 6122
    
    Returns:
        Lista de avisos/violações
    """
    avisos = []
    
    # Verificar dimensões mínimas
    if 'B' in parametros and parametros['B'] < 0.6:
        avisos.append(f"Largura B={parametros['B']:.2f}m < 0.6m (mínimo NBR 6122)")
    
    if 'L' in parametros and parametros['L'] < 0.6:
        avisos.append(f"Comprimento L={parametros['L']:.2f}m < 0.6m (mínimo NBR 6122)")
    
    # Verificar relação L/B
    if 'B' in parametros and 'L' in parametros and parametros['B'] > 0:
        relacao = parametros['L'] / parametros['B']
        if relacao > 3.0:
            avisos.append(f"Relação L/B={relacao:.1f} > 3.0 (máximo recomendado)")
    
    # Verificar pressão admissível típica
    if 'q_adm' in parametros:
        if parametros['q_adm'] > 1000:  # kPa
            avisos.append(f"Pressão admissível muito alta: {parametros['q_adm']:.0f} kPa")
        elif parametros['q_adm'] < 50:
            avisos.append(f"Pressão admissível muito baixa: {parametros['q_adm']:.0f} kPa")
    
    return avisos
