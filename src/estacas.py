"""
MÓDULO DE ESTACAS - Fundações Profundas
Implementação de métodos para cálculo de capacidade de carga de estacas
Versão 3.0 - Corrigido: Validação completa e tratamento de erros
"""
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
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
    
    def __post_init__(self):
        """Validação dos dados da camada"""
        if self.espessura <= 0:
            raise ValueError("Espessura da camada deve ser positiva")
        if self.profundidade_inicio < 0:
            raise ValueError("Profundidade inicial não pode ser negativa")
        if self.profundidade_fim <= self.profundidade_inicio:
            raise ValueError("Profundidade final deve ser maior que a inicial")
        if self.Nspt < 0:
            raise ValueError("Valor SPT não pode ser negativo")
        if self.tipo not in ['argila', 'areia', 'silte']:
            raise ValueError("Tipo de solo deve ser 'argila', 'areia' ou 'silte'")
        if self.peso_especifico <= 0:
            raise ValueError("Peso específico deve ser positivo")
        if self.coeficiente_poisson < 0 or self.coeficiente_poisson >= 0.5:
            raise ValueError("Coeficiente de Poisson deve estar entre 0 e 0.5")

@dataclass
class EstacaGeometria:
    """Geometria e propriedades da estaca"""
    tipo: str  # 'hélice contínua', 'raiz', 'pré-moldada', 'metálica', 'escavada'
    diametro: float  # m
    comprimento: float  # m
    forma: str  # 'circular', 'quadrada'
    material: str  # 'concreto', 'aço', 'madeira'
    modulo_elasticidade: float = 30e6  # kPa (concreto)
    
    def __post_init__(self):
        """Validação da geometria da estaca"""
        if self.diametro <= 0:
            raise ValueError("Diâmetro da estaca deve ser positivo")
        if self.comprimento <= 0:
            raise ValueError("Comprimento da estaca deve ser positivo")
        if self.forma not in ['circular', 'quadrada']:
            raise ValueError("Forma deve ser 'circular' ou 'quadrada'")
        if self.material not in ['concreto', 'aço', 'madeira']:
            raise ValueError("Material deve ser 'concreto', 'aço' ou 'madeira'")
        if self.modulo_elasticidade <= 0:
            raise ValueError("Módulo de elasticidade deve ser positivo")

