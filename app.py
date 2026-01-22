"""
🏗️ SIMULADOR INTERATIVO DE SOLO E FUNDAÇÕES
Aplicação web completa para análise geotécnica
Integração dos módulos: Mohr-Coulomb, Exportação e Validação NBR
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
import os

# Configurar caminho para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ====================== CONFIGURAÇÃO INICIAL ======================
st.set_page_config(
    page_title="Simulador Solo-Fundações",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== IMPORTAÇÕES DOS MÓDULOS ======================
try:
    from src.mohr_coulomb import MohrCoulomb
    from src.export_system import ExportSystem, streamlit_export_ui
    from src.nbr_validation import (
        NBR6122_Validator, NBR6118_ConcreteValidator,
        SoilClass, FoundationType,
        nbr_validation_ui
    )
    from src.foundation_calculations import (
        bearing_capacity_terzaghi,
        elastic_settlement,
        pile_ultimate_capacity,
        pile_settlement,
        safety_factor,
        generate_report
    )
    from src.soil_calculations import shear_strength
    from src.bulbo_tensoes import BulboTensoes
    
    MODULES_LOADED = True
except ImportError as e:
    st.error(f"❌ Erro ao carregar módulos: {e}")
    st.info("Verifique se todos os arquivos estão na pasta `src/`")
    MODULES_LOADED = False

# ====================== FUNÇÕES AUXILIARES ======================
def initialize_session_state():
    """Inicializa variáveis de sessão"""
    if 'soil_params' not in st.session_state:
        st.session_state.soil_params = {
            'c': 10.0,
            'phi': 30.0,
            'gamma': 18.0,
            'unit_weight': 18.0
        }
    if 'foundation_params' not in st.session_state:
        st.session_state.foundation_params = {
            'type': 'shallow',
            'B': 1.5,
            'L': 1.5,
            'D_f': 1.0,
            'shape': 'square'
        }
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'figures' not in st.session_state:
        st.session_state.figures = []

def create_sidebar():
    """Cria barra lateral com controles principais"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/engineering.png", width=100)
        st.title("⚙️ Controles")
        
        st.markdown("### 📐 Parâmetros Globais")
        
        # Seleção de módulo
        app_mode = st.selectbox(
            "Módulo Principal",
            ["Início", "Análise de Solo", "Sapatas", "Estacas", 
             "Exportação", "Validação NBR", "Documentação", "Banco de Solos"]
        )
        
        st.divider()
        
        # Parâmetros básicos do solo (sempre visíveis)
        st.markdown("### 🌱 Parâmetros do Solo")
        
        c = st.slider(
            "Coesão (c) [kPa]",
            min_value=0.0,
            max_value=200.0,
            value=st.session_state.soil_params['c'],
            step=0.5,
            help="Resistência ao cisalhamento sem tensão normal"
        )
        
        phi = st.slider(
            "Ângulo de Atrito (φ) [°]",
            min_value=0.0,
            max_value=45.0,
            value=st.session_state.soil_params['phi'],
            step=0.5,
            help="Inclinação da envoltória de ruptura"
        )
        
        gamma = st.slider(
            "Peso Específico (γ) [kN/m³]",
            min_value=10.0,
            max_value=25.0,
            value=st.session_state.soil_params['gamma'],
            step=0.1,
            help="Peso do solo por unidade de volume"
        )
        
        # Atualizar sessão
        st.session_state.soil_params.update({
            'c': c,
            'phi': phi,
            'gamma': gamma,
            'unit_weight': gamma
        })
        
        st.divider()
        
        # Informações do projeto
        with st.expander("📋 Informações do Projeto"):
            project_name = st.text_input("Nome do Projeto", "Projeto_TCC")
            st.session_state.project_name = project_name
            
            analyst = st.text_input("Responsável", "Estudante Engenharia")
            st.session_state.analyst = analyst
            
            date = st.date_input("Data da Análise")
            st.session_state.analysis_date = date
        
        st.divider()
        
        # Rodapé
        st.caption("""
        **Simulador Solo-Fundações**  
        Desenvolvido para TCC em Engenharia Civil  
        Python + Streamlit + Plotly
        """)
        
        return app_mode

