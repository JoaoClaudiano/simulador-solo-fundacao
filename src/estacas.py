"""
MÓDULO DE ESTACAS - Fundações Profundas
Implementação de métodos para cálculo de capacidade de carga de estacas
"""
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class CamadaSoloEstaca:
    """Camada de solo para análise de estacas"""
    espessura: float  # m
    profundidade_inicio: float  # m
    profundidade_fim: float  # m
    peso_especifico: float  # kN/m³
    peso_especifico_submerso: float  # kN/m³
    angulo_atrito: float  # °
    coesao: float  # kPa
    Nspt: float  # Valor SPT
    tipo: str  # 'argila', 'areia', 'silte'
    modulo_elasticidade: float = 30000  # kPa
    coeficiente_poisson: float = 0.3
    resistencia_nao_drenada: Optional[float] = None  # Su (kPa) para argilas

@dataclass
class EstacaGeometria:
    """Geometria e propriedades da estaca"""
    tipo: str  # 'hélice contínua', 'raiz', 'pré-moldada', 'metálica', 'escavada'
    diametro: float  # m
    comprimento: float  # m
    forma: str  # 'circular', 'quadrada'
    material: str  # 'concreto', 'aço', 'madeira'
    modulo_elasticidade: float = 30e6  # kPa (concreto)

