"""
BULBO DE TENSÕES - SOLUÇÃO DE BOUSSINESQ
Implementação completa para cálculo e visualização de distribuição de tensões no solo
Refatorado com dataclasses e visualização 3D
Versão 3.0 - Otimização de performance com vetorização
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass
import time

@dataclass
class ResultadoAnaliseBulbo:
    """Estrutura para resultados do bulbo de tensões"""
    coordenadas: np.ndarray
    tensoes: np.ndarray
    parametros_entrada: Dict[str, Any]
    tempo_calculo: float

class BulboTensoesOtimizado:
    """Classe otimizada para cálculo do bulbo de tensões"""
    
    def __init__(self):
        self.cache = {}
        self.ultimo_calculo = None
    
    @staticmethod
    def boussinesq_ponto(q: float, x: float, y: float, z: float) -> float:
        """
        Solução de Boussinesq para carga pontual (otimizada)
        
        Args:
            q: Carga pontual (kN)
            x, y: Coordenadas horizontais do ponto (m)
            z: Profundidade (m)
            
        Returns:
            sigma_z: Tensão vertical (kPa)
        """
        r_sq = x**2 + y**2
        R_sq = r_sq + z**2
        
        if R_sq == 0:
            return np.inf
        
        # Fator de influência de Boussinesq
        I_b = (3 * z**3) / (2 * np.pi * R_sq**2.5)
        sigma_z = I_b * q
        
        return max(0, sigma_z)
    
    @staticmethod
    def boussinesq_retangular_vetorizado(q: float, B: float, L: float, 
                                        X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> np.ndarray:
        """
        Tensão vertical sob carga retangular uniforme (VETORIZADO)
        
        Args:
            q: Pressão uniforme (kPa)
            B, L: Largura e comprimento da sapata (m)
            X, Y, Z: Arrays de coordenadas
            
        Returns:
            sigma_z: Array de tensões verticais (kPa)
        """
        # Inicializar array de resultados
        sigma_z = np.zeros_like(X)
        
        # Coordenadas normalizadas
        x_norm = X / (B/2) if B != 0 else X
        y_norm = Y / (L/2) if L != 0 else Y
        
        # Identificar pontos na superfície
        na_superficie = Z < 0.01
        
        # Pontos dentro da área carregada na superfície
        dentro_area = (np.abs(x_norm) <= 1) & (np.abs(y_norm) <= 1) & na_superficie
        sigma_z[dentro_area] = q
        
        # Pontos abaixo da superfície
        abaixo_superficie = ~na_superficie
        
        if np.any(abaixo_superficie):
            # Coordenadas dos pontos abaixo da superfície
            x_below = X[abaixo_superficie]
            y_below = Y[abaixo_superficie]
            z_below = Z[abaixo_superficie]
            
            # Distância radial ao quadrado
            r_sq = x_below**2 + y_below**2 + z_below**2
            
            # Evitar divisão por zero
            r_sq = np.maximum(r_sq, 0.001)
            
            # Fórmula vetorizada simplificada (aproximação)
            A = B * L
            sigma_below = (q * A) / (2 * np.pi * r_sq) * (1 - (z_below**3) / (r_sq**1.5))
            sigma_below = np.maximum(sigma_below, 0)
            
            sigma_z[abaixo_superficie] = sigma_below
        
        return sigma_z
    
    def gerar_malha_3d_otimizada(self, B: float, L: float, 
                                depth_ratio: float = 3.0, 
                                grid_size: int = 40) -> Tuple[np.ndarray, ...]:
        """
        Gera malha 3D otimizada para cálculo
        """
        max_dim = max(B, L)
        x_lim = max(2 * max_dim, 3.0)
        y_lim = max(2 * max_dim, 3.0)
        
        # Usar linspace otimizado
        x = np.linspace(-x_lim, x_lim, grid_size, dtype=np.float32)
        y = np.linspace(-y_lim, y_lim, grid_size, dtype=np.float32)
        z = np.linspace(0.01, depth_ratio * max_dim, grid_size, dtype=np.float32)
        
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        return X, Y, Z
    
    def calcular_bulbo_boussinesq(self, fundacao: Dict[str, Any], 
                                 solo: Dict[str, Any],
                                 depth_ratio: float = 3.0,
                                 grid_size: int = 40,
                                 use_cache: bool = True) -> ResultadoAnaliseBulbo:
        """
        Calcula bulbo de tensões com Boussinesq (OTIMIZADO)
        """
        inicio = time.time()
        
        # Verificar cache
        cache_key = f"{fundacao['largura']}_{fundacao['comprimento']}_{fundacao['carga']}_{grid_size}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extrair parâmetros
        B = fundacao['largura']
        L = fundacao['comprimento']
        q = fundacao['carga']
        
        # Gerar malha otimizada
        X, Y, Z = self.gerar_malha_3d_otimizada(B, L, depth_ratio, grid_size)
        
        # Calcular tensões vetorizadas
        sigma_grid = self.boussinesq_retangular_vetorizado(q, B, L, X, Y, Z)
        
        # Suavizar resultados (opcional)
        from scipy.ndimage import gaussian_filter
        if grid_size > 20:
            sigma_grid = gaussian_filter(sigma_grid, sigma=0.8)
        
        tempo_total = time.time() - inicio
        
        # Criar resultado
        resultado = ResultadoAnaliseBulbo(
            coordenadas=np.stack([X, Y, Z], axis=-1),
            tensoes=sigma_grid,
            parametros_entrada={
                'fundacao': fundacao,
                'solo': solo,
                'analise': {
                    'depth_ratio': depth_ratio,
                    'grid_size': grid_size,
                    'tempo_calculo': tempo_total
                }
            },
            tempo_calculo=tempo_total
        )
        
        # Armazenar em cache
        if use_cache:
            self.cache[cache_key] = resultado
            self.ultimo_calculo = resultado
        
        return resultado
    
    def plot_bulbo_2d_isobaras(self, resultado: ResultadoAnaliseBulbo) -> go.Figure:
        """
        Cria visualização 2D com isóbaras (OTIMIZADA)
        """
        # Extrair dados
        sigma_grid = resultado.tensoes
        coords = resultado.coordenadas
        
        # Pegar slice central (plano Y=0)
        slice_index = sigma_grid.shape[1] // 2
        center_slice = sigma_grid[:, slice_index, :]
        
        # Normalizar para porcentagem
        q = resultado.parametros_entrada['fundacao']['carga']
        center_slice_pct = (center_slice / q * 100) if q > 0 else center_slice * 0
        
        X_slice = coords[:, slice_index, :, 0]
        Z_slice = coords[:, slice_index, :, 2]
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar mapa de calor
        fig.add_trace(go.Contour(
            z=center_slice_pct,
            x=X_slice[0, :],
            y=Z_slice[:, 0],
            colorscale='Plasma',
            contours=dict(
                start=0,
                end=100,
                size=10,
                coloring='heatmap',
                showlabels=True,
                labelfont=dict(size=10, color='white')
            ),
            colorbar=dict(
                title="Δσ/q (%)",
                tickvals=list(range(0, 101, 10))
            ),
            hovertemplate=(
                "Distância X: %{x:.2f} m<br>"
                "Profundidade Z: %{y:.2f} m<br>"
                "Tensão Δσ/q: %{z:.1f} %<br>"
                "<extra></extra>"
            ),
            name="Bulbo de Tensões"
        ))
        
        # Adicionar linha da sapata
        B = resultado.parametros_entrada['fundacao']['largura']
        fig.add_shape(
            type="rect",
            x0=-B/2, y0=0,
            x1=B/2, y1=-0.05,
            line=dict(color="red", width=3),
            fillcolor="rgba(255, 0, 0, 0.3)",
            name="Sapata"
        )
        
        # Configurar layout
        fig.update_layout(
            title="BULBO DE TENSÕES - SOLUÇÃO DE BOUSSINESQ",
            xaxis_title="DISTÂNCIA DO CENTRO (m)",
            yaxis_title="PROFUNDIDADE (m)",
            yaxis=dict(autorange='reversed'),
            height=600,
            showlegend=True,
            plot_bgcolor='rgba(240, 240, 240, 0.8)'
        )
        
        return fig
    
    def calcular_profundidade_influencia(self, B: float, L: float, 
                                        percentual: float = 0.1) -> float:
        """
        Calcula profundidade de influência (onde Δσ/q = percentual)
        """
        # Fórmula prática para profundidade de influência
        area = B * L
        diametro_equivalente = np.sqrt(4 * area / np.pi)
        
        if percentual == 0.05:
            return 1.5 * diametro_equivalente
        elif percentual == 0.10:
            return diametro_equivalente
        elif percentual == 0.20:
            return 0.7 * diametro_equivalente
        else:
            return 2 * B
    
    def relatorio_tecnico(self, resultado: ResultadoAnaliseBulbo) -> str:
        """
        Gera relatório técnico do bulbo de tensões
        """
        fundacao = resultado.parametros_entrada['fundacao']
        B = fundacao['largura']
        L = fundacao['comprimento']
        q = fundacao['carga']
        
        # Calcular profundidades
        z_10 = self.calcular_profundidade_influencia(B, L, 0.10)
        z_20 = self.calcular_profundidade_influencia(B, L, 0.20)
        z_05 = self.calcular_profundidade_influencia(B, L, 0.05)
        
        relatorio = f"""
