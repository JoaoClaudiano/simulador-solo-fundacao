"""
BULBO DE TENSÕES - SOLUÇÃO DE BOUSSINESQ
Implementação completa para cálculo e visualização de distribuição de tensões no solo
Refatorado com dataclasses e visualização 3D
"""
import numpy as np
from scipy import integrate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Tuple, Optional, Dict, Any
import warnings
import time

# Importações locais
try:
    from .models import Solo, Fundacao, ResultadoAnalise
except ImportError:
    # Fallback para desenvolvimento
    from dataclasses import dataclass
    
    @dataclass
    class Solo:
        nome: str = "Solo"
        peso_especifico: float = 18.0
        angulo_atrito: Optional[float] = None
        coesao: Optional[float] = None
        modulo_elasticidade: Optional[float] = None
        coeficiente_poisson: float = 0.3
    
    @dataclass
    class Fundacao:
        largura: float = 1.5
        comprimento: float = 1.5
        carga: float = 200.0
    
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
    
    @staticmethod
    def boussinesq_rectangular_load(
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
            # Método dos coeficientes de influência de Newmark
            if z == 0:
                # Na superfície, dentro da área carregada
                if abs(x) <= B/2 and abs(y) <= L/2:
                    return q
                else:
                    return 0.0
            
            m = abs(x) / (B/2)
            n = abs(y) / (L/2)
            
            # Coeficientes m e n normalizados
            m_prime = B / (2 * z)
            n_prime = L / (2 * z)
            
            # Cálculo do fator de influência Iσ
            I_sigma = self._calcular_fator_influencia_newmark(m_prime, n_prime)
            
            sigma_z = q * I_sigma
            
        else:  # method == 'integration'
            # Integração numérica da solução de Boussinesq
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
                # Fallback para Newmark se a integração falhar
                sigma_z = BulboTensoes.boussinesq_rectangular_load(q, B, L, x, y, z, nu, 'newmark')
        
        return sigma_z
    
    @staticmethod
    def _calcular_fator_influencia_newmark(m: float, n: float) -> float:
        """Calcula fator de influência usando fórmulas de Newmark"""
        m2 = m**2
        n2 = n**2
        m2_n2 = m2 + n2
        
        if m2_n2 == 0:
            return 0.0
        
        sqrt_term = np.sqrt(1 + m2 + n2)
        
        # Fórmula de Newmark para tensão vertical
        term1 = (2 * m * n * sqrt_term) / (m2_n2 + m2_n2 * sqrt_term + 1)
        term2 = (m2 + n2 + 2) / (m2 + n2 + 1)
        term3 = np.arctan((2 * m * n * sqrt_term) / (m2_n2 - m2_n2 * sqrt_term + 1))
        
        I = (1 / (4 * np.pi)) * (term1 * term2 + term3)
        
        return I
    
    @staticmethod
    def _criar_malha_tridimensional(
        fundacao: Fundacao, 
        depth_ratio: float = 3.0, 
        grid_size: int = 50
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Cria uma malha 3D otimizada para análise.
        """
        # Ajustar limites baseados nas dimensões da fundação
        max_dim = max(fundacao.largura, fundacao.comprimento)
        x_lim = 2 * max_dim
        y_lim = 2 * max_dim
        
        x = np.linspace(-x_lim, x_lim, grid_size)
        y = np.linspace(-y_lim, y_lim, grid_size)
        z_coords = np.linspace(0.01, depth_ratio * max_dim, grid_size)  # Evitar z=0
        
        X, Y, Z = np.meshgrid(x, y, z_coords, indexing='ij')
        return X, Y, Z
    
    def _calcular_tensao_malha_vetorizado(
        self,
        X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
        fundacao: Fundacao, solo: Solo, method: str = 'newmark'
    ) -> np.ndarray:
        """
        Calcula tensão vertical na malha usando vetorização para performance.
        """
        start_time = time.time()
        
        # Inicializar array de tensões
        sigma_grid = np.zeros_like(X)
        
        # Calcular tensões para cada ponto (vetorizado onde possível)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                for k in range(X.shape[2]):
                    x_val = X[i, j, k]
                    y_val = Y[i, j, k]
                    z_val = Z[i, j, k]
                    
                    # Verificar se está dentro da área carregada na superfície
                    if z_val < 0.01:  # Próximo da superfície
                        if (abs(x_val) <= fundacao.largura/2 and 
                            abs(y_val) <= fundacao.comprimento/2):
                            sigma_grid[i, j, k] = fundacao.carga
                        else:
                            sigma_grid[i, j, k] = 0
                    else:
                        sigma_grid[i, j, k] = self.boussinesq_rectangular_load(
                            fundacao.carga, fundacao.largura, fundacao.comprimento,
                            x_val, y_val, z_val,
                            nu=solo.coeficiente_poisson, method=method
                        )
        
        print(f"Tempo cálculo: {time.time() - start_time:.2f}s")
        return sigma_grid
    
    def gerar_bulbo_boussinesq_avancado(
        self, 
        fundacao: Fundacao, 
        solo: Solo, 
        depth_ratio: float = 3.0, 
        grid_size: int = 50,
        method: str = 'newmark',
        use_cache: bool = True
    ) -> ResultadoAnalise:
        """
        Gera bulbo de tensões real usando Boussinesq (método avançado).
        
        Args:
            fundacao: Objeto Fundacao com parâmetros
            solo: Objeto Solo com parâmetros
            depth_ratio: Razão profundidade/largura
            grid_size: Resolução da malha
            method: Método de cálculo ('newmark' ou 'integration')
            use_cache: Usar cache para cálculos repetidos
            
        Returns:
            ResultadoAnalise com coordenadas, tensões e parâmetros
        """
        print(f"Calculando bulbo de Boussinesq (grid_size={grid_size}, method={method})...")
        
        # Verificar cache
        cache_key = f"{fundacao.largura}_{fundacao.comprimento}_{fundacao.carga}_{grid_size}_{method}"
        if use_cache and cache_key in self.cache:
            print("Usando resultado em cache")
            return self.cache[cache_key]
        
        # Criar malha 3D
        X, Y, Z = self._criar_malha_tridimensional(fundacao, depth_ratio, grid_size)
        
        # Calcular tensões
        sigma_grid = self._calcular_tensao_malha_vetorizado(X, Y, Z, fundacao, solo, method)
        
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
            tensoes=sigma_grid,
            parametros_entrada=parametros
        )
        
        # Armazenar em cache
        if use_cache:
            self.cache[cache_key] = resultado
            self.ultimo_calculo = resultado
        
        return resultado
    
    def plot_bulbo_2d(self, resultado: ResultadoAnalise) -> go.Figure:
        """
        Cria visualização 2D do bulbo de tensões (corte no plano Y=0).
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
        
        # Criar figura
        fig = go.Figure(data=go.Contour(
            z=center_slice_pct,
            x=X_slice[0, :],
            y=Z_slice[:, 0],
            colorscale='Plasma',
            contours=dict(
                start=0,
                end=100,
                size=10,
                coloring='heatmap'
            ),
            colorbar=dict(
                title="Δσ/q (%)",
                titleside="right",
                tickvals=list(range(0, 101, 10))
            ),
            hovertemplate=(
                "<b>Distância X</b>: %{x:.2f} m<br>"
                "<b>Profundidade Z</b>: %{y:.2f} m<br>"
                "<b>Tensão Δσ/q</b>: %{z:.1f} %<br>"
                "<b>Tensão absoluta</b>: %{customdata:.1f} kPa"
                "<extra></extra>"
            ),
            customdata=center_slice,
            line_smoothing=0.85,
            name="Bulbo de Tensões"
        ))
        
        # Adicionar contorno da sapata
        B = resultado.parametros_entrada['fundacao']['largura']
        
        fig.add_shape(
            type="rect",
            x0=-B/2, y0=0,
            x1=B/2, y1=-0.05,
            line=dict(color="red", width=3),
            fillcolor="rgba(255, 0, 0, 0.2)",
            name="Sapata",
            layer="above"
        )
        
        # Configurar layout
        fig.update_layout(
            title="Bulbo de Tensões - Solução de Boussinesq (Corte Y=0)",
            xaxis_title="Distância do Centro (m)",
            yaxis_title="Profundidade (m)",
            yaxis=dict(
                autorange='reversed',
                scaleanchor="x",
                scaleratio=1
            ),
            height=550,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def plot_bulbo_3d_interativo(self, resultado: ResultadoAnalise) -> go.Figure:
        """
        Cria visualização 3D interativa do bulbo de tensões.
        """
        # Extrair dados
        sigma_grid = resultado.tensoes
        coords = resultado.coordenadas
        q = resultado.parametros_entrada['fundacao']['carga']
        
        # Normalizar para porcentagem
        sigma_pct = sigma_grid / q * 100
        
        # Reduzir resolução para performance 3D
        stride = max(1, sigma_grid.shape[0] // 30)
        X = coords[::stride, ::stride, ::stride, 0]
        Y = coords[::stride, ::stride, ::stride, 1]
        Z = coords[::stride, ::stride, ::stride, 2]
        sigma_pct_sampled = sigma_pct[::stride, ::stride, ::stride]
        
        # Criar figura 3D
        fig = go.Figure()
        
        # Opção 1: Isosuperfícies (requer scikit-image)
        try:
            from skimage import measure
            
            st.info("Gerando isosuperfícies 3D...")
            
            # Definir níveis de tensão para visualização
            levels = [10, 20, 30, 40, 50]
            colors = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']
            
            for level, color in zip(levels, colors):
                # Extrair superfície do nível
                try:
                    vertices, faces, _, _ = measure.marching_cubes(
                        sigma_pct_sampled, 
                        level,
                        spacing=(
                            np.diff(X[0,0,:])[0],
                            np.diff(Y[0,:,0])[0],
                            np.diff(Z[:,0,0])[0]
                        )
                    )
                    
                    if len(vertices) > 0:
                        fig.add_trace(go.Mesh3d(
                            x=vertices[:, 0] + X.min(),
                            y=vertices[:, 1] + Y.min(),
                            z=vertices[:, 2] + Z.min(),
                            i=faces[:, 0],
                            j=faces[:, 1],
                            k=faces[:, 2],
                            color=color,
                            opacity=0.6,
                            name=f'{level}% q',
                            showlegend=True,
                            hoverinfo='name'
                        ))
                except:
                    continue
                    
        except ImportError:
            # Opção 2: Nuvem de pontos colorida (fallback)
            st.warning("scikit-image não instalado. Usando visualização 3D simplificada.")
            
            # Amostrar pontos para performance
            sample_size = 5000
            indices = np.random.choice(
                X.size, 
                size=min(sample_size, X.size), 
                replace=False
            )
            
            fig.add_trace(go.Scatter3d(
                x=X.flatten()[indices],
                y=Y.flatten()[indices],
                z=Z.flatten()[indices],
                mode='markers',
                marker=dict(
                    size=3,
                    color=sigma_pct_sampled.flatten()[indices],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Δσ/q (%)"),
                    cmin=0,
                    cmax=100,
                    opacity=0.6
                ),
                name='Distribuição de Tensões',
                hovertemplate=(
                    "X: %{x:.2f}m<br>"
                    "Y: %{y:.2f}m<br>"
                    "Z: %{z:.2f}m<br>"
                    "Δσ/q: %{marker.color:.1f}%"
                    "<extra></extra>"
                )
            ))
        
        # Adicionar sapata como retângulo 3D
        B = resultado.parametros_entrada['fundacao']['largura']
        L = resultado.parametros_entrada['fundacao']['comprimento']
        
        # Pontos da sapata
        sapata_x = [-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2]
        sapata_y = [-L/2, -L/2, L/2, L/2, -L/2, -L/2, L/2, L/2]
        sapata_z = [0, 0, 0, 0, -0.1, -0.1, -0.1, -0.1]
        
        # Triângulos para a malha
        i = [0, 0, 0, 4, 4, 6]
        j = [1, 2, 3, 5, 6, 7]
        k = [2, 3, 0, 6, 7, 4]
        
        fig.add_trace(go.Mesh3d(
            x=sapata_x,
            y=sapata_y,
            z=sapata_z,
            i=i,
            j=j,
            k=k,
            color='red',
            opacity=0.7,
            name='Sapata',
            showlegend=True
        ))
        
        # Configurar cena 3D
        fig.update_layout(
            title="Bulbo de Tensões 3D - Solução de Boussinesq",
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Profundidade Z (m)",
                aspectmode='manual',
                aspectratio=dict(x=2, y=2, z=1),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=0.8),
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=-0.5)
                ),
                zaxis=dict(
                    autorange='reversed',
                    title="Profundidade (m)"
                )
            ),
            height=700,
            showlegend=True,
            legend=dict(
                x=0.8,
                y=0.9,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        return fig
    
    def plot_comparativo_profundidade(self, resultado: ResultadoAnalise) -> go.Figure:
        """
        Cria gráfico comparativo de tensão vs profundidade em diferentes pontos.
        """
        sigma_grid = resultado.tensoes
        coords = resultado.coordenadas
        q = resultado.parametros_entrada['fundacao']['carga']
        
        # Definir pontos de análise
        pontos = [
            (0, 0, "Centro"),
            (resultado.parametros_entrada['fundacao']['largura']/2, 0, "Borda X"),
            (0, resultado.parametros_entrada['fundacao']['comprimento']/2, "Borda Y"),
            (resultado.parametros_entrada['fundacao']['largura'], 0, "Fora X"),
        ]
        
        fig = go.Figure()
        
        for x_offset, y_offset, nome in pontos:
            # Encontrar índices mais próximos
            x_idx = np.argmin(np.abs(coords[0, 0, :, 0] - x_offset))
            y_idx = np.argmin(np.abs(coords[0, :, 0, 1] - y_offset))
            
            # Extrair perfil de tensão
            z_coords = coords[0, 0, :, 2]
            tensoes = sigma_grid[x_idx, y_idx, :] / q * 100
            
            fig.add_trace(go.Scatter(
                x=tensoes,
                y=z_coords,
                mode='lines+markers',
                name=nome,
                hovertemplate=f"{nome}<br>Tensão: %{{x:.1f}}%<br>Profundidade: %{{y:.2f}}m"
            ))
        
        fig.update_layout(
            title="Perfil de Tensão vs Profundidade",
            xaxis_title="Δσ/q (%)",
            yaxis_title="Profundidade (m)",
            yaxis=dict(autorange='reversed'),
            height=500,
            showlegend=True
        )
        
        return fig
    
    def calcular_profundidade_influencia(self, B: float, L: float, percentual: float = 0.1) -> float:
        """
        Calcula profundidade de influência (onde Δσ/q = percentual).
        """
        z_values = np.linspace(0.1, 5 * B, 500)
        
        for z in z_values:
            influencia = self.boussinesq_rectangular_load(
                1.0, B, L, 0, 0, z, method='newmark'
            )
            
            if influencia < percentual:
                return z
        
        return 2 * B  # Valor conservador padrão
    
    def relatorio_tecnico_bulbo(self, q: float, B: float, L: float) -> str:
        """
        Gera relatório técnico completo do bulbo de tensões.
        """
        # Calcular profundidades de influência
        z_10 = self.calcular_profundidade_influencia(B, L, 0.10)
        z_20 = self.calcular_profundidade_influencia(B, L, 0.20)
        z_05 = self.calcular_profundidade_influencia(B, L, 0.05)
        
        # Calcular tensões em pontos-chave
        sigma_centro_zB = self.boussinesq_rectangular_load(q, B, L, 0, 0, B, method='newmark')
        sigma_centro_2zB = self.boussinesq_rectangular_load(q, B, L, 0, 0, 2*B, method='newmark')
        
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
        
        TENSÕES EM PONTOS CARACTERÍSTICOS:
        • No centro, à profundidade z = B:
          Δσ = {sigma_centro_zB:.1f} kPa ({sigma_centro_zB/q*100:.1f}% de q)
        
        • No centro, à profundidade z = 2B:
          Δσ = {sigma_centro_2zB:.1f} kPa ({sigma_centro_2zB/q*100:.1f}% de q)
        
        RECOMENDAÇÕES TÉCNICAS:
        1. Para análise de recalques: considerar até profundidade {z_10:.1f} m
        2. Para interação entre fundações: zona de influência ≈ {z_20:.1f} m
        3. Para ensaios in situ: investigar até {z_05:.1f} m
        
        OBSERVAÇÕES:
        • Método utilizado: Solução de Boussinesq para carga retangular
        • Considerações: Solo homogêneo, isotrópico e elástico
        • Limitações: Não considera estratificação ou comportamento não-linear
        """
        
        return relatorio
    
    def exportar_dados_csv(self, resultado: ResultadoAnalise, filename: str = "bulbo_tensoes.csv"):
        """
        Exporta dados do bulbo para arquivo CSV.
        """
        sigma_grid = resultado.tensoes
        coords = resultado.coordenadas
        
        # Preparar dados para exportação
        data = []
        for i in range(coords.shape[0]):
            for j in range(coords.shape[1]):
                for k in range(coords.shape[2]):
                    data.append({
                        'x': coords[i, j, k, 0],
                        'y': coords[i, j, k, 1],
                        'z': coords[i, j, k, 2],
                        'tensao_kPa': sigma_grid[i, j, k],
                        'tensao_percentual': sigma_grid[i, j, k] / resultado.parametros_entrada['fundacao']['carga'] * 100
                    })
        
        # Converter para DataFrame e exportar
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
        return filename
    
    def limpar_cache(self):
        """Limpa o cache de resultados calculados."""
        self.cache.clear()
        self.ultimo_calculo = None


# Funções auxiliares para compatibilidade
def criar_bulbo_tensoes() -> BulboTensoes:
    """Factory function para criar instância de BulboTensoes."""
    return BulboTensoes()


# Exemplo de uso
if __name__ == "__main__":
    print("Testando módulo BulboTensoes...")
    
    # Criar objetos de teste
    solo_teste = Solo(nome="Areia Média", peso_especifico=18.5, coeficiente_poisson=0.3)
    fundacao_teste = Fundacao(largura=2.0, comprimento=2.0, carga=200.0)
    
    # Criar calculador
    bulbo = BulboTensoes()
    
    # Calcular bulbo
    resultado = bulbo.gerar_bulbo_boussinesq_avancado(
        fundacao=fundacao_teste,
        solo=solo_teste,
        grid_size=30,
        method='newmark'
    )
    
    print(f"Bulbo calculado com sucesso!")
    print(f"Dimensões: {resultado.tensoes.shape}")
    print(f"Tensão máxima: {resultado.tensoes.max():.1f} kPa")
    
    # Gerar relatório
    relatorio = bulbo.relatorio_tecnico_bulbo(200, 2, 2)
    print(relatorio)