class EstacaDesigner:
    """Classe para projeto de estacas"""
    
    def __init__(self):
        self.resultados = {}
    
    def capacidade_estaca_metodo_estatico(self, 
                                         camadas: List[CamadaSoloEstaca],
                                         estaca: EstacaGeometria,
                                         metodo: str = 'aoki_velloso',
                                         nivel_agua: float = 0.0) -> Dict[str, Any]:
        """
        Calcula capacidade de estaca usando métodos estáticos
        
        Args:
            camadas: Lista de camadas de solo
            estaca: Geometria da estaca
            metodo: 'aoki_velloso', 'decourt_quaresma', 'meyerhof', 'alpha_beta'
            nivel_agua: Profundidade do nível d'água (m)
            
        Returns:
            Dicionário com resultados da capacidade
        """
        resultados = {
            'metodo': metodo,
            'estaca': estaca.__dict__,
            'camadas': [c.__dict__ for c in camadas]
        }
        
        # Parâmetros geométricos
        if estaca.forma == 'circular':
            perimetro = np.pi * estaca.diametro
            area_ponta = np.pi * (estaca.diametro/2)**2
        else:  # quadrada
            perimetro = 4 * estaca.diametro
            area_ponta = estaca.diametro**2
        
        # Classificar camadas por profundidade
        camadas_ordenadas = sorted(camadas, key=lambda x: x.profundidade_inicio)
        
        if metodo == 'aoki_velloso':
            capacidade = self._metodo_aoki_velloso(camadas_ordenadas, perimetro, area_ponta, estaca)
        elif metodo == 'decourt_quaresma':
            capacidade = self._metodo_decourt_quaresma(camadas_ordenadas, perimetro, area_ponta)
        elif metodo == 'meyerhof':
            capacidade = self._metodo_meyerhof(camadas_ordenadas, perimetro, area_ponta, estaca)
        elif metodo == 'alpha_beta':
            capacidade = self._metodo_alpha_beta(camadas_ordenadas, perimetro, area_ponta, nivel_agua)
        else:
            raise ValueError(f"Método {metodo} não implementado")
        
        # Adicionar fatores de segurança
        capacidade['capacidade_admissivel'] = capacidade['capacidade_total'] / 2.0  # FS=2
        
        resultados.update(capacidade)
        self.resultados = resultados
        
        return resultados
    
    def _metodo_aoki_velloso(self, camadas: List[CamadaSoloEstaca], 
                            perimetro: float, area_ponta: float,
                            estaca: EstacaGeometria) -> Dict[str, float]:
        """
        Método de Aoki & Velloso (1975) - Baseado em SPT
        """
        # Parâmetros conforme Aoki & Velloso
        if estaca.tipo == 'hélice contínua':
            K = 0.8  # Coeficiente para atrito lateral
            F1 = 3.0  # Coeficiente para ponta em argila
            F2 = 2.0  # Coeficiente para ponta em areia
        elif estaca.tipo == 'pré-moldada':
            K = 1.0
            F1 = 2.0
            F2 = 1.5
        else:  # estaca escavada
            K = 1.2
            F1 = 2.5
            F2 = 1.8
        
        # Calcular atrito lateral por camada
        atrito_lateral_total = 0.0
        tensoes_laterais = []
        
        for camada in camadas:
            # Determinar coeficiente conforme tipo de solo
            if camada.tipo == 'argila':
                F = F1
            else:  # areia/silte
                F = F2
            
            # Tensão lateral admissível (kPa)
            tensao_lateral = K * camada.Nspt / F
            
            # Área lateral da camada
            altura_camada = min(camada.espessura, camada.profundidade_fim - camada.profundidade_inicio)
            area_lateral = perimetro * altura_camada
            
            # Atrito lateral da camada
            atrito_camada = tensao_lateral * area_lateral
            atrito_lateral_total += atrito_camada
            
            tensoes_laterais.append({
                'profundidade': camada.profundidade_inicio,
                'tensao': tensao_lateral,
                'atrito': atrito_camada
            })
        
        # Resistência de ponta
        camada_ponta = camadas[-1] if camadas else None
        if camada_ponta:
            if camada_ponta.tipo == 'argila':
                tensao_ponta = F1 * camada_ponta.Nspt
            else:
                tensao_ponta = F2 * camada_ponta.Nspt
            
            resistencia_ponta = tensao_ponta * area_ponta
        else:
            resistencia_ponta = 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta if camada_ponta else 0.0
        }
    
    def _metodo_decourt_quaresma(self, camadas: List[CamadaSoloEstaca],
                                perimetro: float, area_ponta: float) -> Dict[str, float]:
        """
        Método de Décourt & Quaresma (1978) - Baseado em SPT
        """
        # Coeficientes conforme Décourt & Quaresma
        ALPHA = 0.03  # kN/cm² para atrito lateral
        BETA = 0.4   # Coeficiente para resistência de ponta
        
        atrito_lateral_total = 0.0
        tensoes_laterais = []
        
        for camada in camadas:
            # Tensão lateral (convertendo Nspt para tensão)
            tensao_lateral = ALPHA * camada.Nspt  # kN/cm²
            tensao_lateral *= 100  # Converter para kPa
            
            # Limites práticos
            tensao_lateral = min(tensao_lateral, 120)  # Limite de 120 kPa
            
            # Área lateral
            altura_camada = min(camada.espessura, camada.profundidade_fim - camada.profundidade_inicio)
            area_lateral = perimetro * altura_camada
            
            atrito_camada = tensao_lateral * area_lateral
            atrito_lateral_total += atrito_camada
            
            tensoes_laterais.append({
                'profundidade': camada.profundidade_inicio,
                'tensao': tensao_lateral,
                'atrito': atrito_camada
            })
        
        # Resistência de ponta
        camada_ponta = camadas[-1] if camadas else None
        if camada_ponta:
            tensao_ponta = BETA * camada_ponta.Nspt * 1000  # kPa
            resistencia_ponta = tensao_ponta * area_ponta
        else:
            resistencia_ponta = 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta if camada_ponta else 0.0
        }
    
    def _metodo_meyerhof(self, camadas: List[CamadaSoloEstaca],
                        perimetro: float, area_ponta: float,
                        estaca: EstacaGeometria) -> Dict[str, float]:
        """
        Método de Meyerhof para estacas em solos granulares
        """
        atrito_lateral_total = 0.0
        tensoes_laterais = []
        
        for camada in camadas:
            if camada.tipo in ['areia', 'silte']:
                # Para solos granulares
                tensao_lateral = 2 * camada.Nspt  # kPa
                tensao_lateral = min(tensao_lateral, 100)  # Limite
            else:
                # Para argilas (Meyerhof não é recomendado)
                tensao_lateral = 0.5 * camada.coesao if camada.coesao > 0 else 10
            
            altura_camada = min(camada.espessura, camada.profundidade_fim - camada.profundidade_inicio)
            area_lateral = perimetro * altura_camada
            
            atrito_camada = tensao_lateral * area_lateral
            atrito_lateral_total += atrito_camada
            
            tensoes_laterais.append({
                'profundidade': camada.profundidade_inicio,
                'tensao': tensao_lateral,
                'atrito': atrito_camada
            })
        
        # Resistência de ponta (Meyerhof para solos granulares)
        camada_ponta = camadas[-1] if camadas else None
        if camada_ponta and camada_ponta.tipo in ['areia', 'silte']:
            tensao_ponta = 400 * camada_ponta.Nspt  # kPa
            resistencia_ponta = tensao_ponta * area_ponta
        else:
            resistencia_ponta = 9 * camada_ponta.coesao * area_ponta if camada_ponta else 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta if camada_ponta else 0.0
        }
    
    def _metodo_alpha_beta(self, camadas: List[CamadaSoloEstaca],
                          perimetro: float, area_ponta: float,
                          nivel_agua: float) -> Dict[str, float]:
        """
        Método Alpha-Beta (α-β) para estacas em solos coesivos e granulares
        """
        atrito_lateral_total = 0.0
        tensoes_laterais = []
        
        for camada in camadas:
            profundidade_media = (camada.profundidade_inicio + camada.profundidade_fim) / 2
            
            # Determinar tensão vertical efetiva
            if profundidade_media > nivel_agua:
                tensao_vertical = camada.peso_especifico_submerso * (profundidade_media - nivel_agua)
                tensao_vertical += camada.peso_especifico * min(profundidade_media, nivel_agua)
            else:
                tensao_vertical = camada.peso_especifico * profundidade_media
            
            # Coeficientes Alpha e Beta
            if camada.tipo == 'argila':
                # Método Alpha para argilas
                if camada.coesao <= 25:
                    alpha = 1.0
                elif camada.coesao <= 50:
                    alpha = 0.8
                elif camada.coesao <= 75:
                    alpha = 0.6
                else:
                    alpha = 0.5
                
                tensao_lateral = alpha * camada.coesao
            else:
                # Método Beta para solos granulares
                beta = np.tan(np.radians(camada.angulo_atrito)) * 0.25  # Beta ≈ K * tan(δ)
                tensao_lateral = beta * tensao_vertical
            
            # Limites práticos
            tensao_lateral = min(tensao_lateral, 200)  # kPa
            
            altura_camada = min(camada.espessura, camada.profundidade_fim - camada.profundidade_inicio)
            area_lateral = perimetro * altura_camada
            
            atrito_camada = tensao_lateral * area_lateral
            atrito_lateral_total += atrito_camada
            
            tensoes_laterais.append({
                'profundidade': camada.profundidade_inicio,
                'tensao': tensao_lateral,
                'atrito': atrito_camada,
                'tensao_vertical': tensao_vertical
            })
        
        # Resistência de ponta
        camada_ponta = camadas[-1] if camadas else None
        if camada_ponta:
            if camada_ponta.tipo == 'argila':
                tensao_ponta = 9 * camada_ponta.coesao  # Nc = 9 para argilas
            else:
                # Para solos granulares
                Nq = np.exp(np.pi * np.tan(np.radians(camada_ponta.angulo_atrito))) * \
                     (np.tan(np.radians(45 + camada_ponta.angulo_atrito/2)))**2
                tensao_ponta = camada_ponta.peso_especifico_submerso * camada_ponta.profundidade_fim * Nq
            
            resistencia_ponta = tensao_ponta * area_ponta
        else:
            resistencia_ponta = 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta if camada_ponta else 0.0
        }
    
    def calcular_recalque_estaca(self, carga: float, estaca: EstacaGeometria,
                                modulo_solo: float, tipo_solo: str) -> Dict[str, float]:
        """
        Calcula recalques de estacas usando método simplificado
        """
        # Área da seção transversal
        if estaca.forma == 'circular':
            area = np.pi * (estaca.diametro/2)**2
        else:
            area = estaca.diametro**2
        
        # Recalque elástico da estaca
        recalque_elastico = (carga * estaca.comprimento) / (area * estaca.modulo_elasticidade)
        
        # Recalque por compressão do solo
        fator_solo = 0.001 if tipo_solo == 'areia' else 0.002
        recalque_solo = fator_solo * carga / (estaca.diametro * modulo_solo)
        
        # Recalque total
        recalque_total = recalque_elastico + recalque_solo
        
        return {
            'recalque_elastico_mm': recalque_elastico * 1000,
            'recalque_solo_mm': recalque_solo * 1000,
            'recalque_total_mm': recalque_total * 1000,
            'recalque_total_m': recalque_total
        }
    
    def eficiencia_grupo_estacas(self, num_estacas: int, espacamento: float,
                                diametro: float, tipo_solo: str) -> Dict[str, float]:
        """
        Calcula eficiência de grupo de estacas
        """
        # Razão espaçamento/diâmetro
        s_D = espacamento / diametro
        
        if tipo_solo == 'argila':
            # Fórmula de Converse-Labarre
            m = int(np.sqrt(num_estacas))  # Número de estacas em uma linha
            n = int(np.ceil(num_estacas / m))  # Número de estacas em uma coluna
            
            theta = np.arctan(diametro/espacamento)
            eficiencia = 1 - (theta * (m * (n - 1) + n * (m - 1)) / (90 * m * n))
        else:
            # Para solos granulares
            if s_D >= 3:
                eficiencia = 1.0
            elif s_D >= 2:
                eficiencia = 0.9
            elif s_D >= 1.5:
                eficiencia = 0.8
            else:
                eficiencia = 0.7
        
        return {
            'eficiencia': min(eficiencia, 1.0),
            'espacamento_diametro': s_D,
            'capacidade_grupo': num_estacas * eficiencia
        }
    
    def gerar_relatorio_estaca(self, resultados: Dict[str, Any]) -> str:
        """Gera relatório técnico da análise de estacas"""
        relatorio = f"""
        =================================================
        RELATÓRIO DE PROJETO DE ESTACA
        Método: {resultados['metodo'].upper()}
        =================================================
        
        PARÂMETROS DA ESTACA:
        - Tipo: {resultados['estaca']['tipo']}
        - Diâmetro: {resultados['estaca']['diametro']:.2f} m
        - Comprimento: {resultados['estaca']['comprimento']:.2f} m
        - Material: {resultados['estaca']['material']}
        
        RESULTADOS DA CAPACIDADE DE CARGA:
        - Atrito lateral total: {resultados['atrito_lateral']:.0f} kN
        - Resistência de ponta: {resultados['resistencia_ponta']:.0f} kN
        - Capacidade total última: {resultados['capacidade_total']:.0f} kN
        - Capacidade admissível (FS=2): {resultados['capacidade_admissivel']:.0f} kN
        
        INFORMAÇÕES ADICIONAIS:
        - Tensão na ponta: {resultados.get('tensao_ponta_ultima', 0):.0f} kPa
        - Método utilizado: {resultados['metodo']}
        
        RECOMENDAÇÕES:
        1. Verificar recalques para carga de {resultados['capacidade_admissivel']:.0f} kN
        2. Realizar prova de carga para confirmação
        3. Considerar efeito de grupo se houver múltiplas estacas
        
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        return relatorio

# Função de conveniência para uso no Streamlit
def criar_designer_estacas() -> EstacaDesigner:
    """Factory function para criar designer de estacas"""
    return EstacaDesigner()