"""
MÓDULO TERZAGHI - Capacidade de carga e recalques
Implementação completa das teorias de Karl Terzaghi
Versão 3.0 - Corrigido: Removida duplicação, corrigido método aninhado
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TerzaghiCapacity:
    """Capacidade de carga pelo método de Terzaghi (1943)"""
    
    @staticmethod
    def bearing_capacity_basic(c: float, phi: float, gamma: float,
                              B: float, L: float, D_f: float,
                              shape: str = 'rectangular') -> Dict[str, Any]:
        """
        Capacidade de carga básica pelo método de Terzaghi.
        
        Args:
            c: Coesão [kPa]
            phi: Ângulo de atrito [°]
            gamma: Peso específico [kN/m³]
            B, L: Dimensões da sapata [m]
            D_f: Profundidade de assentamento [m]
            shape: Forma da sapata ('strip', 'square', 'circular', 'rectangular')
            
        Returns:
            Dicionário com resultados
        """
        # Validação de entrada
        if B <= 0 or L <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")
        if D_f < 0:
            raise ValueError("Profundidade de embutimento não pode ser negativa")
        
        phi_rad = np.radians(phi)
        
        # Fatores de capacidade de carga
        if phi > 0:
            Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45 + phi/2)))**2
            Nc = (Nq - 1) / np.tan(phi_rad) if np.tan(phi_rad) > 0 else 5.14
            Ngamma = 2 * (Nq + 1) * np.tan(phi_rad)
        else:
            Nc = 5.14
            Nq = 1.0
            Ngamma = 0.0
        
        # Fatores de forma
        if shape == 'strip':
            sc, sq, sgamma = 1.0, 1.0, 1.0
        elif shape == 'square':
            sc, sq, sgamma = 1.3, 1.0, 0.8
        elif shape == 'circular':
            sc, sq, sgamma = 1.3, 1.0, 0.6
        elif shape == 'rectangular':
            sc = 1 + 0.2 * (B/L)
            sq = 1 + 0.1 * (B/L) * np.sin(phi_rad)
            sgamma = 1 - 0.4 * (B/L)
        else:
            raise ValueError(f"Forma {shape} não suportada")
        
        # Cálculo da capacidade de carga
        term1 = c * Nc * sc
        term2 = gamma * D_f * Nq * sq
        term3 = 0.5 * gamma * B * Ngamma * sgamma
        
        q_ult = term1 + term2 + term3
        q_adm = q_ult / 3.0  # FS = 3
        
        return {
            'q_ult': q_ult,
            'q_adm': q_adm,
            'Nc': Nc,
            'Nq': Nq,
            'Ngamma': Ngamma,
            'sc': sc,
            'sq': sq,
            'sgamma': sgamma
        }
    
    @staticmethod
    def bearing_capacity_advanced(c: float, phi: float, gamma: float,
                                 B: float, L: float, D_f: float,
                                 water_table_depth: Optional[float] = None,
                                 shape: str = 'rectangular',
                                 load_inclination: float = 0.0,
                                 load_eccentricity_x: float = 0.0,
                                 load_eccentricity_y: float = 0.0,
                                 surcharge: float = 0.0) -> Dict[str, float]:
        """
        Capacidade de carga avançada com correções completas
        
        Args:
            c: Coesão [kPa]
            phi: Ângulo de atrito [°]
            gamma: Peso específico [kN/m³]
            B, L: Dimensões da sapata [m]
            D_f: Profundidade de assentamento [m]
            water_table_depth: Profundidade do NA [m]
            shape: Forma da sapata
            load_inclination: Inclinação da carga [°]
            load_eccentricity_x: Excentricidade em x [m]
            load_eccentricity_y: Excentricidade em y [m]
            surcharge: Sobrecarga na superfície [kPa]
            
        Returns:
            Dicionário com resultados avançados
        """
        # Validação de entrada
        if B <= 0 or L <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")
        if D_f < 0:
            raise ValueError("Profundidade de embutimento não pode ser negativa")
        
        # Converter phi para radianos
        phi_rad = np.radians(phi)
        
        # 1. Fatores de capacidade de carga (Vesic, 1973 - mais preciso)
        if phi > 0:
            Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45 + phi/2)))**2
            Nc = (Nq - 1) / np.tan(phi_rad) if np.tan(phi_rad) > 0 else 5.14
            Ngamma = 2 * (Nq + 1) * np.tan(phi_rad)  # Vesic
        else:
            Nc = 5.14  # Valor exato para φ=0 (Prandtl)
            Nq = 1.0
            Ngamma = 0.0
        
        # 2. Fatores de forma (De Beer, 1970)
        if shape == 'square':
            sc = 1.3
            sq = 1.0
            sgamma = 0.8
        elif shape == 'rectangular':
            sc = 1 + 0.2 * (B/L)
            sq = 1 + 0.1 * (B/L) * np.sin(phi_rad)
            sgamma = 1 - 0.4 * (B/L)
        elif shape == 'strip':
            sc, sq, sgamma = 1.0, 1.0, 1.0
        elif shape == 'circular':
            sc, sq, sgamma = 1.3, 1.0, 0.6
        else:
            raise ValueError(f"Forma {shape} não suportada")
        
        # 3. Fatores de profundidade (Hansen, 1970)
        if D_f/B <= 1:
            dc = 1 + 0.4 * (D_f/B)
            dq = 1 + 0.1 * (D_f/B) * np.sqrt(np.tan(np.radians(45 + phi/2)))
        else:
            dc = 1 + 0.4 * np.arctan(D_f/B)
            dq = 1 + 0.1 * np.arctan(D_f/B) * np.sqrt(np.tan(np.radians(45 + phi/2)))
        
        dgamma = 1.0
        
        # 4. Fatores de inclinação (Meyerhof, 1963)
        alpha_rad = np.radians(load_inclination)
        if phi == 0:
            ic = (1 - alpha_rad/(np.pi/2))**2
        else:
            ic = (1 - alpha_rad/phi_rad)**2
        iq = (1 - 0.7 * np.tan(alpha_rad))**3
        igamma = (1 - np.tan(alpha_rad))**3
        
        # 5. Fatores de excentricidade (área efetiva)
        if load_eccentricity_x != 0 or load_eccentricity_y != 0:
            B_eff = B - 2 * abs(load_eccentricity_x)
            L_eff = L - 2 * abs(load_eccentricity_y)
            area_eff = B_eff * L_eff
        else:
            B_eff = B
            L_eff = L
            area_eff = B * L
        
        # 6. Correção do nível d'água
        gamma_effective = gamma
        gamma_d_f = gamma
        
        if water_table_depth is not None:
            if water_table_depth <= D_f:
                # NA acima da base
                gamma_effective = max(gamma - 9.81, 0)
                gamma_d_f = max(gamma - 9.81, 0)
            elif water_table_depth <= D_f + B_eff:
                # NA entre a base e B abaixo
                factor = (water_table_depth - D_f) / B_eff
                gamma_effective = gamma - 9.81 * factor
                gamma_d_f = gamma
            else:
                # NA abaixo de D_f + B
                gamma_effective = gamma
                gamma_d_f = gamma
        
        # 7. Equação geral de capacidade de carga (Hansen)
        term1 = c * Nc * sc * dc * ic
        term2 = (gamma_d_f * D_f + surcharge) * Nq * sq * dq * iq
        term3 = 0.5 * gamma_effective * B_eff * Ngamma * sgamma * dgamma * igamma
        
        q_ult = term1 + term2 + term3
        
        # 8. Capacidade líquida (sem o peso do solo)
        q_net = q_ult - gamma_d_f * D_f
        
        # 9. Capacidade admissível com diferentes FS
        q_adm_fs2 = q_ult / 2.0
        q_adm_fs3 = q_ult / 3.0
        
        return {
            'q_ult': q_ult,
            'q_net': q_net,
            'q_adm_fs2': q_adm_fs2,
            'q_adm_fs3': q_adm_fs3,
            'Nc': Nc,
            'Nq': Nq,
            'Ngamma': Ngamma,
            'sc': sc, 'sq': sq, 'sgamma': sgamma,
            'dc': dc, 'dq': dq, 'dgamma': dgamma,
            'ic': ic, 'iq': iq, 'igamma': igamma,
            'B_eff': B_eff,
            'L_eff': L_eff,
            'gamma_effective': gamma_effective,
            'gamma_d_f': gamma_d_f
        }
    
    @staticmethod
    def settlement_advanced(q: float, B: float, L: float,
                           soil_layers: List[Dict[str, Any]],
                           foundation_type: str = 'flexible',
                           time_years: float = 1.0) -> Dict[str, Any]:
        """
        Cálculo avançado de recalques (imediato + adensamento)
        
        Args:
            q: Pressão aplicada [kPa]
            B, L: Dimensões da sapata [m]
            soil_layers: Lista de dicionários com propriedades das camadas
            foundation_type: 'flexible' ou 'rigid'
            time_years: Tempo para cálculo de adensamento [anos]
            
        Returns:
            Dicionário com todos os recalques
        """
        # Validação
        if q <= 0:
            raise ValueError("Pressão aplicada deve ser positiva")
        if B <= 0 or L <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")
        
        resultados = {
            'settlement_immediate': 0.0,
            'settlement_consolidation': 0.0,
            'settlement_total': 0.0,
            'degree_of_consolidation': 0.0,
            'time_years': time_years,
            'layer_settlements': []
        }
        
        if not soil_layers:
            return resultados
        
        # 1. Recalque imediato (Schmertmann, 1970)
        # Fator de forma
        if L/B >= 10:
            I = 0.6  # Sapata corrida
        else:
            I = 0.8  # Sapata retangular
        
        # Fator de profundidade
        H = sum(layer.get('thickness', 0) for layer in soil_layers)
        depth_factor = min(1.0, H/(2*B))
        
        # Módulo equivalente (média ponderada)
        E_avg = 0
        total_thickness = 0
        
        for layer in soil_layers:
            E = layer.get('E', 30000)
            thickness = layer.get('thickness', 0)
            E_avg += E * thickness
            total_thickness += thickness
        
        if total_thickness > 0:
            E_avg /= total_thickness
        
        # Recalque imediato (Schmertmann)
        settlement_immediate = (q * B * I * depth_factor) / max(E_avg, 1.0)
        resultados['settlement_immediate'] = settlement_immediate * 1000  # mm
        
        # 2. Recalque por adensamento (Terzaghi 1D)
        settlement_consolidation = 0.0
        layer_settlements = []
        
        for i, layer in enumerate(soil_layers):
            thickness = layer.get('thickness', 0)
            if thickness <= 0:
                continue
                
            Cc = layer.get('Cc', 0.3)  # Índice de compressão
            Cr = layer.get('Cr', 0.05)  # Índice de recompressão
            e0 = layer.get('e0', 1.0)
            sigma_v0 = layer.get('sigma_v0', 0.0)
            OCR = layer.get('OCR', 1.0)  # Razão de sobre-adensamento
            
            # Acréscimo de tensão (simplificado - Boussinesq)
            z = sum(l.get('thickness', 0) for l in soil_layers[:i]) + thickness/2
            delta_sigma = q * (1 / (1 + (z/B)**2))**1.5  # Simplificação
            
            sigma_v_final = sigma_v0 + delta_sigma
            
            if sigma_v_final > sigma_v0:
                if sigma_v_final > OCR * sigma_v0:
                    # Zona virgem
                    settlement = (Cc * thickness / (1 + e0)) * np.log10(sigma_v_final / max(sigma_v0, 0.1))
                else:
                    # Recompressão
                    settlement = (Cr * thickness / (1 + e0)) * np.log10(sigma_v_final / max(sigma_v0, 0.1))
                
                settlement_consolidation += settlement
                layer_settlements.append({
                    'layer': i+1,
                    'thickness': thickness,
                    'settlement': settlement * 1000,  # mm
                    'delta_sigma': delta_sigma
                })
        
        # Grau de adensamento (Terzaghi)
        cv = soil_layers[0].get('cv', 1.0) if soil_layers else 1.0
        H_drain = sum(l.get('thickness', 0) for l in soil_layers)
        
        if H_drain > 0:
            T = (cv * time_years * 365 * 24 * 3600) / (H_drain**2)  # Fator tempo
            U = 1 - (8/np.pi**2) * np.exp(-np.pi**2 * T / 4)  # Grau de adensamento
            resultados['degree_of_consolidation'] = min(U, 1.0)
        else:
            resultados['degree_of_consolidation'] = 0.0
        
        settlement_consolidation *= resultados['degree_of_consolidation']
        
        # 3. Recalque total
        settlement_total = settlement_immediate + settlement_consolidation
        
        resultados.update({
            'settlement_consolidation': settlement_consolidation * 1000,  # mm
            'settlement_total': settlement_total * 1000,  # mm
            'layer_settlements': layer_settlements
        })
        
        return resultados
    
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
        # Validação
        if q <= 0:
            raise ValueError("Pressão aplicada deve ser positiva")
        if B <= 0 or L <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")
        if E <= 0:
            raise ValueError("Módulo de elasticidade deve ser positivo")
        
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


class FoundationDesign:
    """Classe para projeto completo de fundações"""
    
    def __init__(self):
        self.terzaghi = TerzaghiCapacity()
    
    def complete_design(self, soil_params: Dict[str, Any], 
                       foundation_params: Dict[str, Any],
                       load_params: Dict[str, Any]) -> Dict[str, Any]:
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
            # Validação de parâmetros obrigatórios
            required_soil = ['c', 'phi', 'gamma']
            required_foundation = ['B', 'L', 'D_f']
            required_load = ['q_applied']
            
            for param in required_soil:
                if param not in soil_params:
                    raise ValueError(f"Parâmetro do solo faltando: {param}")
            
            for param in required_foundation:
                if param not in foundation_params:
                    raise ValueError(f"Parâmetro da fundação faltando: {param}")
            
            for param in required_load:
                if param not in load_params:
                    raise ValueError(f"Parâmetro de carga faltando: {param}")
            
            # 1. Capacidade de carga
            bearing = self.terzaghi.bearing_capacity_basic(
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
            if q_applied <= 0:
                fs_calculated = float('inf')
            else:
                fs_calculated = bearing['q_ult'] / q_applied
            
            safety_status = 'SAFE' if fs_calculated >= 3.0 else 'FAIL'
            
            # 3. Recalques (simplificado)
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
    
    def complete_design_advanced(self, soil_params: Dict[str, Any], 
                                foundation_params: Dict[str, Any],
                                load_params: Dict[str, Any],
                                water_params: Optional[Dict[str, Any]] = None,
                                time_years: float = 1.0) -> Dict[str, Any]:
        """
        Projeto avançado com todas as correções
        """
        try:
            # Validação de parâmetros obrigatórios
            required_soil = ['c', 'phi', 'gamma']
            required_foundation = ['B', 'L', 'D_f']
            required_load = ['q_applied']
            
            for param in required_soil:
                if param not in soil_params:
                    raise ValueError(f"Parâmetro do solo faltando: {param}")
            
            for param in required_foundation:
                if param not in foundation_params:
                    raise ValueError(f"Parâmetro da fundação faltando: {param}")
            
            for param in required_load:
                if param not in load_params:
                    raise ValueError(f"Parâmetro de carga faltando: {param}")
            
            # Parâmetros padrão
            water_params = water_params or {'water_table_depth': None}
            
            # 1. Capacidade de carga avançada
            bearing = self.terzaghi.bearing_capacity_advanced(
                c=soil_params['c'],
                phi=soil_params['phi'],
                gamma=soil_params['gamma'],
                B=foundation_params['B'],
                L=foundation_params['L'],
                D_f=foundation_params['D_f'],
                water_table_depth=water_params.get('water_table_depth'),
                shape=foundation_params.get('shape', 'rectangular'),
                load_inclination=load_params.get('load_inclination', 0.0),
                load_eccentricity_x=load_params.get('load_eccentricity_x', 0.0),
                load_eccentricity_y=load_params.get('load_eccentricity_y', 0.0),
                surcharge=load_params.get('surcharge', 0.0)
            )
            
            # 2. Verificação de segurança
            q_applied = load_params['q_applied']
            if q_applied <= 0:
                fs_calculated = float('inf')
            else:
                fs_calculated = bearing['q_ult'] / q_applied
            
            # Critérios de segurança (NBR 6122)
            if fs_calculated >= 3.0:
                safety_status = 'SEGURO'
                safety_color = 'green'
            elif fs_calculated >= 2.0:
                safety_status = 'ATENÇÃO'
                safety_color = 'orange'
            else:
                safety_status = 'INSEGURO'
                safety_color = 'red'
            
            # 3. Recalques avançados (simulação de camadas)
            soil_layers = soil_params.get('soil_layers', [])
            if not soil_layers:
                # Criar camada padrão se não fornecida
                soil_layers = [{
                    'thickness': foundation_params['B'] * 3,  # 3×B
                    'E': soil_params.get('E', 30000),
                    'Cc': 0.3,
                    'Cr': 0.05,
                    'e0': 1.0,
                    'sigma_v0': soil_params['gamma'] * foundation_params['D_f'],
                    'OCR': 1.0,
                    'cv': 1.0
                }]
            
            settlements = self.terzaghi.settlement_advanced(
                q=q_applied,
                B=foundation_params['B'],
                L=foundation_params['L'],
                soil_layers=soil_layers,
                foundation_type=load_params.get('foundation_type', 'flexible'),
                time_years=time_years
            )
            
            # 4. Verificação de recalques (NBR 6122)
            settlement_limit = 25.0  # 25 mm
            if settlements['settlement_total'] <= 15.0:
                settlement_status = 'ACEITÁVEL'
                settlement_color = 'green'
            elif settlements['settlement_total'] <= 25.0:
                settlement_status = 'LIMITE'
                settlement_color = 'orange'
            else:
                settlement_status = 'EXCESSIVO'
                settlement_color = 'red'
            
            # 5. Recomendações avançadas
            recommendations = self._generate_recommendations_advanced(
                fs_calculated, 
                settlements['settlement_total'],
                bearing,
                foundation_params
            )
            
            # 6. Resumo do projeto
            design_summary = self._create_design_summary_advanced(
                soil_params, foundation_params, load_params, water_params,
                bearing, fs_calculated, settlements, safety_status,
                settlement_status, recommendations, time_years
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
                    'color': safety_color,
                    'nbr_compliance': fs_calculated >= 3.0
                },
                'settlement': {
                    'immediate_mm': settlements['settlement_immediate'],
                    'consolidation_mm': settlements['settlement_consolidation'],
                    'total_mm': settlements['settlement_total'],
                    'degree_consolidation': settlements['degree_of_consolidation'],
                    'limit_mm': settlement_limit,
                    'status': settlement_status,
                    'color': settlement_color,
                    'layer_settlements': settlements['layer_settlements'],
                    'nbr_compliance': settlements['settlement_total'] <= 25.0
                },
                'recommendations': recommendations,
                'design_summary': design_summary,
                'time_years': time_years
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_recommendations_advanced(self, fs: float, settlement: float,
                                          bearing: Dict[str, Any], 
                                          foundation_params: Dict[str, Any]) -> List[str]:
        """Gera recomendações avançadas de projeto"""
        recommendations = []
        
        # Verificação de capacidade
        if fs < 2.0:
            recommendations.append("❌ AUMENTAR DIMENSÕES URGENTE: FS < 2.0 (abaixo do mínimo)")
        elif fs < 3.0:
            recommendations.append("⚠️ CONSIDERAR AUMENTAR DIMENSÕES: FS < 3.0 (abaixo do recomendado pela NBR)")
        else:
            recommendations.append("✅ FS ADEQUADO: Atende NBR 6122 (FS ≥ 3.0)")
        
        # Verificação de recalques
        if settlement > 25.0:
            recommendations.append(f"❌ RECALQUE EXCESSIVO: {settlement:.1f} mm > 25 mm (limite NBR)")
        elif settlement > 15.0:
            recommendations.append(f"⚠️ RECALQUE NO LIMITE: {settlement:.1f} mm (próximo ao limite de 25 mm)")
        else:
            recommendations.append(f"✅ RECALQUE ACEITÁVEL: {settlement:.1f} mm ≤ 15 mm")
        
        # Verificação de excentricidade
        B_eff = bearing.get('B_eff', foundation_params['B'])
        if B_eff < foundation_params['B'] * 0.8:
            recommendations.append("⚠️ EXCENTRICIDADE ELEVADA: Redução significativa da área efetiva")
        
        # Verificação de inclinação
        ic = bearing.get('ic', 1.0)
        if ic < 0.7:
            recommendations.append("⚠️ CARGA INCLINADA: Redução significativa da capacidade")
        
        # Recomendações de otimização
        if fs >= 4.0 and settlement <= 10.0:
            recommendations.append("🎯 PROJETO OTIMIZADO: Pode-se considerar reduzir dimensões")
        
        return recommendations
    
    def _generate_recommendations(self, fs: float, settlement_mm: float) -> List[str]:
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
    
    def _create_design_summary(self, soil_params: Dict[str, Any], 
                              foundation_params: Dict[str, Any],
                              load_params: Dict[str, Any],
                              bearing: Dict[str, Any], 
                              fs: float, 
                              settlement_mm: float, 
                              safety_status: str, 
                              settlement_status: str, 
                              recommendations: List[str]) -> str:
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
    
    def _create_design_summary_advanced(self, soil_params: Dict[str, Any],
                                       foundation_params: Dict[str, Any],
                                       load_params: Dict[str, Any],
                                       water_params: Dict[str, Any],
                                       bearing: Dict[str, Any],
                                       fs: float,
                                       settlements: Dict[str, Any],
                                       safety_status: str,
                                       settlement_status: str,
                                       recommendations: List[str],
                                       time_years: float) -> str:
        """Cria resumo avançado do projeto"""
        summary = f"""