def home_page():
    """Página inicial do simulador"""
    st.title("🏗️ Simulador Interativo de Solo e Fundações")
    st.markdown("### Laboratório Virtual para Análise Geotécnica")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 📋 Sobre o Projeto
        
        Este simulador é uma ferramenta desenvolvida para **TCC em Engenharia Civil** que integra:
        
        ✅ **Análise avançada de tensões** (Critério de Mohr-Coulomb)  
        ✅ **Dimensionamento de fundações** (Sapatas e Estacas)  
        ✅ **Validação normativa** (NBR 6122 e NBR 6118)  
        ✅ **Sistema de exportação** (CSV, Excel, PDF, HTML)  
        ✅ **Visualizações interativas** (Plotly 3D, gráficos dinâmicos)  
        ✅ **Bulbo de tensões real** (Boussinesq)  
        ✅ **Banco de dados de solos**  
        
        ## 🎯 Objetivos
        
        1. **Didático**: Facilitar o aprendizado de mecânica dos solos
        2. **Prático**: Realizar análises preliminares de fundações
        3. **Técnico**: Validar projetos conforme normas brasileiras
        4. **Acadêmico**: Demonstrar integração engenharia + programação
        
        ## 🚀 Como Usar
        
        1. **Configure os parâmetros** na barra lateral
        2. **Selecione o módulo** desejado no menu
        3. **Ajuste os controles** específicos de cada análise
        4. **Visualize resultados** em gráficos e tabelas
        5. **Exporte** relatórios técnicos completos
        """)
    
    with col2:
        # Cartão de status
        st.info("""
        ### 📊 Status do Sistema
        
        **Módulos Carregados:**
        - ✅ Mohr-Coulomb
        - ✅ Fundações (Sapatas/Estacas)
        - ✅ Exportação de Dados
        - ✅ Validação NBR
        - ✅ Bulbo de Tensões (Boussinesq)
        - ✅ Banco de Dados de Solos
        
        **Próximos Passos:**
        1. Testar cada módulo
        2. Validar com casos reais
        3. Preparar relatório TCC
        """)
        
        # Métricas rápidas
        st.metric("Versão", "2.0.0")
        st.metric("Última Atualização", datetime.now().strftime("%d/%m/%Y"))
        
        # Início rápido
        with st.expander("⚡ Início Rápido"):
            if st.button("Ir para Análise de Solo"):
                st.session_state.app_mode = "Análise de Solo"
                st.rerun()
            if st.button("Ir para Sapatas"):
                st.session_state.app_mode = "Sapatas"
                st.rerun()
            if st.button("Ir para Banco de Solos"):
                st.session_state.app_mode = "Banco de Solos"
                st.rerun()
    
    # Exemplos de aplicação
    st.divider()
    st.markdown("## 📚 Exemplos de Aplicação")
    
    examples = st.columns(3)
    
    with examples[0]:
        st.markdown("""
        ### 🎓 Didático
        - Compreender o círculo de Mohr
        - Visualizar envoltória de ruptura
        - Analisar transformação de tensões
        - Comparar bulbos de tensões
        """)
    
    with examples[1]:
        st.markdown("""
        ### 🏢 Profissional
        - Dimensionamento preliminar
        - Análise de capacidade de carga
        - Verificação de recalques
        - Validação com normas
        """)
    
    with examples[2]:
        st.markdown("""
        ### 📝 Acadêmico
        - Validação com normas
        - Geração de relatórios
        - Análise paramétrica
        - Banco de dados de solos
        """)

def soil_analysis_page():
    """Página de análise de solo com Mohr-Coulomb"""
    st.title("🌱 Análise de Solo - Critério de Mohr-Coulomb")
    
    if not MODULES_LOADED:
        st.error("Módulo Mohr-Coulomb não carregado!")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ⚙️ Estado de Tensões")
        
        sigma_x = st.number_input(
            "σx [kPa] (Tensão horizontal)",
            min_value=0.0,
            max_value=1000.0,
            value=100.0,
            step=10.0
        )
        
        sigma_z = st.number_input(
            "σz [kPa] (Tensão vertical)",
            min_value=0.0,
            max_value=1000.0,
            value=200.0,
            step=10.0
        )
        
        tau_xz = st.number_input(
            "τxz [kPa] (Tensão cisalhante)",
            min_value=-500.0,
            max_value=500.0,
            value=50.0,
            step=5.0
        )
        
        u = st.number_input(
            "Poropressão (u) [kPa]",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=10.0,
            help="Pressão da água nos poros"
        )
        
        include_failure = st.checkbox("Mostrar envoltória de ruptura", True)
        include_stress_points = st.checkbox("Mostrar pontos de tensão", True)
        
        analyze_button = st.button(
            "🔬 Analisar Tensões",
            type="primary",
            use_container_width=True
        )
    
    with col1:
        # Inicializar classe MohrCoulomb
        soil = MohrCoulomb(
            c=st.session_state.soil_params['c'],
            phi=st.session_state.soil_params['phi'],
            unit_weight=st.session_state.soil_params['gamma']
        )
        
        if analyze_button:
            # Criar gráfico do círculo de Mohr
            fig, principals = soil.create_mohr_circle_plot(
                sigma_x, sigma_z, tau_xz, u,
                include_failure, include_stress_points
            )
            
            # Calcular segurança
            safety = soil.calculate_safety_margin(sigma_x, sigma_z, tau_xz, u)
            
            # Armazenar para exportação
            st.session_state.analysis_results.update({
                'sigma_x': sigma_x,
                'sigma_z': sigma_z,
                'tau_xz': tau_xz,
                'u': u,
                'sigma_1': principals['sigma_1'],
                'sigma_3': principals['sigma_3'],
                'FS_simple': safety['FS_simple'],
                'phi_mobilized': safety['phi_mobilized_deg'],
                'mobilization_percent': safety['mobilization_percent']
            })
            
            st.session_state.figures = [fig]
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir resultados
            st.markdown("### 📊 Resultados da Análise")
            
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric("σ₁ (kPa)", f"{principals['sigma_1']:.1f}")
                st.metric("σ₃ (kPa)", f"{principals['sigma_3']:.1f}")
            
            with res_col2:
                st.metric("Centro (kPa)", f"{principals['sigma_avg']:.1f}")
                st.metric("Raio (kPa)", f"{principals['radius']:.1f}")
            
            with res_col3:
                # Indicador de segurança colorido
                fs = safety['FS_simple']
                if fs >= 2.0:
                    color = "green"
                    status = "SEGURO"
                elif fs >= 1.5:
                    color = "orange"
                    status = "ATENÇÃO"
                else:
                    color = "red"
                    status = "CRÍTICO"
                
                st.metric("Fator de Segurança", f"{fs:.2f}")
                st.markdown(f"<h4 style='color:{color};'>Status: {status}</h4>", 
                          unsafe_allow_html=True)
        
        else:
            # Mostrar gráfico padrão
            fig, _ = soil.create_mohr_circle_plot(100, 200, 50, 0, True, True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Abas adicionais
    tab1, tab2, tab3 = st.tabs(["📈 Transformação", "🔄 Caminho das Tensões", "📋 Relatório"])
    
    with tab1:
        st.markdown("### Transformação de Tensões")
        
        theta_deg = st.slider(
            "Ângulo do plano (θ) [°]",
            min_value=0.0,
            max_value=180.0,
            value=45.0,
            step=5.0
        )
        
        transformed = soil.stress_transformation(sigma_x, sigma_z, tau_xz, theta_deg)
        
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            st.metric("σθ [kPa]", f"{transformed['sigma_theta']:.1f}")
        with col_t2:
            st.metric("τθ [kPa]", f"{transformed['tau_theta']:.1f}")
        with col_t3:
            st.metric("τmáx [kPa]", f"{transformed['tau_max_theta']:.1f}")
    
    with tab2:
        st.markdown("### Caminho das Tensões (Stress Path)")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            delta_sigma_x = st.number_input("Δσx [kPa]", -200.0, 200.0, 100.0, 10.0)
            delta_sigma_z = st.number_input("Δσz [kPa]", -200.0, 200.0, 150.0, 10.0)
            delta_tau_xz = st.number_input("Δτxz [kPa]", -100.0, 100.0, 50.0, 5.0)
        
        with col_s2:
            steps = st.slider("Número de etapas", 2, 20, 10)
            
            if st.button("Traçar Caminho"):
                fig_path = soil.stress_path_plot(
                    initial_stress=(sigma_x, sigma_z, tau_xz),
                    stress_increment=(delta_sigma_x, delta_sigma_z, delta_tau_xz),
                    steps=steps
                )
                st.plotly_chart(fig_path, use_container_width=True)
    
    with tab3:
        # Gerar relatório da análise
        if 'analysis_results' in st.session_state and st.session_state.analysis_results:
            params = {
                'Coesão (c)': f"{st.session_state.soil_params['c']} kPa",
                'Ângulo (φ)': f"{st.session_state.soil_params['phi']}°",
                'Peso (γ)': f"{st.session_state.soil_params['gamma']} kN/m³",
                'σx': f"{sigma_x} kPa",
                'σz': f"{sigma_z} kPa",
                'τxz': f"{tau_xz} kPa"
            }
            
            if 'FS_simple' in st.session_state.analysis_results:
                results = {
                    'σ₁': f"{st.session_state.analysis_results['sigma_1']:.1f} kPa",
                    'σ₃': f"{st.session_state.analysis_results['sigma_3']:.1f} kPa",
                    'Fator Segurança': f"{st.session_state.analysis_results['FS_simple']:.2f}",
                    'φ mobilizado': f"{st.session_state.analysis_results['phi_mobilized']:.1f}°",
                    'Mobilização': f"{st.session_state.analysis_results['mobilization_percent']:.1f}%"
                }
                
                report = generate_report('soil', params, results)
                
                with st.expander("📄 Relatório Completo"):
                    st.text(report)
                
                # Opção de download
                st.download_button(
                    label="📥 Baixar Relatório",
                    data=report,
                    file_name=f"relatorio_solo_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )

def shallow_foundation_page():
    """Página de análise de sapatas"""
    st.title("📐 Análise de Sapatas (Fundações Rasas)")
    
    if not MODULES_LOADED:
        st.error("Módulo de fundações não carregado!")
        return
    
    col_config, col_viz = st.columns([1, 2])
    
    with col_config:
        st.markdown("### ⚙️ Configuração da Sapata")
        
        foundation_type = st.selectbox(
            "Tipo de sapata",
            ["strip", "square", "circular"],
            index=1,
            help="Contínua, quadrada ou circular"
        )
        
        B = st.number_input(
            "Largura (B) [m]",
            min_value=0.5,
            max_value=10.0,
            value=1.5,
            step=0.1,
            help="Largura da base da sapata"
        )
        
        L = st.number_input(
            "Comprimento (L) [m]",
            min_value=0.5,
            max_value=10.0,
            value=1.5,
            step=0.1,
            help="Comprimento da sapata"
        )
        
        D_f = st.number_input(
            "Profundidade (Df) [m]",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Profundidade de embutimento"
        )
        
        st.markdown("### 📊 Carregamento")
        
        q_applied = st.number_input(
            "Pressão aplicada [kPa]",
            min_value=50.0,
            max_value=5000.0,
            value=200.0,
            step=10.0
        )
        
        st.markdown("### 🏗️ Propriedades do Concreto")
        
        fck = st.select_slider(
            "fck do concreto [MPa]",
            options=[20, 25, 30, 35, 40, 50],
            value=25
        )
        
        analyze_button = st.button(
            "🔍 Analisar Sapata",
            type="primary",
            use_container_width=True
        )
    
    with col_viz:
        # Espaço para visualizações
        placeholder = st.empty()
        
        if analyze_button:
            with st.spinner("Calculando capacidade de carga..."):
                # Obter parâmetros do solo
                c = st.session_state.soil_params['c']
                phi = st.session_state.soil_params['phi']
                gamma = st.session_state.soil_params['gamma']
                
                # Calcular capacidade de carga
                q_ult, (Nc, Nq, Nγ) = bearing_capacity_terzaghi(
                    c, phi, gamma, B, L, D_f, foundation_type
                )
                
                # Calcular recalque (simplificado)
                E_s = 50000  # kPa (valor padrão)
                mu = 0.3
                settlement = elastic_settlement(
                    q_applied, B, E_s, mu,
                    'rectangular' if foundation_type != 'circular' else 'circular',
                    L/B if L != 0 else 1.0
                )
                
                # Calcular fator de segurança
                FS, is_safe = safety_factor(q_ult, q_applied, 3.0)
                
                # Armazenar resultados
                st.session_state.analysis_results.update({
                    'foundation_type': 'shallow',
                    'shape': foundation_type,
                    'B': B,
                    'L': L,
                    'D_f': D_f,
                    'c': c,
                    'phi': phi,
                    'gamma': gamma,
                    'q_ult': q_ult,
                    'q_applied': q_applied,
                    'settlement': settlement,
                    'FS': FS,
                    'is_safe': is_safe,
                    'Nc': Nc,
                    'Nq': Nq,
                    'Nγ': Nγ
                })
                
                # Exibir resultados
                placeholder.markdown("### 📊 Resultados Calculados")
                
                # Métricas
                col_res1, col_res2, col_res3 = st.columns(3)
                
                with col_res1:
                    st.metric("Capacidade Última", f"{q_ult:.0f} kPa")
                    st.metric("Fator Nq", f"{Nq:.2f}")
                
                with col_res2:
                    st.metric("Fator de Segurança", f"{FS:.2f}")
                    st.metric("Fator Nγ", f"{Nγ:.2f}")
                    
                    # Indicador de segurança
                    if FS >= 3.0:
                        st.success("✅ SAPATA SEGURA")
                    elif FS >= 2.0:
                        st.warning("⚠️  ATENÇÃO - Fator de segurança baixo")
                    else:
                        st.error("❌ CAPACIDADE INSUFICIENTE")
                
                with col_res3:
                    st.metric("Recalque Estimado", f"{settlement*1000:.1f} mm")
                    st.metric("Fator Nc", f"{Nc:.2f}")
                    
                    # Verificação de recalque
                    if settlement*1000 <= 25:  # 25 mm limite comum
                        st.info("📏 Recalque dentro do limite")
                    else:
                        st.warning("📏 Recalque excessivo - verificar")
        else:
            # Exibir imagem ilustrativa inicial
            placeholder.info("""
            ### Configure a sapata e clique em "Analisar Sapata"
            
            **Parâmetros a serem definidos:**
            1. **Tipo de sapata**: Forma da base
            2. **Dimensões**: Largura, comprimento, profundidade
            3. **Carregamento**: Pressão aplicada
            4. **Concreto**: Resistência característica
            
            **Resultados obtidos:**
            • Capacidade de carga última
            • Fator de segurança
            • Recalque estimado
            • Bulbo de tensões
            • Validação conforme NBR 6122
            """)
    
    # Abas para bulbos de tensões
    st.divider()
    st.markdown("### 📈 Bulbos de Tensões")
    
    tab_bulbo1, tab_bulbo2, tab_bulbo3 = st.tabs(["Método 2:1", "Método Boussinesq", "Comparativo"])
    
    with tab_bulbo1:
        if analyze_button:
            st.markdown("#### Método 2:1 Simplificado")
            # Gerar bulbo 2:1 usando a nova classe
            bulbo = BulboTensoes()
            X_21, Z_21, sigma_21 = bulbo.gerar_bulbo_21(B, L)
            
            fig_21 = go.Figure(data=
                go.Contour(
                    z=sigma_21 * 100,
                    x=X_21[0, :],
                    y=Z_21[:, 0],
                    colorscale='Viridis',
                    contours=dict(start=0, end=100, size=10),
                    colorbar=dict(title="Δσ/q [%]"),
                    hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
                )
            )
            
            fig_21.update_layout(
                title="Bulbo de Tensões - Método 2:1 Simplificado",
                xaxis_title="Distância do centro [m]",
                yaxis_title="Profundidade [m]",
                yaxis=dict(autorange='reversed'),
                height=500
            )
            
            # Adicionar contorno da sapata
            fig_21.add_shape(
                type="rect",
                x0=-B/2, y0=0,
                x1=B/2, y1=-0.1,
                line=dict(color="red", width=2),
                fillcolor="rgba(255,0,0,0.1)"
            )
            
            st.plotly_chart(fig_21, use_container_width=True)
            
            st.info("**Método 2:1 Simplificado:** Aproximação prática com propagação 2V:1H (26.6°).")
    
    with tab_bulbo2:
        if analyze_button:
            st.markdown("#### Método de Boussinesq (Real)")
            bulbo = BulboTensoes()
            
            # Configurações para Boussinesq
            col_method, col_res = st.columns(2)
            with col_method:
                metodo = st.selectbox(
                    "Método de cálculo",
                    ["newmark", "integration"],
                    format_func=lambda x: "Newmark (rápido)" if x == "newmark" else "Integração (preciso)",
                    key="metodo_boussinesq"
                )
                
                resolucao = st.slider("Resolução da malha", 20, 100, 50, 10, key="res_boussinesq")
            
            with st.spinner("Calculando bulbo de Boussinesq..."):
                # Gerar bulbo Boussinesq
                X_b, Y_b, Z_b, sigma_b = bulbo.gerar_bulbo_boussinesq(
                    q_applied, B, L, grid_size=resolucao
                )
                
                # Pegar slice central (y=0)
                center_slice = sigma_b[:, sigma_b.shape[1]//2, :] / q_applied * 100
                X_b_slice = X_b[:, 0, :]
                Z_b_slice = Z_b[:, 0, :]
                
                fig_bouss = go.Figure(data=
                    go.Contour(
                        z=center_slice,
                        x=X_b_slice[0, :],
                        y=Z_b_slice[:, 0],
                        colorscale='Plasma',
                        contours=dict(start=0, end=100, size=10),
                        colorbar=dict(title="Δσ/q [%]"),
                        hovertemplate="X: %{x:.2f}m<br>Z: %{y:.2f}m<br>Δσ/q: %{z:.1f}%<extra></extra>"
                    )
                )
                
                fig_bouss.update_layout(
                    title="Bulbo de Tensões - Método de Boussinesq",
                    xaxis_title="Distância do centro [m]",
                    yaxis_title="Profundidade [m]",
                    yaxis=dict(autorange='reversed'),
                    height=500
                )
                
                # Adicionar contorno da sapata
                fig_bouss.add_shape(
                    type="rect",
                    x0=-B/2, y0=0,
                    x1=B/2, y1=-0.1,
                    line=dict(color="red", width=2),
                    fillcolor="rgba(255,0,0,0.1)"
                )
                
                st.plotly_chart(fig_bouss, use_container_width=True)
                
                # Calcular profundidade de influência
                z_10 = bulbo.calcular_profundidade_influencia(B, L, 0.10)
                z_20 = bulbo.calcular_profundidade_influencia(B, L, 0.20)
                
                st.info(f"""
                **Profundidades de influência:**
                - Até 20% de q: **{z_20:.2f} m** ({z_20/B:.1f}×B)
                - Até 10% de q: **{z_10:.2f} m** ({z_10/B:.1f}×B)
                """)
    
    with tab_bulbo3:
        if analyze_button:
            st.markdown("#### Comparativo: Método 2:1 vs Boussinesq")
            
            bulbo = BulboTensoes()
            fig_comparativo = bulbo.plot_comparativo_bulbos(q_applied, B, L)
            st.plotly_chart(fig_comparativo, use_container_width=True)
            
            # Relatório técnico
            with st.expander("📊 Relatório Técnico Comparativo"):
                relatorio = bulbo.relatorio_tecnico_bulbo(q_applied, B, L)
                st.text(relatorio)
                
                st.download_button(
                    label="📥 Baixar Relatório",
                    data=relatorio,
                    file_name=f"relatorio_bulbo_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
    
    # Validação NBR
    st.divider()
    st.markdown("### 📋 Validação conforme NBR 6122")
    
    if analyze_button and 'analysis_results' in st.session_state:
        # Criar validador
        validator = NBR6122_Validator(
            soil_class=SoilClass.AREIA_MEDIA,  # Pode ser ajustado
            water_table_depth=2.0
        )
        
        # Validar capacidade
        validation = validator.validate_bearing_capacity(q_ult, q_applied)
        
        col_val1, col_val2 = st.columns(2)
        
        with col_val1:
            if validation['is_valid']:
                st.success(f"✅ {validation['status']}")
            else:
                st.error(f"❌ {validation['status']}")
            
            st.metric("FS Calculado", f"{validation['FS_calculated']:.2f}")
            st.metric("FS Mínimo NBR", f"{validation['FS_min_required']:.2f}")
        
        with col_val2:
            # Validar dimensões
            dim_validation = validator.validate_foundation_dimensions(
                FoundationType.SAPATA_ISOLADA, B, L, 0.5  # Altura padrão
            )
            
            if dim_validation['is_valid']:
                st.success(f"✅ Dimensões OK")
            else:
                st.warning(f"⚠️  Verificar dimensões")
                for violation in dim_validation['violations']:
                    st.write(f"- {violation}")

def deep_foundation_page():
    """Página de análise de estacas"""
    st.title("📏 Análise de Estacas (Fundações Profundas)")
    
    if not MODULES_LOADED:
        st.error("Módulo de fundações não carregado!")
        return
    
    tab_config, tab_results = st.tabs(["⚙️ Configuração", "📊 Resultados"])
    
    with tab_config:
        col_geom, col_soil = st.columns(2)
        
        with col_geom:
            st.markdown("### 📐 Geometria da Estaca")
            
            pile_diameter = st.number_input(
                "Diâmetro [m]",
                min_value=0.3,
                max_value=2.0,
                value=0.5,
                step=0.1
            )
            
            pile_length = st.number_input(
                "Comprimento [m]",
                min_value=5.0,
                max_value=50.0,
                value=15.0,
                step=1.0
            )
            
            pile_type = st.selectbox(
                "Tipo de estaca",
                ["driven", "bored"],
                format_func=lambda x: "Cravada" if x == "driven" else "Escavada"
            )
            
            load_applied = st.number_input(
                "Carga aplicada [kN]",
                min_value=100,
                max_value=10000,
                value=1500,
                step=100
            )
        
        with col_soil:
            st.markdown("### 🌱 Perfil do Solo")
            st.info("Configure as camadas do solo (máximo 3 camadas)")
            
            layers = []
            
            for i in range(3):
                with st.expander(f"Camada {i+1}", expanded=(i == 0)):
                    depth_top = st.number_input(
                        f"Topo camada {i+1} [m]",
                        0.0, 20.0, float(i * 5), 1.0,
                        key=f"top_{i}"
                    )
                    
                    depth_bottom = st.number_input(
                        f"Base camada {i+1} [m]",
                        0.0, 30.0, float((i + 1) * 5), 1.0,
                        key=f"bottom_{i}"
                    )
                    
                    c_layer = st.number_input(
                        f"Coesão c{i+1} [kPa]",
                        0.0, 200.0, [5.0, 10.0, 15.0][i], 1.0,
                        key=f"c_{i}"
                    )
                    
                    phi_layer = st.number_input(
                        f"Ângulo φ{i+1} [°]",
                        0.0, 45.0, [28.0, 30.0, 32.0][i], 1.0,
                        key=f"phi_{i}"
                    )
                    
                    gamma_layer = st.number_input(
                        f"Peso γ{i+1} [kN/m³]",
                        15.0, 22.0, [18.0, 19.0, 20.0][i], 0.1,
                        key=f"gamma_{i}"
                    )
                    
                    layers.append({
                        'depth_top': depth_top,
                        'depth_bottom': depth_bottom,
                        'c': c_layer,
                        'phi': phi_layer,
                        'gamma': gamma_layer
                    })
        
        analyze_pile = st.button(
            "🔍 Analisar Estaca",
            type="primary",
            use_container_width=True
        )
    
    with tab_results:
        if analyze_pile:
            with st.spinner("Calculando capacidade da estaca..."):
                # Calcular capacidade
                total_capacity, shaft_capacity, tip_capacity = pile_ultimate_capacity(
                    layers, pile_diameter, pile_length, pile_type
                )
                
                # Calcular recalque
                settlement, breakdown = pile_settlement(
                    load_applied, shaft_capacity, tip_capacity,
                    pile_diameter, pile_length, 50000
                )
                
                # Calcular fator de segurança
                FS, is_safe = safety_factor(total_capacity, load_applied, 2.0)
                
                # Armazenar resultados
                st.session_state.analysis_results.update({
                    'foundation_type': 'deep',
                    'pile_type': pile_type,
                    'diameter': pile_diameter,
                    'length': pile_length,
                    'total_capacity': total_capacity,
                    'shaft_capacity': shaft_capacity,
                    'tip_capacity': tip_capacity,
                    'load_applied': load_applied,
                    'settlement': settlement,
                    'FS': FS,
                    'is_safe': is_safe
                })
                
                # Exibir resultados
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    st.metric("Capacidade Total", f"{total_capacity:.0f} kN")
                    st.metric("Atrito Lateral", f"{shaft_capacity:.0f} kN")
                    st.metric("Pontência de Ponta", f"{tip_capacity:.0f} kN")
                
                with col_res2:
                    st.metric("Fator de Segurança", f"{FS:.2f}")
                    st.metric("Recalque Estimado", f"{settlement*1000:.1f} mm")
                    
                    if is_safe:
                        st.success("✅ ESTACA SEGURA")
                    else:
                        st.error("❌ CAPACIDADE INSUFICIENTE")
                
                # Gráfico de distribuição
                st.markdown("### 📊 Distribuição de Capacidade")
                
                fig_pile = go.Figure(data=[
                    go.Bar(
                        name='Atrito Lateral',
                        x=['Atrito Lateral', 'Resistência de Ponta'],
                        y=[shaft_capacity, tip_capacity],
                        marker_color=['#FFA726', '#66BB6A']
                    )
                ])
                
                fig_pile.update_layout(
                    title="Distribuição da Capacidade da Estaca",
                    yaxis_title="Capacidade [kN]",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig_pile, use_container_width=True)
                
                # Perfil geotécnico
                st.markdown("### 📈 Perfil Geotécnico")
                
                fig_profile = go.Figure()
                
                colors = ['#8B4513', '#D2691E', '#A0522D']
                for i, layer in enumerate(layers):
                    fig_profile.add_trace(go.Scatter(
                        x=[0, 1, 1, 0],
                        y=[-layer['depth_top'], -layer['depth_top'], 
                           -layer['depth_bottom'], -layer['depth_bottom']],
                        fill='toself',
                        fillcolor=colors[i % len(colors)],
                        opacity=0.6,
                        line=dict(width=0),
                        name=f"Camada {i+1}",
                        hoverinfo='text',
                        text=f"c={layer['c']} kPa, φ={layer['phi']}°, γ={layer['gamma']} kN/m³"
                    ))
                
                # Adicionar estaca
                fig_profile.add_trace(go.Scatter(
                    x=[0.4, 0.6, 0.6, 0.4],
                    y=[0, 0, -pile_length, -pile_length],
                    fill='toself',
                    fillcolor='gray',
                    opacity=0.8,
                    line=dict(color='black', width=2),
                    name="Estaca",
                    hoverinfo='text',
                    text=f"Diâmetro: {pile_diameter}m, Tipo: {pile_type}"
                ))
                
                fig_profile.update_layout(
                    title="Perfil Geotécnico com Estaca",
                    xaxis=dict(showticklabels=False, range=[0, 1]),
                    yaxis=dict(title="Profundidade [m]", autorange='reversed'),
                    showlegend=True,
                    height=500
                )
                
                st.plotly_chart(fig_profile, use_container_width=True)
        else:
            st.info("Configure a estaca e clique em 'Analisar Estaca' para ver os resultados.")

def export_page():
    """Página de exportação de resultados"""
    st.title("📤 Exportação de Resultados")
    
    if not MODULES_LOADED:
        st.error("Sistema de exportação não carregado!")
        return
    
    # Usar a UI do módulo de exportação
    streamlit_export_ui()

def nbr_validation_page():
    """Página de validação normativa"""
    st.title("📐 Validação Normativa - NBR 6122/6118")
    
    if not MODULES_LOADED:
        st.error("Módulo de validação NBR não carregado!")
        return
    
    # Usar a UI do módulo de validação
    nbr_validation_ui()

def soil_database_page():
    """Página do banco de dados de solos"""
    st.title("📊 Banco de Dados de Solos")
    
    # Dados de solos típicos
    soil_data = {
        "Argila Mole": {"c": 5.0, "phi": 0.0, "gamma": 16.0, "descricao": "Baixa resistência, alta compressibilidade"},
        "Argila Rija": {"c": 50.0, "phi": 0.0, "gamma": 19.0, "descricao": "Resistência média, compressibilidade moderada"},
        "Silte": {"c": 0.0, "phi": 28.0, "gamma": 18.0, "descricao": "Granular fino, comportamento intermediário"},
        "Areia Fina": {"c": 0.0, "phi": 30.0, "gamma": 17.0, "descricao": "Granular, drenante, baixa coesão"},
        "Areia Média": {"c": 0.0, "phi": 32.0, "gamma": 18.0, "descricao": "Resistência boa, compactação média"},
        "Areia Grossa": {"c": 0.0, "phi": 35.0, "gamma": 19.0, "descricao": "Alta resistência, boa compactação"},
        "Pedregulho": {"c": 0.0, "phi": 40.0, "gamma": 20.0, "descricao": "Alta resistência, excelente capacidade de carga"},
    }
    
    tab_view, tab_import = st.tabs(["👁️ Visualizar", "📥 Importar"])
    
    with tab_view:
        st.markdown("### Solos Típicos para Análise")
        
        # Criar DataFrame
        df = pd.DataFrame.from_dict(soil_data, orient='index')
        df.index.name = "Tipo de Solo"
        df.reset_index(inplace=True)
        
        # Exibir tabela
        st.dataframe(
            df,
            column_config={
                "Tipo de Solo": st.column_config.TextColumn("Tipo de Solo", width="medium"),
                "c": st.column_config.NumberColumn("Coesão (kPa)", format="%.1f"),
                "phi": st.column_config.NumberColumn("Ângulo φ (°)", format="%.1f"),
                "gamma": st.column_config.NumberColumn("Peso γ (kN/m³)", format="%.1f"),
                "descricao": st.column_config.TextColumn("Descrição", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Seleção para carregar dados
        st.markdown("### 🚀 Carregar para Análise")
        selected_soil = st.selectbox("Selecione um tipo de solo:", list(soil_data.keys()))
        
        if st.button("Carregar Parâmetros", type="primary"):
            soil = soil_data[selected_soil]
            st.session_state.soil_params.update({
                'c': soil['c'],
                'phi': soil['phi'],
                'gamma': soil['gamma']
            })
            
            st.success(f"✅ Parâmetros de {selected_soil} carregados!")
            st.rerun()
    
    with tab_import:
        st.markdown("### Importar Dados Personalizados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            c_custom = st.number_input("Coesão personalizada [kPa]", 0.0, 200.0, 10.0, 1.0)
            phi_custom = st.number_input("Ângulo personalizado [°]", 0.0, 45.0, 30.0, 1.0)
            gamma_custom = st.number_input("Peso personalizado [kN/m³]", 10.0, 25.0, 18.0, 0.1)
        
        with col2:
            soil_name = st.text_input("Nome do solo personalizado", "Meu Solo")
            description = st.text_area("Descrição", "Solo com parâmetros personalizados")
        
        if st.button("Salvar Solo Personalizado"):
            soil_data[soil_name] = {
                "c": c_custom,
                "phi": phi_custom,
                "gamma": gamma_custom,
                "descricao": description
            }
            
            # Atualizar parâmetros atuais
            st.session_state.soil_params.update({
                'c': c_custom,
                'phi': phi_custom,
                'gamma': gamma_custom
            })
            
            st.success(f"✅ Solo '{soil_name}' salvo e parâmetros carregados!")
            
            # Mostrar dados atualizados
            st.dataframe(pd.DataFrame.from_dict(soil_data, orient='index'))

def documentation_page():
    """Página de documentação do projeto"""
    st.title("📚 Documentação do Projeto")
    
    tab_docs, tab_code, tab_about = st.tabs(["📖 Documentação", "💻 Código", "👨‍🎓 Sobre"])
    
    with tab_docs:
        st.markdown("""
        ## 📖 Documentação Técnica
        
        ### 1. Arquitetura do Sistema
        
        ```
        simulador_interativo_solo_fundacoes/
        ├── app.py                          # Aplicação principal
        ├── requirements.txt                # Dependências
        ├── src/                           # Módulos Python
        │   ├── mohr_coulomb.py            # Análise de tensões
        │   ├── foundation_calculations.py # Cálculos de fundações
        │   ├── soil_calculations.py       # Propriedades do solo
        │   ├── export_system.py           # Sistema de exportação
        │   ├── nbr_validation.py          # Validação normativa
        │   └── bulbo_tensoes.py           # Bulbo de tensões (Boussinesq)
        ├── tests/                         # Testes unitários
        ├── examples/                      # Exemplos de uso
        └── docs/                          # Documentação
        ```
        
        ### 2. Teoria Implementada
        
        #### 2.1 Critério de Mohr-Coulomb
        ```math
        τ = c + σ'·tan(φ)
        ```
        Onde:
        - τ = resistência ao cisalhamento
        - c = coesão
        - σ' = tensão normal efetiva
        - φ = ângulo de atrito interno
        
        #### 2.2 Capacidade de Carga - Terzaghi
        ```math
        q_ult = c·N_c·s_c + q·N_q·s_q + 0.5·γ·B·N_γ·s_γ
        ```
        
        #### 2.3 Estacas - Método Estático
        ```math
        Q_ult = Q_ponta + Q_lateral
        Q_lateral = Σ (π·D·ΔL·f_s)
        Q_ponta = A_ponta·q_p
        ```
        
        #### 2.4 Bulbo de Tensões - Boussinesq
        ```math
        σ_z = \\frac{3Qz^3}{2πR^5} \\quad \\text{(carga pontual)}
        ```
        
        ### 3. Validação Normativa
        
        #### 3.1 NBR 6122:2019 - Fundações
        - Fatores de segurança mínimos
        - Recalques admissíveis
        - Dimensões mínimas
        
        #### 3.2 NBR 6118:2014 - Concreto
        - Resistências características
        - Cobrimentos mínimos
        - Armaduras mínimas
        
        ### 4. Referências Bibliográficas
        
        1. **NBR 6122:2019** - Projeto e execução de fundações
        2. **NBR 6118:2014** - Projeto de estruturas de concreto
        3. **Das, B.M.** - Principles of Geotechnical Engineering
        4. **Velloso, D.A.** - Fundações: critérios de projeto
        5. **Cintra, J.C.A.** - Fundações em estacas
        6. **Boussinesq, J.** - Application des potentiels à l'étude de l'équilibre et du mouvement des solides élastiques
        """)
    
    with tab_code:
        st.markdown("""
        ## 💻 Guia de Desenvolvimento
        
        ### 1. Estrutura do Código
        
        #### 1.1 Módulo Principal (`app.py`)
        ```python
        # Estrutura básica
        app.py
        ├── Configuração
        ├── Inicialização
        ├── Rotas/Abas
        └── Interface
        ```
        
        #### 1.2 Módulos Especializados
        ```python
        # src/mohr_coulomb.py
        class MohrCoulomb:
            • shear_strength()
            • principal_stresses()
            • stress_transformation()
            • create_mohr_circle_plot()
        
        # src/foundation_calculations.py
        • bearing_capacity_terzaghi()
        • pile_ultimate_capacity()
        • elastic_settlement()
        
        # src/bulbo_tensoes.py
        class BulboTensoes:
            • boussinesq_point_load()
            • gerar_bulbo_boussinesq()
            • plot_comparativo_bulbos()
        ```
        
        ### 2. Padrões de Codificação
        
        #### 2.1 Nomenclatura
        ```python
        # Variáveis: snake_case
        cohesion = 10.0
        friction_angle = 30.0
        
        # Funções: snake_case
        def calculate_bearing_capacity():
            pass
        
        # Classes: PascalCase
        class MohrCoulomb:
            pass
        
        # Constantes: UPPER_CASE
        MIN_SAFETY_FACTOR = 2.0
        ```
        
        #### 2.2 Documentação
        ```python
        def calculate_something(param1, param2):
            '''
            Descrição da função
            
            Args:
                param1 (type): Descrição
                param2 (type): Descrição
            
            Returns:
                type: Descrição
            
            Raises:
                ExceptionType: Quando ocorre
            
            Examples:
                >>> calculate_something(10, 20)
                30
            '''
            return param1 + param2
        ```
        
        ### 3. Testes Unitários
        
        ```python
        # tests/test_foundations.py
        import pytest
        from src import foundation_calculations as fc
        
        def test_bearing_capacity():
            # Arrange
            c = 10
            phi = 30
            
            # Act
            result = fc.bearing_capacity_terzaghi(...)
            
            # Assert
            assert result > 0
            assert isinstance(result, tuple)
        ```
        
        ### 4. Deployment
        
        #### 4.1 Local
        ```bash
        pip install -r requirements.txt
        streamlit run app.py
        ```
        
        #### 4.2 Streamlit Cloud
        1. Push para GitHub
        2. Acessar share.streamlit.io
        3. Conectar repositório
        4. Configurar e deploy
        
        ### 5. Extensões Futuras
        
        1. **Análise 3D** com MEF
        2. **Banco de dados** de solos
        3. **API REST** para integração
        4. **App mobile** com React Native
        """)
    
    with tab_about:
        st.markdown("""
        ## 👨‍🎓 Sobre o Projeto
        
        ### Informações do TCC
        
        **Título:** Simulador Interativo para Análise Geotécnica de Fundações
        
        **Autor:** [Seu Nome]
        
        **Orientador:** [Nome do Orientador]
        
        **Instituição:** [Nome da Universidade]
        
        **Curso:** Engenharia Civil
        
        **Ano:** 2024
        
        ### Objetivos Específicos
        
        1. Desenvolver uma ferramenta computacional para análise de tensões no solo
        2. Implementar métodos de cálculo para fundações rasas e profundas
        3. Validar resultados conforme normas técnicas brasileiras
        4. Criar interface amigável para estudantes e profissionais
        5. Documentar todo o processo de desenvolvimento
        
        ### Contribuições Acadêmicas
        
        #### Para a Engenharia Civil
        - Ferramenta didática para mecânica dos solos
        - Sistema de validação automática de projetos
        - Biblioteca de cálculos geotécnicos em Python
        
        #### Para a Computação
        - Padrão de desenvolvimento para apps de engenharia
        - Integração Python + Streamlit para web apps técnicos
        - Sistema modular e extensível
        
        ### Agradecimentos
        
        - Orientador pela orientação técnica
        - Colegas de turma pelo feedback
        - Comunidade open-source pelas bibliotecas
        - StackOverflow pela ajuda em problemas específicos
        
        ### Licença
        
        Este projeto é disponibilizado sob a licença MIT:
        
        ```
        MIT License
        
        Copyright (c) 2024 [Seu Nome]
        
        Permissão é concedida, gratuitamente, a qualquer pessoa...
        ```
        
        ### Contato
        
        **Email:** seu.email@universidade.edu.br
        
        **GitHub:** github.com/seuusuario
        
        **LinkedIn:** linkedin.com/in/seuusuario
        
        ### Citação
        
        Se usar este projeto em sua pesquisa, cite como:
        
        ```
        [SEU SOBRENOME], [Seu Nome]. Simulador Interativo para 
        Análise Geotécnica de Fundações. TCC em Engenharia Civil. 
        [Universidade], 2024.
        ```
        """)

# ====================== APLICAÇÃO PRINCIPAL ======================
def main():
    """Função principal da aplicação"""
    
    # Inicializar estado da sessão
    initialize_session_state()
    
    # Criar barra lateral e obter modo selecionado
    app_mode = create_sidebar()
    
    # Navegação entre páginas
    if app_mode == "Início":
        home_page()
    
    elif app_mode == "Análise de Solo":
        soil_analysis_page()
    
    elif app_mode == "Sapatas":
        shallow_foundation_page()
    
    elif app_mode == "Estacas":
        deep_foundation_page()
    
    elif app_mode == "Exportação":
        export_page()
    
    elif app_mode == "Validação NBR":
        nbr_validation_page()
    
    elif app_mode == "Banco de Solos":
        soil_database_page()
    
    elif app_mode == "Documentação":
        documentation_page()
    
    # Footer
    st.divider()
    st.caption(f"""
    🏗️ Simulador Solo-Fundações v2.0.0 | 
    Desenvolvido para TCC em Engenharia Civil | 
    {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)

if __name__ == "__main__":
    main()