"""
Cálculos para fundações rasas (sapatas) e profundas (estacas)
"""
import numpy as np
from scipy import interpolate

# ====================== FUNDAÇÕES RASAS (SAPATAS) ======================

def bearing_capacity_terzaghi(c, phi, gamma, B, L, D_f, foundation_type='strip'):
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
    phi_rad = np.radians(phi)
    
    # Fatores de capacidade de carga
    Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45 + phi/2)))**2
    Nc = (Nq - 1) / np.tan(phi_rad) if phi > 0 else 5.14
    Nγ = 2 * (Nq + 1) * np.tan(phi_rad)
    
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
    else:
        sc, sγ, sq = 1.0, 1.0, 1.0
    
    # Cálculo da capacidade de carga
    q_ult = c * Nc * sc + gamma * D_f * Nq * sq + 0.5 * gamma * B * Nγ * sγ
    
    return q_ult, (Nc, Nq, Nγ)

def elastic_settlement(q, B, Es, mu, foundation_shape='rectangular', L_over_B=1.0):
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
    # Fatores de influência (Is)
    if foundation_shape == 'circular':
        # Para fundação circular rígida
        Is = 0.79  # Fator de influência
        shape_factor = 1.0
    else:
        # Para fundação retangular
        # Fator de profundidade (simplificado)
        Df_factor = 1.0  # Pode ser expandido
        m = L_over_B
        n = 1.0  # Relação profundidade/largura (simplificado)
        
        # Cálculo simplificado do fator de influência
        M = np.sqrt(1 + m**2)
        N = np.sqrt(1 + n**2)
        Is = (1/np.pi) * (m * np.log((M+1)/(M-1)) + np.log((N+1)/(N-1)))
        shape_factor = 1.12  # Para média da distribuição de tensões
    
    settlement = (q * B * Is * shape_factor * (1 - mu**2)) / Es
    return settlement

def stress_bulb(B, L, depth_ratio=3.0, points=50):
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

# ====================== FUNDAÇÕES PROFUNDAS (ESTACAS) ======================

def pile_ultimate_capacity(soil_layers, pile_diameter, pile_length, pile_type='driven'):
    """
    Calcula a capacidade última de uma estaca.
    
    Args:
        soil_layers: Lista de dicionários, cada um com:
            'depth_top', 'depth_bottom', 'c', 'phi', 'gamma', 'N_spt' (opcional)
        pile_diameter: Diâmetro da estaca (m)
        pile_length: Comprimento da estaca (m)
        pile_type: 'driven' (cravada) ou 'bored' (escavada)
    
    Returns:
        total_capacity: Capacidade última (kN)
        shaft_capacity: Capacidade por atrito lateral (kN)
        tip_capacity: Capacidade de ponta (kN)
    """
    # Inicialização
    shaft_capacity = 0.0
    tip_capacity = 0.0
    
    # Coeficientes reduzidos para estacas escavadas
    if pile_type == 'bored':
        alpha = 0.5  # Redução no atrito lateral
        beta = 0.7   # Redução na ponta
    else:
        alpha = 1.0
        beta = 1.0
    
    # Cálculo do atrito lateral ao longo do fuste
    for layer in soil_layers:
        layer_top = layer['depth_top']
        layer_bottom = layer['depth_bottom']
        
        # Limitar ao comprimento da estaca
        segment_top = max(layer_top, 0)
        segment_bottom = min(layer_bottom, pile_length)
        
        if segment_bottom <= segment_top:
            continue
        
        layer_thickness = segment_bottom - segment_top
        
        # Profundidade média do segmento
        avg_depth = (segment_top + segment_bottom) / 2
        
        # Tensão vertical efetiva na profundidade média
        sigma_v_eff = 0
        for soil in soil_layers:
            if soil['depth_top'] < avg_depth:
                soil_top = max(soil['depth_top'], 0)
                soil_bottom = min(soil['depth_bottom'], avg_depth)
                if soil_bottom > soil_top:
                    sigma_v_eff += soil['gamma'] * (soil_bottom - soil_top)
        
        # Resistência unitária ao atrito lateral
        if 'c' in layer and layer['c'] > 0:  # Solo coesivo
            if layer['c'] < 25:  # Argila mole
                f_s = alpha * 0.5 * layer['c']
            else:  # Argila rija
                f_s = alpha * 1.0 * layer['c']
        else:  # Solo granular
            K = 1.0  # Coeficiente de empuxo
            delta = layer['phi'] * 2/3  # Ângulo de atrito solo-estaca
            f_s = alpha * K * sigma_v_eff * np.tan(np.radians(delta))
        
        # Área lateral do segmento
        perimeter = np.pi * pile_diameter
        area_lateral = perimeter * layer_thickness
        
        shaft_capacity += f_s * area_lateral
    
    # Cálculo da capacidade de ponta
    # Encontrar a camada na ponta da estaca
    tip_layer = None
    for layer in soil_layers:
        if layer['depth_top'] <= pile_length <= layer['depth_bottom']:
            tip_layer = layer
            break
    
    if tip_layer:
        if 'c' in tip_layer and tip_layer['c'] > 0:  # Solo coesivo na ponta
            N_c = 9.0
            q_tip = beta * N_c * tip_layer['c']
        else:  # Solo granular na ponta
            N_q = 40  # Valor aproximado para φ=30°
            if 'phi' in tip_layer:
                phi_tip = tip_layer['phi']
                N_q = np.exp(np.pi * np.tan(np.radians(phi_tip))) * (np.tan(np.radians(45 + phi_tip/2)))**2
            
            # Tensão vertical efetiva na ponta
            sigma_v_tip = 0
            for soil in soil_layers:
                if soil['depth_top'] < pile_length:
                    soil_top = max(soil['depth_top'], 0)
                    soil_bottom = min(soil['depth_bottom'], pile_length)
                    if soil_bottom > soil_top:
                        sigma_v_tip += soil['gamma'] * (soil_bottom - soil_top)
            
            q_tip = beta * sigma_v_tip * N_q
        
        # Área da ponta
        area_tip = np.pi * (pile_diameter/2)**2
        tip_capacity = q_tip * area_tip
    
    total_capacity = shaft_capacity + tip_capacity
    
    return total_capacity, shaft_capacity, tip_capacity

