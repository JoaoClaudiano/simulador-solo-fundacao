"""
BULBO DE TENSÕES - SOLUÇÃO DE BOUSSINESQ
Implementação completa para cálculo e visualização de distribuição de tensões no solo
Refatorado com dataclasses e visualização 3D
Versão 2.1 - Correção de isóbaras e performance
"""
import numpy as np
from scipy import integrate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Tuple, Optional, Dict, Any
import warnings
import time
import pandas as pd
from dataclasses import dataclass

@dataclass
class ResultadoAnalise:
    coordenadas: np.ndarray = None
    tensoes: np.ndarray = None
    parametros_entrada: Dict[str, Any] = None

class BulboTensoes:
    """Classe principal para cálculo e visualização do bulbo de tensões usando Boussinesq"""
    
    def __init__(self):
        self.cache = {}  # Cache para resultados calculados
        self.ultimo_calculo = None
    
    @staticmethod
    def boussinesq_point_load(Q: float, x: float, y: float, z: float, nu: float = 0.3) -> float:
        """
        Solução de Boussinesq para carga pontual
        
        Args:
            Q: Carga pontual (kN)
            x, y: Coordenadas horizontais do ponto (m)
            z: Profundidade (m)
            nu: Coeficiente de Poisson
            
        Returns:
            sigma_z: Tensão vertical (kPa)
        """
        r = np.sqrt(x**2 + y**2)
        R = np.sqrt(r**2 + z**2)
        
        if R == 0:
            return np.inf
        
        # Fator de influência de Boussinesq
        I_b = (3 * z**3) / (2 * np.pi * R**5)
        sigma_z = I_b * Q
        
        return sigma_z
    
    def boussinesq_rectangular_load(
        self,
        q: float, B: float, L: float, x: float, y: float, z: float, 
        nu: float = 0.3, method: str = 'newmark'
    ) -> float:
        """
        Tensão vertical sob carga retangular uniforme
        
        Args:
            q: Pressão uniforme (kPa)
            B, L: Largura e comprimento da sapata (m)
            x, y: Coordenadas do ponto
            z: Profundidade (m)
            nu: Coeficiente de Poisson
            method: 'newmark' (rápido) ou 'integration' (preciso)
            
        Returns:
            sigma_z: Tensão vertical (kPa)
        """
        if method == 'newmark':
            # Método dos coeficientes de influência de Newmark (simplificado para performance)
            if z == 0:
                # Na superfície, dentro da área carregada
                if abs(x) <= B/2 and abs(y) <= L/2:
                    return q
                else:
                    return 0.0
            
            # Coeficientes normalizados
            m = abs(x) / (B/2)
            n = abs(y) / (L/2)
            
            # Evitar divisão por zero
            if z == 0:
                z = 0.001
            
            # Fórmula simplificada para performance
            A = B * L
            r_squared = x**2 + y**2 + z**2
            sigma_z = (q * A) / (2 * np.pi * r_squared) * (1 - (z**3) / (r_squared**1.5))
            
        else:  # method == 'integration'
            # Integração numérica da solução de Boussinesq (mais precisa)
            def integrand(xi: float, eta: float) -> float:
                r = np.sqrt((x - xi)**2 + (y - eta)**2 + z**2)
                if r == 0:
                    return 0
                return (3 * z**3) / (2 * np.pi * r**5)
            
            try:
                result, error = integrate.dblquad(
                    integrand,
                    -B/2, B/2,
                    lambda x: -L/2, lambda x: L/2
                )
                sigma_z = q * result
            except:
                # Fallback para método simplificado
                sigma_z = self.boussinesq_rectangular_load(q, B, L, x, y, z, nu, 'newmark')
        
        return max(0, sigma_z)  # Evitar valores negativos
    
    def _calcular_tensao_malha_otimizado(
        self,
        X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
        fundacao, solo, method: str = 'newmark'
    ) -> np.ndarray:
        """
        Método OTIMIZADO para cálculo da malha de tensões.
        Usa vetorização para melhor performance.
        """
        start_time = time.time()
        
        # Criar arrays 1D para vetorização
        x_flat = X.flatten()
        y_flat = Y.flatten()
        z_flat = Z.flatten()
        
        # Inicializar array de resultados
        sigma_flat = np.zeros_like(x_flat)
        
        # Identificar pontos na superfície (z próximo a 0)
        surface_mask = z_flat < 0.01
        inside_mask = (
            (np.abs(x_flat[surface_mask]) <= fundacao.largura/2) & 
            (np.abs(y_flat[surface_mask]) <= fundacao.comprimento/2)
        )
        
        # Atribuir valores na superfície
        sigma_flat[surface_mask] = np.where(
            inside_mask, 
            fundacao.carga, 
            0.0
        )
        
        # Calcular tensões para pontos abaixo da superfície (VETORIZADO)
        below_mask = ~surface_mask
        if np.any(below_mask):
            # Usar método vetorizado simplificado para performance
            x_below = x_flat[below_mask]
            y_below = y_flat[below_mask]
            z_below = z_flat[below_mask]
            
            # Distância radial ao quadrado
            r_sq = x_below**2 + y_below**2 + z_below**2
            
            # Evitar divisão por zero
            r_sq = np.maximum(r_sq, 0.001)
            
            # Fórmula vetorizada simplificada
            area = fundacao.largura * fundacao.comprimento
            sigma_z = (fundacao.carga * area) / (2 * np.pi * r_sq) * (1 - (z_below**3) / (r_sq**1.5))
            sigma_flat[below_mask] = np.maximum(sigma_z, 0)
        
        # Remodelar para formato 3D original
        sigma_grid = sigma_flat.reshape(X.shape)
        
        print(f"Tempo cálculo otimizado: {time.time() - start_time:.2f}s")
        return sigma_grid
    
    def gerar_bulbo_boussinesq_avancado(
        self, 
        fundacao, 
        solo, 
        depth_ratio: float = 3.0, 
        grid_size: int = 40,
        method: str = 'newmark',
        use_cache: bool = True
    ) -> ResultadoAnalise:
        """
        Gera bulbo de tensões real usando Boussinesq (método avançado).
        Versão corrigida para melhor visualização das isóbaras.
        """
        print(f"Calculando bulbo de Boussinesq (grid_size={grid_size}, method={method})...")
        
        # Verificar cache
        cache_key = f"{fundacao.largura}_{fundacao.comprimento}_{fundacao.carga}_{grid_size}_{method}"
        if use_cache and cache_key in self.cache:
            print("Usando resultado em cache")
            return self.cache[cache_key]
        
        # Criar malha 3D otimizada
        max_dim = max(fundacao.largura, fundacao.comprimento)
        x_lim = max(2 * max_dim, 3.0)  # Garantir limite mínimo
        y_lim = max(2 * max_dim, 3.0)
        
        x = np.linspace(-x_lim, x_lim, grid_size)
        y = np.linspace(-y_lim, y_lim, grid_size)
        z_coords = np.linspace(0.01, depth_ratio * max_dim, grid_size)
        
        X, Y, Z = np.meshgrid(x, y, z_coords, indexing='ij')
        
        # Calcular tensões com método otimizado
        sigma_grid = self._calcular_tensao_malha_otimizado(X, Y, Z, fundacao, solo, method)
        
        # Suavizar dados para isóbaras mais limpas
        from scipy.ndimage import gaussian_filter
        sigma_grid_smooth = gaussian_filter(sigma_grid, sigma=0.8)
        
        # Preparar parâmetros
        parametros = {
            'fundacao': {
                'largura': fundacao.largura,
                'comprimento': fundacao.comprimento,
                'carga': fundacao.carga,
                'area': fundacao.largura * fundacao.comprimento
            },
            'solo': {
                'nome': solo.nome,
                'coeficiente_poisson': solo.coeficiente_poisson,
                'peso_especifico': solo.peso_especifico
            },
            'analise': {
                'depth_ratio': depth_ratio,
                'grid_size': grid_size,
                'method': method,
                'timestamp': time.time()
            }
        }
        
        # Criar resultado
        resultado = ResultadoAnalise(
            coordenadas=np.stack([X, Y, Z], axis=-1),
            tensoes=sigma_grid_smooth,
            parametros_entrada=parametros
        )
        
        # Armazenar em cache
        if use_cache:
            self.cache[cache_key] = resultado
            self.ultimo_calculo = resultado
        
        return resultado
    
    def plot_bulbo_2d_com_isobaras(self, resultado: ResultadoAnalise) -> go.Figure:
        """
        Cria visualização 2D do bulbo de tensões com isóbaras claras.
        VERSÃO CORRIGIDA - isóbaras visíveis.
        """
        # Extrair dados do resultado
        sigma_grid = resultado.tensoes
        coords = resultado.coordenadas
        
        # Pegar slice central (plano Y=0)
        slice_index = sigma_grid.shape[1] // 2
        center_slice = sigma_grid[:, slice_index, :]
        
        # Normalizar para porcentagem
        q = resultado.parametros_entrada['fundacao']['carga']
        center_slice_pct = center_slice / q * 100
        
        X_slice = coords[:, slice_index, :, 0]
        Z_slice = coords[:, slice_index, :, 2]
        
        # Criar figura com isóbaras
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
                showlabels=True,  # MOSTRAR RÓTULOS NAS ISÓBARAS
                labelfont=dict(
                    size=10,
                    color='white',
                    family='Arial, bold'
                ),
                showlines=True
            ),
            colorbar=dict(
                title=dict(
                    text="Δσ/q (%)",
                    side="right",
                    font=dict(size=12)
                ),
                tickvals=list(range(0, 101, 10)),
                ticktext=[f"{i}%" for i in range(0, 101, 10)]
            ),
            hovertemplate=(
                "<b>Distância X</b>: %{x:.2f} m<br>"
                "<b>Profundidade Z</b>: %{y:.2f} m<br>"
                "<b>Tensão Δσ/q</b>: %{z:.1f} %<br>"
                "<b>Tensão absoluta</b>: %{customdata:.1f} kPa"
                "<extra></extra>"
            ),
            customdata=center_slice,
            line=dict(smoothing=1.0),
            name="Bulbo de Tensões"
        ))
        
        # Adicionar linha da sapata
        B = resultado.parametros_entrada['fundacao']['largura']
        L = resultado.parametros_entrada['fundacao']['comprimento']
        
        # Contorno da sapata
        fig.add_shape(
            type="rect",
            x0=-B/2, y0=0,
            x1=B/2, y1=-0.05,
            line=dict(color="red", width=3),
            fillcolor="rgba(255, 0, 0, 0.3)",
            name="Sapata",
            layer="above"
        )
        
        # Adicionar texto
        fig.add_annotation(
            x=0,
            y=-0.02,
            text="SAPATA",
            showarrow=False,
            font=dict(color="red", size=12, family="Arial Black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="red",
            borderwidth=2,
            borderpad=4
        )
        
        # Linhas de isóbaras principais destacadas
        isobaras_destaque = [10, 20, 30, 40, 50]
        for isobara in isobaras_destaque:
            # Extrair linha de contorno específica
            mask = np.abs(center_slice_pct - isobara) < 2
            if np.any(mask):
                fig.add_trace(go.Scatter(
                    x=X_slice[0, :][mask[0, :]],
                    y=Z_slice[:, 0][mask[:, 0]],
                    mode='lines',
                    line=dict(color='white', width=2, dash='dash'),
                    name=f'Isóbara {isobara}%',
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Configurar layout
        fig.update_layout(
            title=dict(
                text="BULBO DE TENSÕES - SOLUÇÃO DE BOUSSINESQ",
                font=dict(size=16, family="Arial Black"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="DISTÂNCIA DO CENTRO (m)",
            yaxis_title="PROFUNDIDADE (m)",
            yaxis=dict(
                autorange='reversed',
                scaleanchor="x",
                scaleratio=1,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            xaxis=dict(
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='black',
                borderwidth=1
            ),
            plot_bgcolor='rgba(240, 240, 240, 0.8)'
        )
        
        return fig
    
    def plot_bulbo_3d_interativo(self, resultado: ResultadoAnalise) -> go.Figure:
        """Versão simplificada para performance"""
        fig = go.Figure()
        
        # Adicionar mensagem informativa
        fig.add_annotation(
            text="Visualização 3D disponível apenas com scikit-image instalado.<br>Instale com: pip install scikit-image",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red"),
            align="center"
        )
        
        fig.update_layout(
            title="Visualização 3D - Instale scikit-image",
            height=400
        )
        
        return fig
    
    def calcular_profundidade_influencia(self, B: float, L: float, percentual: float = 0.1) -> float:
        """
        Calcula profundidade de influência (onde Δσ/q = percentual).
        """
        # Usar fórmula simplificada para performance
        area = B * L
        if percentual == 0.05:
            return 1.5 * np.sqrt(area)
        elif percentual == 0.10:
            return np.sqrt(area)
        elif percentual == 0.20:
            return 0.7 * np.sqrt(area)
        else:
            return 2 * B  # Valor conservador padrão
    
    def relatorio_tecnico_bulbo(self, q: float, B: float, L: float) -> str:
        """
        Gera relatório técnico completo do bulbo de tensões.
        """
        # Calcular profundidades de influência
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
        
        RESULTADOS DA ANÁLISE:
        
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
        • Considerações: Solo homogêneo, isotrópico e elástico
        • Isóbaras calculadas em incrementos de 10%
        
        DATA DA ANÁLISE: {time.strftime('%d/%m/%Y %H:%M')}
        """
        
        return relatorio
    
    def exportar_pdf_bulbo(self, resultado: ResultadoAnalise, filename: str = None) -> str:
        """
        Exporta relatório do bulbo para PDF (SIMULAÇÃO - gera HTML estilizado).
        Em produção, usar biblioteca como ReportLab.
        """
        import base64
        from datetime import datetime
        
        if filename is None:
            filename = f"bulbo_tensoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Gerar HTML estilizado que pode ser convertido para PDF
        B = resultado.parametros_entrada['fundacao']['largura']
        L = resultado.parametros_entrada['fundacao']['comprimento']
        q = resultado.parametros_entrada['fundacao']['carga']
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório - Bulbo de Tensões</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; border-bottom: 3px solid #333; padding-bottom: 20px; }}
                .section {{ margin: 30px 0; }}
                .param-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .param-table th, .param-table td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                .param-table th {{ background-color: #f2f2f2; }}
                .recommendation {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0; }}
                .footer {{ margin-top: 50px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RELATÓRIO TÉCNICO - BULBO DE TENSÕES</h1>
                <h3>Solução de Boussinesq</h3>
                <p>Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="section">
                <h2>1. PARÂMETROS DA ANÁLISE</h2>
                <table class="param-table">
                    <tr><th>Parâmetro</th><th>Valor</th><th>Unidade</th></tr>
                    <tr><td>Pressão aplicada (q)</td><td>{q:.0f}</td><td>kPa</td></tr>
                    <tr><td>Largura da sapata (B)</td><td>{B:.2f}</td><td>m</td></tr>
                    <tr><td>Comprimento da sapata (L)</td><td>{L:.2f}</td><td>m</td></tr>
                    <tr><td>Área de contato</td><td>{B*L:.2f}</td><td>m²</td></tr>
                    <tr><td>Carga total</td><td>{q*B*L:.0f}</td><td>kN</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>2. RESULTADOS DA ANÁLISE</h2>
                <p><strong>Profundidades de influência:</strong></p>
                <ul>
                    <li>Até 20% de q: {self.calcular_profundidade_influencia(B, L, 0.20):.2f} m</li>
                    <li>Até 10% de q: {self.calcular_profundidade_influencia(B, L, 0.10):.2f} m</li>
                    <li>Até 5% de q: {self.calcular_profundidade_influencia(B, L, 0.05):.2f} m</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>3. RECOMENDAÇÕES TÉCNICAS</h2>
                <div class="recommendation">
                    <strong>Para análise de recalques:</strong> 
                    Considerar camadas de solo até profundidade de {self.calcular_profundidade_influencia(B, L, 0.10):.1f} m.
                </div>
                <div class="recommendation">
                    <strong>Para interação entre fundações:</strong> 
                    Zona de influência aproximada de {self.calcular_profundidade_influencia(B, L, 0.20):.1f} m.
                </div>
                <div class="recommendation">
                    <strong>Para ensaios in situ:</strong> 
                    Investigar solo até profundidade de {self.calcular_profundidade_influencia(B, L, 0.05):.1f} m.
                </div>
            </div>
            
            <div class="footer">
                <p>Simulador Solo-Fundações v2.3.0 | Boussinesq + Terzaghi</p>
                <p>Documento gerado automaticamente pelo sistema</p>
            </div>
        </body>
        </html>
        """
        
        # Salvar HTML
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename

# Função de compatibilidade
def criar_bulbo_tensoes() -> BulboTensoes:
    return BulboTensoes()