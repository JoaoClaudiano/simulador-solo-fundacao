"""
Implementação completa do critério de Mohr-Coulomb
com visualização avançada e análises de tensões
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import fsolve

class MohrCoulomb:
    """Classe para análise de tensões pelo critério de Mohr-Coulomb"""
    
    def __init__(self, c, phi, unit_weight=18):
        """
        Inicializa parâmetros do solo
        
        Args:
            c: Coesão (kPa)
            phi: Ângulo de atrito interno (graus)
            unit_weight: Peso específico (kN/m³)
        """
        self.c = c
        self.phi = phi
        self.phi_rad = np.radians(phi)
        self.unit_weight = unit_weight
        
    def shear_strength(self, sigma_n, sigma_n_eff=None, u=0):
        """
        Resistência ao cisalhamento τ = c + σ'·tan(φ)
        
        Args:
            sigma_n: Tensão normal total (kPa)
            sigma_n_eff: Tensão normal efetiva (kPa) - opcional
            u: Poropressão (kPa)
            
        Returns:
            tau_max: Resistência ao cisalhamento (kPa)
        """
        if sigma_n_eff is None:
            sigma_n_eff = sigma_n - u
            
        tau_max = self.c + sigma_n_eff * np.tan(self.phi_rad)
        return tau_max
    
    def principal_stresses(self, sigma_x, sigma_z, tau_xz):
        """
        Calcula tensões principais e orientação
        
        Args:
            sigma_x: Tensão na direção x (kPa)
            sigma_z: Tensão na direção z (kPa)
            tau_xz: Tensão cisalhante (kPa)
            
        Returns:
            dict: Tensões principais e ângulo
        """
        # Centro do círculo
        sigma_avg = (sigma_x + sigma_z) / 2
        
        # Raio do círculo
        R = np.sqrt(((sigma_x - sigma_z) / 2)**2 + tau_xz**2)
        
        # Tensões principais
        sigma_1 = sigma_avg + R
        sigma_3 = sigma_avg - R
        
        # Ângulo do plano principal
        if abs(sigma_x - sigma_z) > 1e-10:
            theta_p_rad = 0.5 * np.arctan2(2 * tau_xz, sigma_x - sigma_z)
        else:
            theta_p_rad = np.pi/4 if tau_xz > 0 else -np.pi/4
            
        theta_p_deg = np.degrees(theta_p_rad)
        
        return {
            'sigma_1': sigma_1,
            'sigma_3': sigma_3,
            'sigma_avg': sigma_avg,
            'radius': R,
            'theta_p_deg': theta_p_deg,
            'theta_p_rad': theta_p_rad
        }
    
    def stress_transformation(self, sigma_x, sigma_z, tau_xz, theta_deg):
        """
        Transformação de tensões para um plano inclinado
        
        Args:
            sigma_x, sigma_z, tau_xz: Estado de tensões inicial
            theta_deg: Ângulo do plano (graus)
            
        Returns:
            dict: Tensões no plano inclinado
        """
        theta_rad = np.radians(theta_deg)
        
        # Fórmulas de transformação
        sigma_theta = (sigma_x + sigma_z)/2 + \
                     (sigma_x - sigma_z)/2 * np.cos(2*theta_rad) + \
                     tau_xz * np.sin(2*theta_rad)
        
        tau_theta = -(sigma_x - sigma_z)/2 * np.sin(2*theta_rad) + \
                    tau_xz * np.cos(2*theta_rad)
        
        # Tensão efetiva (considerando poropressão zero por padrão)
        sigma_theta_eff = sigma_theta
        tau_max_theta = self.shear_strength(sigma_theta_eff)
        
        return {
            'sigma_theta': sigma_theta,
            'tau_theta': tau_theta,
            'tau_max_theta': tau_max_theta,
            'safety_factor': tau_max_theta / abs(tau_theta) if abs(tau_theta) > 0 else float('inf')
        }
    
    def failure_plane_angle(self):
        """
        Ângulo do plano de ruptura teórico
        
        Returns:
            theta_f_deg: Ângulo do plano de ruptura (graus)
        """
        theta_f_rad = np.pi/4 + self.phi_rad/2
        return np.degrees(theta_f_rad)
    
    def failure_envelope_points(self, sigma_max=500, points=50):
        """
        Gera pontos da envoltória de ruptura
        
        Args:
            sigma_max: Tensão normal máxima (kPa)
            points: Número de pontos
            
        Returns:
            sigma_points, tau_points
        """
        sigma_points = np.linspace(0, sigma_max, points)
        tau_points = self.c + sigma_points * np.tan(self.phi_rad)
        
        return sigma_points, tau_points
    
    def create_mohr_circle_plot(self, sigma_x, sigma_z, tau_xz, u=0, 
                               include_failure=True, include_stress_points=True):
        """
        Cria gráfico completo do círculo de Mohr
        
        Returns:
            plotly.graph_objects.Figure
        """
        # Cálculo das tensões principais
        principals = self.principal_stresses(sigma_x, sigma_z, tau_xz)
        sigma_1 = principals['sigma_1']
        sigma_3 = principals['sigma_3']
        sigma_avg = principals['sigma_avg']
        R = principals['radius']
        
        # Pontos do círculo
        theta = np.linspace(0, 2*np.pi, 100)
        sigma_circle = sigma_avg + R * np.cos(theta)
        tau_circle = R * np.sin(theta)
        
        # Envoltória de ruptura
        sigma_env, tau_env = self.failure_envelope_points(sigma_max=max(sigma_1, 300))
        
        # Criar figura
        fig = go.Figure()
        
        # 1. Círculo de Mohr
        fig.add_trace(go.Scatter(
            x=sigma_circle, y=tau_circle,
            mode='lines',
            name='Círculo de Mohr',
            line=dict(color='blue', width=2),
            fill='toself',
            fillcolor='rgba(0, 100, 255, 0.1)'
        ))
        
        # 2. Envoltória de ruptura
        if include_failure:
            fig.add_trace(go.Scatter(
                x=sigma_env, y=tau_env,
                mode='lines',
                name='Envoltória de Ruptura',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='τ = %{y:.1f} kPa<br>σ = %{x:.1f} kPa'
            ))
            
            # Área de segurança
            sigma_safe = np.linspace(0, max(sigma_env), 100)
            tau_safe = self.c + sigma_safe * np.tan(self.phi_rad)
            fig.add_trace(go.Scatter(
                x=sigma_safe, y=tau_safe,
                mode='lines',
                line=dict(width=0),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 0, 0.1)',
                name='Zona Segura',
                showlegend=False
            ))
        
        # 3. Tensões principais
        if include_stress_points:
            fig.add_trace(go.Scatter(
                x=[sigma_1, sigma_3], y=[0, 0],
                mode='markers+text',
                marker=dict(size=12, color='green'),
                text=['σ₁', 'σ₃'],
                textposition='top center',
                name='Tensões Principais',
                hovertemplate='σ = %{x:.1f} kPa'
            ))
        
        # 4. Estado de tensões inicial
        fig.add_trace(go.Scatter(
            x=[sigma_x, sigma_z], y=[tau_xz, -tau_xz],
            mode='markers+text',
            marker=dict(size=10, color='orange', symbol='diamond'),
            text=['Ponto A', 'Ponto B'],
            textposition='bottom center',
            name='Estado de Tensões',
            hovertemplate='σ = %{x:.1f} kPa<br>τ = %{y:.1f} kPa'
        ))
        
        # 5. Linhas de conexão (opcional)
        fig.add_trace(go.Scatter(
            x=[sigma_x, sigma_z], y=[tau_xz, -tau_xz],
            mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            showlegend=False
        ))
        
        # Configurações do gráfico
        fig.update_layout(
            title='Círculo de Mohr - Análise de Tensões',
            xaxis_title='Tensão Normal σ (kPa)',
            yaxis_title='Tensão Cisalhante τ (kPa)',
            hovermode='closest',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            shapes=[
                # Linha vertical no centro
                dict(
                    type="line",
                    x0=sigma_avg, y0=min(tau_circle)-50,
                    x1=sigma_avg, y1=max(tau_circle)+50,
                    line=dict(color="gray", width=1, dash="dot")
                ),
                # Linha horizontal no centro
                dict(
                    type="line",
                    x0=sigma_avg-100, y0=0,
                    x1=sigma_avg+100, y1=0,
                    line=dict(color="gray", width=1, dash="dot")
                )
            ],
            annotations=[
                dict(
                    x=sigma_avg, y=max(tau_circle)+20,
                    text=f"Centro: ({sigma_avg:.1f}, 0)",
                    showarrow=False,
                    font=dict(size=10)
                ),
                dict(
                    x=sigma_avg+R, y=0,
                    text=f"Raio: {R:.1f} kPa",
                    showarrow=True,
                    arrowhead=2,
                    ax=50,
                    ay=0
                )
            ]
        )
        
        return fig, principals
    
    def stress_path_plot(self, initial_stress, stress_increment, steps=10):
        """
        Traça o caminho das tensões durante carregamento
        
        Args:
            initial_stress: (sigma_x, sigma_z, tau_xz)
            stress_increment: (delta_sigma_x, delta_sigma_z, delta_tau_xz)
            steps: Número de incrementos
            
        Returns:
            plotly.graph_objects.Figure
        """
        fig = go.Figure()
        
        # Calcular caminho das tensões
        sigma_x_vals = []
        sigma_z_vals = []
        tau_xz_vals = []
        
        for i in range(steps + 1):
            t = i / steps
            sigma_x = initial_stress[0] + stress_increment[0] * t
            sigma_z = initial_stress[1] + stress_increment[1] * t
            tau_xz = initial_stress[2] + stress_increment[2] * t
            
            sigma_x_vals.append(sigma_x)
            sigma_z_vals.append(sigma_z)
            tau_xz_vals.append(tau_xz)
            
            # Calcular círculo em cada passo
            principals = self.principal_stresses(sigma_x, sigma_z, tau_xz)
            
            # Adicionar círculo translúcido
            theta = np.linspace(0, 2*np.pi, 50)
            sigma_circle = principals['sigma_avg'] + principals['radius'] * np.cos(theta)
            tau_circle = principals['radius'] * np.sin(theta)
            
            fig.add_trace(go.Scatter(
                x=sigma_circle, y=tau_circle,
                mode='lines',
                line=dict(width=1, color=f'rgba(0, 0, 255, {0.1 + 0.9*t})'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Adicionar caminho do centro
        center_x = [(sx + sz)/2 for sx, sz in zip(sigma_x_vals, sigma_z_vals)]
        center_y = [0] * len(center_x)
        
        fig.add_trace(go.Scatter(
            x=center_x, y=center_y,
            mode='markers+lines',
            marker=dict(size=8, color='red'),
            line=dict(width=2, color='red'),
            name='Caminho do Centro'
        ))
        
        # Envoltória final
        sigma_env, tau_env = self.failure_envelope_points()
        fig.add_trace(go.Scatter(
            x=sigma_env, y=tau_env,
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='Envoltória de Ruptura'
        ))
        
        fig.update_layout(
            title='Caminho das Tensões (Stress Path)',
            xaxis_title='Tensão Normal σ (kPa)',
            yaxis_title='Tensão Cisalhante τ (kPa)',
            showlegend=True
        )
        
        return fig
    
    def calculate_safety_margin(self, sigma_x, sigma_z, tau_xz, u=0):
        """
        Calcula margem de segurança até a ruptura
        
        Returns:
            dict: Vários índices de segurança
        """
        principals = self.principal_stresses(sigma_x, sigma_z, tau_xz)
        
        # Distância até a envoltória (método do ponto mais próximo)
        sigma_eff = (principals['sigma_1'] + principals['sigma_3']) / 2 - u
        
        # Tensão cisalhante máxima no círculo
        tau_max_circle = principals['radius']
        
        # Resistência no mesmo nível de tensão normal
        tau_strength = self.shear_strength(sigma_eff, u=u)
        
        # Fator de segurança
        FS_simple = tau_strength / tau_max_circle if tau_max_circle > 0 else float('inf')
        
        # Ângulo de mobilização
        phi_mob = np.degrees(np.arctan(tau_max_circle / (sigma_eff + self.c/np.tan(self.phi_rad))))
        
        # Porcentagem de mobilização
        mobilization_ratio = min(100, phi_mob / self.phi * 100)
        
        return {
            'FS_simple': FS_simple,
            'phi_mobilized_deg': phi_mob,
            'mobilization_percent': mobilization_ratio,
            'tau_max_circle': tau_max_circle,
            'tau_strength': tau_strength,
            'distance_to_failure': tau_strength - tau_max_circle
        }

def example_usage():
    """Exemplo de uso da classe MohrCoulomb"""
    # Criar solo
    solo = MohrCoulomb(c=10, phi=30)
    
    # Estado de tensões
    sigma_x = 100
    sigma_z = 50
    tau_xz = 30
    
    # Criar gráfico
    fig, principals = solo.create_mohr_circle_plot(sigma_x, sigma_z, tau_xz)
    
    # Calcular segurança
    safety = solo.calculate_safety_margin(sigma_x, sigma_z, tau_xz)
    
    print("=== ANÁLISE MOHR-COULOMB ===")
    print(f"Coesão: {solo.c} kPa")
    print(f"Ângulo de atrito: {solo.phi}°")
    print(f"σ₁: {principals['sigma_1']:.1f} kPa")
    print(f"σ₃: {principals['sigma_3']:.1f} kPa")
    print(f"Fator de segurança: {safety['FS_simple']:.2f}")
    print(f"Ângulo mobilizado: {safety['phi_mobilized_deg']:.1f}°")
    print(f"Mobilização: {safety['mobilization_percent']:.1f}%")
    
    return fig

if __name__ == "__main__":
    # Testar o módulo
    fig = example_usage()
    fig.show()