def pile_settlement(total_load, shaft_capacity, tip_capacity, 
                   pile_diameter, pile_length, Es_soil, settlement_type='elastic'):
    """
    Estima o recalque de uma estaca.
    
    Args:
        total_load: Carga aplicada (kN)
        shaft_capacity: Capacidade por atrito lateral (kN)
        tip_capacity: Capacidade de ponta (kN)
        pile_diameter: Diâmetro (m)
        pile_length: Comprimento (m)
        Es_soil: Módulo de elasticidade do solo (kPa)
        settlement_type: 'elastic' ou 'load_transfer'
    
    Returns:
        settlement: Recalque total (m)
        breakdown: Dicionário com componentes do recalque
    """
    if settlement_type == 'elastic':
        # Método elástico simplificado
        area_cross = np.pi * (pile_diameter/2)**2
        settlement_shaft = (total_load * 0.5) / (Es_soil * pile_diameter)  # Simplificado
        settlement_tip = (total_load * 0.5) / (Es_soil * pile_diameter/2)  # Simplificado
        
        total_settlement = settlement_shaft + settlement_tip
        
        breakdown = {
            'shaft_settlement': settlement_shaft,
            'tip_settlement': settlement_tip,
            'elastic_component': total_settlement
        }
    else:
        # Método simplificado de transferência de carga
        load_ratio = min(total_load / (shaft_capacity + tip_capacity), 0.8)
        
        # Recalque simplificado baseado na relação carga-capacidade
        base_settlement = 0.01 * pile_diameter  # Recalque para carga de trabalho
        
        if load_ratio < 0.5:
            settlement = base_settlement * load_ratio * 2
        else:
            settlement = base_settlement + (load_ratio - 0.5) * base_settlement * 2
        
        total_settlement = settlement
        
        breakdown = {
            'load_ratio': load_ratio,
            'estimated_settlement': total_settlement
        }
    
    return total_settlement, breakdown

# ====================== FUNÇÕES AUXILIARES ======================

def safety_factor(q_ult, q_applied, FS_min=3.0):
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
    if q_applied <= 0:
        return float('inf'), True
    
    FS = q_ult / q_applied
    is_safe = FS >= FS_min
    
    return FS, is_safe

def generate_report(foundation_type, params, results):
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