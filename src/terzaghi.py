"""
MÓDULO TERZAGHI - Capacidade de carga e recalques
Implementação completa das teorias de Karl Terzaghi
"""
import numpy as np
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TerzaghiCapacity:
    """Capacidade de carga pelo método de Terzaghi (1943)"""
    
    @staticmethod
    def bearing_capacity(c: float, phi: float, gamma: float, 
                         B: float, L: float, D_f: float, 
                         water_table_depth: float = None,
                         shape: str = 'rectangular') -> Dict[str, float]:
        """
        Calcula capacidade de carga última (q_ult) e segura (q_adm)
        
        Args:
            c: Coesão [kPa]
            phi: Ângulo de atrito [°]
            gamma: Peso específico [kN/m³]
            B: Largura da sapata [m]
            L: Comprimento da sapata [m]
            D_f: Profundidade de assentamento [m]
            water_table_depth: Profundidade do NA [m]
            shape: 'square', 'rectangular', 'circular', 'strip'
            
        Returns:
            Dicionário com q_ult, q_adm, fatores Nc, Nq, Nγ
        """
        # Converter phi para radianos
        phi_rad = np.radians(phi)
        
        # Fatores de capacidade de carga (Terzaghi)
        Nq = (np.exp(np.pi * np.tan(phi_rad)) * 
              (np.tan(np.radians(45 + phi/2)))**2)
        
        Nc = (Nq - 1) / np.tan(phi_rad) if phi > 0 else 5.7
        
        # Terzaghi sugeriu Nγ ≈ (Nq-1)tan(1.4φ)
        Ngamma = (Nq - 1) * np.tan(np.radians(1.4 * phi)) if phi > 0 else 0
        
        # Fatores de forma
        if shape == 'square':
            sc, sq, sgamma = 1.3, 1.0, 0.8
        elif shape == 'rectangular':
            sc = 1 + 0.3 * (B/L)
            sq = 1 + 0.2 * (B/L)
            sgamma = 1 - 0.4 * (B/L)  # B é a menor dimensão
        elif shape == 'circular':
            sc, sq, sgamma = 1.3, 1.0, 0.6
        elif shape == 'strip':  # sapata corrida
            sc, sq, sgamma = 1.0, 1.0, 1.0
        
        # Fatores de profundidade (simplificado)
        dc = 1 + 0.4 * (D_f/B)
        dq = 1 + 0.2 * (D_f/B) * np.tan(np.radians(45 + phi/2))
        dgamma = 1.0
        
        # Correção do NA (nível d'água)
        gamma_effective = gamma
        if water_table_depth is not None:
            if water_table_depth <= D_f:
                # NA acima da base
                gamma_effective = gamma - 9.81  # γ_submerso
            elif water_table_depth <= D_f + B:
                # NA entre a base e B abaixo
                gamma_effective = gamma - 9.81 * (water_table_depth - D_f) / B
        
        # Equação de Terzaghi
        q_ult = (c * Nc * sc * dc + 
                 gamma * D_f * Nq * sq * dq + 
                 0.5 * gamma_effective * B * Ngamma * sgamma * dgamma)
        
        # Capacidade admissível (FS = 3)
        q_adm = q_ult / 3.0
        
        return {
            'q_ult': q_ult,
            'q_adm': q_adm,
            'fator_seguranca': 3.0,
            'Nc': Nc,
            'Nq': Nq,
            'Ngamma': Ngamma,
            'sc': sc, 'sq': sq, 'sgamma': sgamma,
            'dc': dc, 'dq': dq, 'dgamma': dgamma
        }
    
    @staticmethod
    def settlement_elastic(q: float, B: float, L: float,
                          E: float, mu: float, depth_factor: float = 1.0,
                          foundation_type: str = 'flexible') -> float:
        """
        Recalque elástico imediato (solução elástica)
        
        Args:
            q: Pressão líquida [kPa]
            B, L: Dimensões [m]
            E: Módulo de elasticidade [kPa]
            mu: Coeficiente de Poisson
            depth_factor: Fator de profundidade
            foundation_type: 'flexible' ou 'rigid'
            
        Returns:
            Recalque [m]
        """
        # Fator de influência (Giroud, 1972)
        if L/B >= 10:  # Sapata corrida
            I = np.pi * (1 - mu**2) / 2
        else:
            # Para sapatas retangulares
            m = L/B
            I = (1 - mu**2) * (0.73 + 0.27 * np.sqrt(m))
        
        # Fator de rigidez
        if foundation_type == 'rigid':
            I *= 0.8
        
        settlement = (q * B * I * depth_factor) / E
        return settlement
    
    @staticmethod
    def settlement_consolidation(soil_layers: list, 
                                delta_sigma: np.ndarray,
                                time_years: float = 1.0) -> Dict[str, Any]:
        """
        Recalque por adensamento (Teoria de Terzaghi 1D)
        
        Args:
            soil_layers: Lista de dicts com {'h', 'Cc', 'Cr', 'e0', 'sigma_v0', 'OCR'}
            delta_sigma: Acréscimo de tensão em cada camada [kPa]
            time_years: Tempo para calcular recalque [anos]
            
        Returns:
            Dicionário com recalques total, primário, secundário
        """
        total_settlement = 0
        primary_settlement = 0
        layer_settlements = []
        
        for i, layer in enumerate(soil_layers):
            h = layer['h']
            Cc = layer.get('Cc', 0)  # Índice de compressão
            Cr = layer.get('Cr', 0)  # Índice de recompressão
            e0 = layer.get('e0', 1.0)
            sigma_v0 = layer.get('sigma_v0', 0)
            OCR = layer.get('OCR', 1.0)  # Razão de sobre-adensamento
            
            sigma_v_final = sigma_v0 + delta_sigma[i]
            
            if sigma_v_final > sigma_v0:
                if sigma_v_final > OCR * sigma_v0:  # Adensamento normal
                    settlement = (Cc * h / (1 + e0)) * np.log10(sigma_v_final / sigma_v0)
                else:  # Recompressão
                    settlement = (Cr * h / (1 + e0)) * np.log10(sigma_v_final / sigma_v0)
                
                total_settlement += settlement
                layer_settlements.append(settlement)
        
        # Fator tempo (simplificado)
        U = 1 - np.exp(-0.5 * time_years)  # Grau de adensamento
        
        return {
            'total_settlement': total_settlement,
            'primary_settlement': total_settlement * U,
            'degree_of_consolidation': U,
            'layer_settlements': layer_settlements
        }