================================================
RELATÓRIO AVANÇADO DE PROJETO DE FUNDAÇÃO
================================================

PARÂMETROS DO SOLO:
- Coesão (c): {soil_params['c']} kPa
- Ângulo de atrito (φ): {soil_params['phi']}°
- Peso específico (γ): {soil_params['gamma']} kN/m³

PARÂMETROS DA FUNDAÇÃO:
- Largura (B): {foundation_params['B']} m
- Comprimento (L): {foundation_params['L']} m
- Profundidade (D_f): {foundation_params['D_f']} m
- Forma: {foundation_params.get('shape', 'retangular')}

CONDIÇÕES ESPECIAIS:
- Nível d'água: {water_params.get('water_table_depth', 'Não considerado')} m
- Tempo de análise: {time_years} anos

RESULTADOS:
1. CAPACIDADE DE CARGA:
   - q_ult = {bearing['q_ult']:.1f} kPa
   - q_adm (FS=3) = {bearing['q_adm_fs3']:.1f} kPa
   - Fatores: Nc={bearing['Nc']:.2f}, Nq={bearing['Nq']:.2f}, Nγ={bearing['Ngamma']:.2f}

2. VERIFICAÇÃO DE SEGURANÇA:
   - FS calculado = {fs:.2f}
   - Status: {safety_status}

3. RECALQUES:
   - Recalque imediato = {settlements['immediate_mm']:.1f} mm
   - Recalque por adensamento = {settlements['consolidation_mm']:.1f} mm
   - Recalque total = {settlements['total_mm']:.1f} mm
   - Grau de adensamento: {settlements['degree_consolidation']:.1%}
   - Status: {settlement_status}

4. RECOMENDAÇÕES:
"""
        
        for i, rec in enumerate(recommendations, 1):
            summary += f"   {i}. {rec}\n"
        
        summary += f"\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        return summary