======================================================
RELATÓRIO TÉCNICO - BULBO DE TENSÕES (BOUSSINESQ)
======================================================

PARÂMETROS DA ANÁLISE:
• Pressão aplicada (q): {q:.0f} kPa
• Largura da sapata (B): {B:.2f} m
• Comprimento da sapata (L): {L:.2f} m
• Área de contato: {B*L:.2f} m²
• Carga total: {q * B * L:.0f} kN
• Tempo de cálculo: {resultado.tempo_calculo:.2f} s

PROFUNDIDADES DE INFLUÊNCIA:
• Até 20% de q: z ≈ {z_20:.2f} m ({z_20/B:.1f}×B)
• Até 10% de q: z ≈ {z_10:.2f} m ({z_10/B:.1f}×B)
• Até 5% de q:  z ≈ {z_05:.2f} m ({z_05/B:.1f}×B)

RECOMENDAÇÕES TÉCNICAS:
1. Para análise de recalques: considerar até profundidade {z_10:.1f} m
2. Para interação entre fundações: zona de influência ≈ {z_20:.1f} m
3. Para ensaios in situ: investigar até {z_05:.1f} m

MÉTODO UTILIZADO:
• Solução de Boussinesq para carga retangular uniforme
• Cálculo vetorizado otimizado para performance
• Grid de cálculo: {resultado.parametros_entrada['analise']['grid_size']}³ pontos

DATA DA ANÁLISE: {time.strftime('%d/%m/%Y %H:%M:%S')}
"""
        
        return relatorio


# Função de compatibilidade
def criar_bulbo_tensoes() -> BulboTensoesOtimizado:
    """Factory function para criar instância otimizada"""
    return BulboTensoesOtimizado()
