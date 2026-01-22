"""
Implementação do bulbo de tensões real usando:
1. Solução de Boussinesq para carga pontual
2. Integração de Newmark para carga distribuída
3. Método 2:1 (simplificado para comparação)
"""
import numpy as np
from scipy import integrate
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class BulboTensoes:
    """Classe para cálculo e visualização de bulbos de tensões"""
    
    @staticmethod
    def boussinesq_point_load(Q, x, y, z, nu=0.3):
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
    def boussinesq_rectangular_load(q, B, L, x, y, z, nu=0.3, method='newmark'):
        """
        Tensão vertical sob carga retangular uniforme
        
        Args:
            q: Pressão uniforme (kPa)
            B, L: Largura e comprimento da sapata (m)
            x, y: Coordenadas do ponto
            z: Profundidade (m)
            method: 'newmark' ou 'integration'
            
        Returns:
            sigma_z: Tensão vertical (kPa)
        """
        if method == 'newmark':
            # Método dos coeficientes de influência (Newmark simplificado)
            m = B / z if z > 0 else 0
            n = L / z if z > 0 else 0
            
            # Fatores para cálculo
            m2 = m**2
            n2 = n**2
            m2_n2 = m2 + n2
            sqrt_term = np.sqrt(1 + m2 + n2)
            
            # Coeficiente de influência
            I = (1/(4*np.pi)) * (
                (2*m*n*sqrt_term/(m2_n2 + m2_n2*sqrt_term + 1)) * 
                ((m2 + n2 + 2)/(m2 + n2 + 1)) +
                np.arctan((2*m*n*sqrt_term)/(m2_n2 - m2_n2*sqrt_term + 1))
            )
            
            sigma_z = q * I
            
        else:
            # Integração numérica da solução de Boussinesq
            def integrand(xi, eta):
                r = np.sqrt((x - xi)**2 + (y - eta)**2 + z**2)
                if r == 0:
                    return 0
                return (3 * z**3) / (2 * np.pi * r**5)
            
            # Integrar sobre a área da sapata
            result, error = integrate.dblquad(
                integrand,
                -B/2, B/2,
                lambda x: -L/2, lambda x: L/2
            )
            
            sigma_z = q * result
        
        return sigma_z
    
    @staticmethod
    def metodo_21_simplificado(B, L, z):
        """
        Método 2:1 simplificado (aproximação)
        
        Args:
            B, L: Dimensões da sapata
            z: Profundidade
            
        Returns:
            fator: Redução da tensão com profundidade
        """
        if z == 0:
            return 1.0
        
        B_eff = B + z
        L_eff = L + z
        
        return (B * L) / (B_eff * L_eff)
    
    def gerar_bulbo_boussinesq(self, q, B, L, depth_ratio=3.0, grid_size=50):
        """
        Gera bulbo de tensões real usando Boussinesq
        
        Args:
            q: Pressão (kPa)
            B, L: Dimensões (m)
            depth_ratio: Razão profundidade/largura
            grid_size: Resolução da malha
            
        Returns:
            X, Y, Z, sigma_grid: Malha 3D com tensões
        """
        # Criar malha 3D
        x = np.linspace(-2*B, 2*B, grid_size)
        y = np.linspace(-2*B, 2*B, grid_size)
        z = np.linspace(0, depth_ratio*B, grid_size)
        
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        sigma_grid = np.zeros_like(X)
        
        # Calcular tensão em cada ponto
        print("Calculando bulbo de Boussinesq...")
        for i in range(grid_size):
            for j in range(grid_size):
                for k in range(grid_size):
                    if Z[i, j, k] == 0:
                        # Na superfície
                        if abs(X[i, j, k]) <= B/2 and abs(Y[i, j, k]) <= L/2:
                            sigma_grid[i, j, k] = q
                        else:
                            sigma_grid[i, j, k] = 0
                    else:
                        sigma_grid[i, j, k] = self.boussinesq_rectangular_load(
                            q, B, L, 
                            X[i, j, k], Y[i, j, k], Z[i, j, k],
                            method='newmark'
                        )
        
        return X, Y, Z, sigma_grid
    
    def gerar_bulbo_21(self, B, L, depth_ratio=3.0, grid_size=50):
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
    
    def plot_comparativo_bulbos(self, q, B, L, depth_ratio=3.0):
        """
        Cria gráfico comparativo entre métodos
        
        Args:
            q: Pressão aplicada (kPa)
            B: Largura da sapata (m)
            L: Comprimento da sapata (m)
            depth_ratio: Razão profundidade/largura (padrão 3.0 m)
            
        
        """
        # Gerar dados para ambos métodos
        X_21, Z_21, sigma_21 = self.gerar_bulbo_21(B, L)
        X_b, Y_b, Z_b, sigma_b = self.gerar_bulbo_boussinesq(q, B, L)
        
        # Pegar slice central do bulbo 3D (y=0)
        center_slice = sigma_b[:, sigma_b.shape[1]//2, :]
        X_b_slice = X_b[:, 0, :]
        Z_b_slice = Z_b[:, 0, :]
        
        # Criar figura comparativa
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Método 2:1 Simplificado', 'Método Boussinesq (Real)'),
            specs=[[{'type': 'contour'}, {'type': 'contour'}]]
        )
        
        # Plot método 2:1
        fig.add_trace(
            go.Contour(
                z=sigma_21 * 100,
                x=X_21[0, :],
                y=Z_21[:, 0],
                colorscale='Viridis',
                contours=dict(
                    start=0,
                    end=100,
                    size=10
                ),
                colorbar=dict(title="Δσ/q (%)", x=0.45),
                name="Método 2:1",
                hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Plot método Boussinesq
        fig.add_trace(
            go.Contour(
                z=center_slice * 100,
                x=X_b_slice[0, :],
                y=Z_b_slice[:, 0],
                colorscale='Plasma',
                contours=dict(
                    start=0,
                    end=100,
                    size=10
                ),
                colorbar=dict(title="Δσ/q (%)", x=1.02),
                name="Boussinesq",
                hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
            ),
            row=1, col=2
        )
        
        # Atualizar layout
        fig.update_layout(
            title_text="Comparação: Bulbo de Tensões - Método 2:1 vs Boussinesq",
            height=500,
            showlegend=False
        )
        
        # Atualizar eixos
        fig.update_xaxes(title_text="Distância do centro (m)", row=1, col=1)
        fig.update_xaxes(title_text="Distância do centro (m)", row=1, col=2)
        fig.update_yaxes(title_text="Profundidade (m)", autorange='reversed', row=1, col=1)
        fig.update_yaxes(title_text="Profundidade (m)", autorange='reversed', row=1, col=2)
        
        # Adicionar contorno da sapata
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
    
    def plot_bulbo_3d_interativo(self, q, B, L):
        """
        Cria visualização 3D interativa do bulbo
        """
        # Gerar dados (usar resolução menor para performance)
        X, Y, Z, sigma = self.gerar_bulbo_boussinesq(q, B, L, grid_size=30)
        
        # Normalizar para porcentagem
        sigma_pct = sigma / q * 100
        
        # Criar isosuperfícies (níveis de tensão)
        fig = go.Figure()
        
        # Adicionar várias isosuperfícies
        levels = [10, 20, 30, 40, 50]
        colors = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']
        
        for level, color in zip(levels, colors):
            # Extrair superfície do nível
            vertices, faces = self._extract_isosurface(sigma_pct, level, X, Y, Z)
            
            if len(vertices) > 0:
                fig.add_trace(go.Mesh3d(
                    x=vertices[:, 0],
                    y=vertices[:, 1],
                    z=vertices[:, 2],
                    i=faces[:, 0],
                    j=faces[:, 1],
                    k=faces[:, 2],
                    opacity=0.3,
                    color=color,
                    name=f'{level}% q',
                    hoverinfo='name',
                    showlegend=True
                ))
        
        # Adicionar sapata como retângulo
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[-L/2, -L/2, L/2, L/2, -L/2, -L/2, L/2, L/2],
            z=[0, 0, 0, 0, -0.1, -0.1, -0.1, -0.1],
            i=[0, 0, 0, 4, 4, 6],
            j=[1, 2, 3, 5, 6, 7],
            k=[2, 3, 0, 6, 7, 4],
            color='red',
            opacity=0.8,
            name='Sapata'
        ))
        
        # Configurar layout
        fig.update_layout(
            title="Bulbo de Tensões 3D - Solução de Boussinesq",
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Profundidade Z (m)",
                aspectratio=dict(x=2, y=2, z=1),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                zaxis=dict(autorange='reversed')
            ),
            height=600
        )
        
        return fig
    
    def _extract_isosurface(self, values, level, X, Y, Z):
        """
        Extrai isosuperfície usando algoritmo marching cubes simplificado
        """
        # Implementação simplificada - em produção usar scikit-image
        try:
            from skimage import measure
            vertices, faces, _, _ = measure.marching_cubes(
                values, level, spacing=(
                    np.diff(X[0,0,:])[0],
                    np.diff(Y[0,:,0])[0],
                    np.diff(Z[:,0,0])[0]
                )
            )
            return vertices, faces
        except ImportError:
            # Fallback simples
            return np.array([]), np.array([])
    
    def calcular_profundidade_influencia(self, B, L, percentual=0.1):
        """
        Calcula profundidade de influência (onde Δσ/q = percentual)
        
        Args:
            B, L: Dimensões da sapata
            percentual: Percentual mínimo (ex: 0.1 = 10%)
            
        Returns:
            z_inf: Profundidade de influência (m)
        """
        # Usar método de Boussinesq simplificado
        z_values = np.linspace(0, 5*B, 1000)
        influences = []
        
        for z in z_values:
            if z == 0:
                influence = 1.0
            else:
                influence = self.boussinesq_rectangular_load(
                    1.0, B, L, 0, 0, z, method='newmark'
                )
            influences.append(influence)
            
            if influence < percentual:
                return z
        
        return 2 * B  # Fallback
    
    def relatorio_tecnico_bulbo(self, q, B, L):
        """
        Gera relatório técnico comparativo
        """
        # Calcular profundidades características
        z_10 = self.calcular_profundidade_influencia(B, L, 0.10)  # 10% q
        z_20 = self.calcular_profundidade_influencia(B, L, 0.20)  # 20% q
        
        # Comparar métodos no centro
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
        
        RECOMENDAÇÕES:
        1. Para ensino: Usar método 2:1 (mais intuitivo)
        2. Para projetos: Usar Boussinesq (mais preciso)
        3. Para solos estratificados: Considerar método 2:1 com correções
        """
        
        return relatorio

# Exemplo de uso
def exemplo_uso():
    """Demonstração do uso da classe"""
    bulbo = BulboTensoes()
    
    # Parâmetros exemplo
    q = 200  # kPa
    B = 1.5  # m
    L = 1.5  # m
    
    # Gerar gráfico comparativo
    fig_comparativo = bulbo.plot_comparativo_bulbos(q, B, L)
    fig_comparativo.show()
    
    # Gerar relatório
    relatorio = bulbo.relatorio_tecnico_bulbo(q, B, L)
    print(relatorio)
    
    return bulbo

if __name__ == "__main__":
    bulbo = exemplo_uso()