class EstacaDesigner:
    """Classe para projeto de estacas com validação completa"""
    
    def __init__(self):
        self.resultados = {}
        self.historico = []
    
    def _validar_camadas(self, camadas: List[CamadaSoloEstaca]):
        """Valida lista de camadas de solo"""
        if not camadas:
            raise ValueError("Lista de camadas não pode estar vazia")
        
        # Verificar continuidade das camadas
        profundidade_anterior = 0
        for i, camada in enumerate(camadas):
            if abs(camada.profundidade_inicio - profundidade_anterior) > 0.01:
                raise ValueError(f"Descontinuidade nas camadas: camada {i}")
            profundidade_anterior = camada.profundidade_fim
    
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
        try:
            # Validação de entrada
            self._validar_camadas(camadas)
            if nivel_agua < 0:
                raise ValueError("Nível d'água não pode ser negativo")
            
            # Ordenar camadas por profundidade
            camadas_ordenadas = sorted(camadas, key=lambda x: x.profundidade_inicio)
            
            # Parâmetros geométricos
            if estaca.forma == 'circular':
                perimetro = np.pi * estaca.diametro
                area_ponta = np.pi * (estaca.diametro/2)**2
            else:  # quadrada
                perimetro = 4 * estaca.diametro
                area_ponta = estaca.diametro**2
            
            # Executar método selecionado
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
            capacidade_total = capacidade.get('capacidade_total', 0)
            if capacidade_total > 0:
                capacidade['capacidade_admissivel'] = capacidade_total / 2.0  # FS=2
            else:
                capacidade['capacidade_admissivel'] = 0
            
            # Preparar resultados
            resultados = {
                'metodo': metodo,
                'estaca': {
                    'tipo': estaca.tipo,
                    'diametro': estaca.diametro,
                    'comprimento': estaca.comprimento,
                    'forma': estaca.forma,
                    'material': estaca.material
                },
                'camadas': len(camadas),
                'nivel_agua': nivel_agua,
                **capacidade
            }
            
            self.resultados = resultados
            self.historico.append({
                'timestamp': datetime.now(),
                'metodo': metodo,
                'resultados': resultados
            })
            
            return resultados
            
        except Exception as e:
            raise ValueError(f"Erro no cálculo da capacidade: {str(e)}")
    
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
            tensao_lateral = K * camada.Nspt / F if F > 0 else 0
            
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
            tensao_ponta = 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta
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
            tensao_ponta = 0.0
        
        capacidade_total = atrito_lateral_total + resistencia_ponta
        
        return {
            'atrito_lateral': atrito_lateral_total,
            'resistencia_ponta': resistencia_ponta,
            'capacidade_total': capacidade_total,
            'tensoes_laterais': tensoes_laterais,
            'tensao_ponta_ultima': tensao_ponta
        }
    
    def calcular_recalque_estaca(self, carga: float, estaca: EstacaGeometria,
                                modulo_solo: float, tipo_solo: str) -> Dict[str, float]:
        """
        Calcula recalques de estacas usando método simplificado
        """
        if carga <= 0:
            raise ValueError("Carga deve ser positiva")
        if modulo_solo <= 0:
            raise ValueError("Módulo do solo deve ser positivo")
        
        # Área da seção transversal
        if estaca.forma == 'circular':
            area = np.pi * (estaca.diametro/2)**2
        else:
            area = estaca.diametro**2
        
        # Recalque elástico da estaca
        recalque_elastico = (carga * estaca.comprimento) / (area * estaca.modulo_elasticidade)
        
        # Recalque por compressão do solo
        if tipo_solo == 'areia':
            fator_solo = 0.001
        else:
            fator_solo = 0.002
        
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
        if num_estacas <= 0:
            raise ValueError("Número de estacas deve ser positivo")
        if espacamento <= 0:
            raise ValueError("Espaçamento deve ser positivo")
        if diametro <= 0:
            raise ValueError("Diâmetro deve ser positivo")
        
        # Razão espaçamento/diâmetro
        s_D = espacamento / diametro
        
        if tipo_solo == 'argila':
            # Fórmula de Converse-Labarre
            m = int(np.sqrt(num_estacas))
            n = int(np.ceil(num_estacas / m))
            
            if espacamento > 0 and diametro > 0:
                theta = np.arctan(diametro/espacamento)
            else:
                theta = 0
            
            if m > 0 and n > 0:
                eficiencia = 1 - (theta * (m * (n - 1) + n * (m - 1)) / (90 * m * n))
            else:
                eficiencia = 1.0
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
{'='*60}
RELATÓRIO DE PROJETO DE ESTACA
Método: {resultados.get('metodo', 'N/A').upper()}
{'='*60}

PARÂMETROS DA ESTACA:
• Tipo: {resultados.get('estaca', {}).get('tipo', 'N/A')}
• Diâmetro: {resultados.get('estaca', {}).get('diametro', 0):.2f} m
• Comprimento: {resultados.get('estaca', {}).get('comprimento', 0):.2f} m
• Material: {resultados.get('estaca', {}).get('material', 'N/A')}

RESULTADOS DA CAPACIDADE DE CARGA:
• Atrito lateral total: {resultados.get('atrito_lateral', 0):.0f} kN
• Resistência de ponta: {resultados.get('resistencia_ponta', 0):.0f} kN
• Capacidade total última: {resultados.get('capacidade_total', 0):.0f} kN
• Capacidade admissível (FS=2): {resultados.get('capacidade_admissivel', 0):.0f} kN

INFORMAÇÕES ADICIONAIS:
• Tensão na ponta: {resultados.get('tensao_ponta_ultima', 0):.0f} kPa
• Número de camadas: {resultados.get('camadas', 0)}
• Nível d'água: {resultados.get('nivel_agua', 0):.1f} m

RECOMENDAÇÕES:
1. Verificar recalques para carga de {resultados.get('capacidade_admissivel', 0):.0f} kN
2. Realizar prova de carga para confirmação
3. Considerar efeito de grupo se houver múltiplas estacas

Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        
        return relatorio


# Função de conveniência para uso no Streamlit
def criar_designer_estacas() -> EstacaDesigner:
    """Factory function para criar designer de estacas"""
    return EstacaDesigner()