class FoundationDesign:
    """Classe para projeto completo de fundações"""
    
    def __init__(self):
        self.terzaghi = TerzaghiCapacity()
    
    def complete_design(self, soil_params: Dict, 
                       foundation_params: Dict,
                       load_params: Dict) -> Dict[str, Any]:
        """
        Projeto completo: capacidade + recalques + verificação
        
        Args:
            soil_params: c, phi, gamma, E, etc.
            foundation_params: B, L, D_f, shape
            load_params: q_applied, load_type
            
        Returns:
            Dicionário com todos os resultados do projeto
        """
        try:
            # 1. Capacidade de carga
            bearing = self.terzaghi.bearing_capacity(
                c=soil_params['c'],
                phi=soil_params['phi'],
                gamma=soil_params['gamma'],
                B=foundation_params['B'],
                L=foundation_params['L'],
                D_f=foundation_params['D_f'],
                shape=foundation_params.get('shape', 'rectangular')
            )
            
            # 2. Verificação de segurança
            q_applied = load_params['q_applied']
            fs_calculated = bearing['q_ult'] / q_applied if q_applied > 0 else float('inf')
            
            safety_status = 'SAFE' if fs_calculated >= 3.0 else 'FAIL'
            
            # 3. Recalques (simplificado) - agora em mm
            settlement_m = self.terzaghi.settlement_elastic(
                q=q_applied,
                B=foundation_params['B'],
                L=foundation_params['L'],
                E=soil_params.get('E', 30000),
                mu=soil_params.get('mu', 0.3)
            )
            settlement_mm = settlement_m * 1000  # Converter para mm
            
            # 4. Verificação de recalques (em mm)
            settlement_limit = 25.0  # 25 mm
            settlement_status = 'OK' if settlement_mm <= settlement_limit else 'EXCESSIVE'
            
            # 5. Gerar recomendações (ajustado para mm)
            recommendations = self._generate_recommendations(fs_calculated, settlement_mm)
            
            # 6. Criar resumo do projeto
            design_summary = self._create_design_summary(
                soil_params, foundation_params, load_params,
                bearing, fs_calculated, settlement_mm, safety_status,
                settlement_status, recommendations
            )
            
            return {
                'success': True,
                'bearing_capacity': bearing,
                'safety_check': {
                    'q_applied': q_applied,
                    'q_ult': bearing['q_ult'],
                    'fs_calculated': fs_calculated,
                    'fs_required': 3.0,
                    'status': safety_status,
                    'color': 'green' if safety_status == 'SAFE' else 'red'
                },
                'settlement': {
                    'settlement_mm': settlement_mm,
                    'limit_mm': settlement_limit,
                    'status': settlement_status
                },
                'recommendations': recommendations,
                'design_summary': design_summary
            }
            
        except Exception as e:
            # Retornar erro formatado
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_recommendations(self, fs: float, settlement_mm: float) -> list:
        """Gera recomendações de projeto (ajustado para mm)"""
        recommendations = []
        
        if fs < 2.0:
            recommendations.append(
                "❌ AUMENTAR DIMENSÕES: Fator de segurança muito baixo (FS < 2.0)"
            )
        elif fs < 3.0:
            recommendations.append(
                "⚠️ CONSIDERAR AUMENTO: FS abaixo do recomendado (FS < 3.0)"
            )
        else:
            recommendations.append(
                "✅ FS ADEQUADO: Fator de segurança ≥ 3.0"
            )
        
        if settlement_mm > 25.0:
            recommendations.append(
                f"❌ MELHORAR SOLO: Recalque {settlement_mm:.1f} mm > limite 25 mm"
            )
        elif settlement_mm > 15.0:
            recommendations.append(
                f"⚠️ RECALQUE ELEVADO: {settlement_mm:.1f} mm (limite: 25 mm)"
            )
        else:
            recommendations.append(
                f"✅ RECALQUE ACEITÁVEL: {settlement_mm:.1f} mm ≤ 15 mm (recomendado)"
            )
        
        if fs >= 3.0 and settlement_mm <= 15.0:
            recommendations.append("🎯 PROJETO OTIMIZADO: Atende todos os critérios com folga")
        
        return recommendations
    
    def _create_design_summary(self, soil_params, foundation_params, load_params,
                              bearing, fs, settlement_mm, safety_status, 
                              settlement_status, recommendations) -> str:
        """Cria resumo textual do projeto"""
        summary = f"""
================================================
RELATÓRIO DE PROJETO DE FUNDAÇÃO - TERZAGHI
================================================

PARÂMETROS DO SOLO:
- Coesão (c): {soil_params['c']} kPa
- Ângulo de atrito (φ): {soil_params['phi']}°
- Peso específico (γ): {soil_params['gamma']} kN/m³
- Módulo de elasticidade (E): {soil_params.get('E', 30000)} kPa

PARÂMETROS DA FUNDAÇÃO:
- Largura (B): {foundation_params['B']} m
- Comprimento (L): {foundation_params['L']} m
- Profundidade (D_f): {foundation_params['D_f']} m
- Forma: {foundation_params.get('shape', 'retangular')}

CARREGAMENTO:
- Pressão aplicada (q): {load_params['q_applied']} kPa

RESULTADOS:
1. CAPACIDADE DE CARGA:
   - q_ult = {bearing['q_ult']:.1f} kPa
   - q_adm (FS=3) = {bearing['q_adm']:.1f} kPa
   - Fatores: Nc={bearing['Nc']:.2f}, Nq={bearing['Nq']:.2f}, Nγ={bearing['Ngamma']:.2f}

2. VERIFICAÇÃO DE SEGURANÇA:
   - FS calculado = {fs:.2f}
   - Status: {safety_status}

3. RECALQUES:
   - Recalque imediato = {settlement_mm:.1f} mm
   - Status: {settlement_status}

4. RECOMENDAÇÕES:
"""
        
        for i, rec in enumerate(recommendations, 1):
            summary += f"   {i}. {rec}\n"
        
        summary += f"\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        return summary