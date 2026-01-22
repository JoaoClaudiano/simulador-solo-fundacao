"""
Implementação do bulbo de tensões real usando:
1. Solução de Boussinesq para carga pontual
2. Integração de Newmark para carga distribuída
3. Método 2:1 (simplificado para comparação)

Refatorado para uso de dataclasses e estrutura modular.
"""
import numpy as np
from scipy import integrate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Tuple, Optional
import warnings

# Importações locais
try:
    from .models import Solo, Fundacao, ResultadoAnalise
except ImportError:
    # Fallback para desenvolvimento
    from dataclasses import dataclass
    import numpy as np
    from typing import Dict, Any, Optional
    
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
    """Classe para cálculo e visualização de bulbos de tensões"""
    
    @staticmethod
    def boussinesq_point_load(Q: float, x: float, y: float, z: float, nu: float = 0.3) -> float:
        """
        Solução de Boussinesq para carga pontual
        """
        r = np.sqrt(x**2 + y**2)
        R = np.sqrt(r**2 + z**2)
        
        if R == 0:
            return np.inf
        
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
        """
        if method == 'newmark':
            m = B / z if z > 0 else 0
            n = L / z if z > 0 else 0
            
            m2 = m**2
            n2 = n**2
            m2_n2 = m2 + n2
            sqrt_term = np.sqrt(1 + m2 + n2)
            
            I = (1/(4*np.pi)) * (
                (2*m*n*sqrt_term/(m2_n2 + m2_n2*sqrt_term + 1)) * 
                ((m2 + n2 + 2)/(m2 + n2 + 1)) +
                np.arctan((2*m*n*sqrt_term)/(m2_n2 - m2_n2*sqrt_term + 1))
            )
            
            sigma_z = q * I
            
        else:
            def integrand(xi: float, eta: float) -> float:
                r = np.sqrt((x - xi)**2 + (y - eta)**2 + z**2)
                if r == 0:
                    return 0
                return (3 * z**3) / (2 * np.pi * r**5)
            
            result, _ = integrate.dblquad(
                integrand,
                -B/2, B/2,
                lambda x: -L/2, lambda x: L/2
            )
            
            sigma_z = q * result
        
        return sigma_z
    
    @staticmethod
    def metodo_21_simplificado(B: float, L: float, z: float) -> float:
        """
        Método 2:1 simplificado (aproximação)
        """
        if z == 0:
            return 1.0
        
        B_eff = B + z
        L_eff = L + z
        
        return (B * L) / (B_eff * L_eff)
    
    @staticmethod
    def _criar_malha_tridimensional(
        fundacao: Fundacao, 
        depth_ratio: float = 3.0, 
        grid_size: int = 50
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Cria uma malha 3D para análise.
        """
        x = np.linspace(-2*fundacao.largura, 2*fundacao.largura, grid_size)
        y = np.linspace(-2*fundacao.largura, 2*fundacao.largura, grid_size)
        z_coords = np.linspace(0, depth_ratio*fundacao.largura, grid_size)
        
        X, Y, Z = np.meshgrid(x, y, z_coords, indexing='ij')
        return X, Y, Z
    
    @staticmethod
    def _calcular_tensao_malha(
        X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
        fundacao: Fundacao, solo: Solo, method: str = 'newmark'
    ) -> np.ndarray:
        """
        Calcula a tensão vertical em cada ponto da malha.
        """
        sigma_grid = np.zeros_like(X)
        grid_size = X.shape[0]
        
        # Otimização: vetorizar quando possível
        for i in range(grid_size):
            for j in range(grid_size):
                for k in range(grid_size):
                    if Z[i, j, k] == 0:
                        if (abs(X[i, j, k]) <= fundacao.largura/2 and 
                            abs(Y[i, j, k]) <= fundacao.comprimento/2):
                            sigma_grid[i, j, k] = fundacao.carga
                        else:
                            sigma_grid[i, j, k] = 0
                    else:
                        sigma_grid[i, j, k] = BulboTensoes.boussinesq_rectangular_load(
                            fundacao.carga, fundacao.largura, fundacao.comprimento, 
                            X[i, j, k], Y[i, j, k], Z[i, j, k],
                            nu=solo.coeficiente_poisson, method=method
                        )
        return sigma_grid
    
    def gerar_bulbo_boussinesq_legado(
        self, q: float, B: float, L: float, depth_ratio: float = 3.0, 
        grid_size: int = 50, method: str = 'newmark'
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Método legado mantido para compatibilidade.
        """
        warnings.warn("Use gerar_bulbo_boussinesq_avancado em vez disso.", DeprecationWarning)
        
        fundacao = Fundacao(largura=B, comprimento=L, carga=q)
        solo = Solo(nome="Legacy", peso_especifico=18.0, coeficiente_poisson=0.3)
        
        resultado = self.gerar_bulbo_boussinesq_avancado(fundacao, solo, depth_ratio, grid_size, method)
        
        X = resultado.coordenadas[:, :, :, 0]
        Y = resultado.coordenadas[:, :, :, 1]
        Z = resultado.coordenadas[:, :, :, 2]
        sigma_grid = resultado.tensoes
        
        return X, Y, Z, sigma_grid
    
    def gerar_bulbo_boussinesq_avancado(
        self, fundacao: Fundacao, solo: Solo, 
        depth_ratio: float = 3.0, grid_size: int = 50,
        method: str = 'newmark'
    ) -> ResultadoAnalise:
        """
        Gera bulbo de tensões real usando Boussinesq (avançado).
        """
        print(f"Calculando bulbo de Boussinesq (grid_size={grid_size})...")
        
        X, Y, Z = self._criar_malha_tridimensional(fundacao, depth_ratio, grid_size)
        sigma_grid = self._calcular_tensao_malha(X, Y, Z, fundacao, solo, method)
        
        parametros = {
            'fundacao': fundacao.__dict__,
            'solo': solo.__dict__,
            'depth_ratio': depth_ratio,
            'grid_size': grid_size,
            'method': method
        }
        
        return ResultadoAnalise(
            coordenadas=np.stack([X, Y, Z], axis=-1),
            tensoes=sigma_grid,
            parametros_entrada=parametros
        )
    
    def gerar_bulbo_21(
        self, B: float, L: float, depth_ratio: float = 3.0, 
        grid_size: int = 50
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Gera bulbo usando método 2:1 simplificado
        """
        x = np.linspace(-2*B, 2*B, grid_size)
        z = np.linspace(0, depth_ratio*B, grid_size)
        
        X, Z = np.meshgrid(x, z)
        sigma_grid = np.zeros_like(X)
        
        for i in range(grid_size):
            for j in range(grid_size):
                if Z[i, j] == 0:
                    sigma_grid[i, j] = 1.0 if abs(X[i, j]) <= B/2 else 0
                else:
                    sigma_grid[i, j] = self.metodo_21_simplificado(B, L, Z[i, j])
        
        return X, Z, sigma_grid
    
    def plot_comparativo_bulbos(self, q: float, B: float, L: float, depth_ratio: float = 3.0):
        """
        Cria gráfico comparativo entre métodos
        """
        X_21, Z_21, sigma_21 = self.gerar_bulbo_21(B, L, depth_ratio)
        X_b, Y_b, Z_b, sigma_b = self.gerar_bulbo_boussinesq_legado(q, B, L, depth_ratio)
        
        center_slice = sigma_b[:, sigma_b.shape[1]//2, :]
        X_b_slice = X_b[:, 0, :]
        Z_b_slice = Z_b[:, 0, :]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Método 2:1 Simplificado', 'Método Boussinesq (Real)'),
            specs=[[{'type': 'contour'}, {'type': 'contour'}]]
        )
        
        fig.add_trace(
            go.Contour(
                z=sigma_21 * 100,
                x=X_21[0, :],
                y=Z_21[:, 0],
                colorscale='Viridis',
                contours=dict(start=0, end=100, size=10),
                colorbar=dict(title="Δσ/q (%)", x=0.45),
                name="Método 2:1",
                hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Contour(
                z=center_slice * 100,
                x=X_b_slice[0, :],
                y=Z_b_slice[:, 0],
                colorscale='Plasma',
                contours=dict(start=0, end=100, size=10),
                colorbar=dict(title="Δσ/q (%)", x=1.02),
                name="Boussinesq",
                hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="Comparação: Bulbo de Tensões - Método 2:1 vs Boussinesq",
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Distância do centro (m)", row=1, col=1)
        fig.update_xaxes(title_text="Distância do centro (m)", row=1, col=2)
        fig.update_yaxes(title_text="Profundidade (m)", autorange='reversed', row=1, col=1)
        fig.update_yaxes(title_text="Profundidade (m)", autorange='reversed', row=1, col=2)
        
        for col in [1, 2]:
            fig.add_shape(
                type="rect",
                x0=-B/2, y0=0,
                x1=B/2, y1=-0.05*depth_ratio*B,
                line=dict(color="red", width=2),
                fillcolor="rgba(255,0,0,0.1)",
                row=1, col=col
            )
        
        return fig
    
    def calcular_profundidade_influencia(self, B: float, L: float, percentual: float = 0.1) -> float:
        """
        Calcula profundidade de influência (onde Δσ/q = percentual)
        """
        z_values = np.linspace(0, 5*B, 1000)
        
        for z in z_values:
            if z == 0:
                influence = 1.0
            else:
                influence = self.boussinesq_rectangular_load(
                    1.0, B, L, 0, 0, z, method='newmark'
                )
            
            if influence < percentual:
                return z
        
        return 2 * B
    
    def relatorio_tecnico_bulbo(self, q: float, B: float, L: float) -> str:
        """
        Gera relatório técnico comparativo
        """
        z_10 = self.calcular_profundidade_influencia(B, L, 0.10)
        z_20 = self.calcular_profundidade_influencia(B, L, 0.20)
        
        sigma_centro_21 = self.metodo_21_simplificado(B, L, z_10)
        sigma_centro_bouss = self.boussinesq_rectangular_load(q, B, L, 0, 0, z_10, method='newmark') / q
        
        relatorio = f"""
        ================================================
        RELATÓRIO TÉCNICO - BULBO DE TENSÕES
        ================================================
        
        PARÂMETROS DA SAPATA:
        • Pressão aplicada (q): {q:.0f} kPa
        • Largura (B): {B:.2f} m
        • Comprimento (L): {L:.2f} m
        • Área: {B*L:.2f} m²
        
        RESULTADOS DOS MÉTODOS:
        
        1. MÉTODO 2:1 (SIMPLIFICADO):
           • Forma: Pirâmide/funil invertido
           • Propagação: Ângulo fixo de ≈ 26.6° (2:1)
           • Uso: Estimativas rápidas e didáticas
        
        2. MÉTODO DE BOUSSINESQ (TEÓRICO):
           • Forma: Bulbo/elipsoide real
           • Fundamento: Teoria da elasticidade
           • Uso: Projetos reais e análises precisas
        
        PROFUNDIDADES DE INFLUÊNCIA:
        • Até 20% de q: z ≈ {z_20:.2f} m ({z_20/B:.1f}×B)
        • Até 10% de q: z ≈ {z_10:.2f} m ({z_10/B:.1f}×B)
        
        COMPARAÇÃO NO CENTRO (z = {z_10:.2f} m):
        • Método 2:1: Δσ/q = {sigma_centro_21*100:.1f}%
        • Boussinesq: Δσ/q = {sigma_centro_bouss*100:.1f}%
        • Diferença: {abs(sigma_centro_21 - sigma_centro_bouss)*100:.1f}%
        """
        
        return relatorio

# Alias para compatibilidade
gerar_bulbo_boussinesq = BulboTensoes.gerar_bulbo_boussinesq_legado
