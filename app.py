"""
🏗️ SIMULADOR INTERATIVO DE SOLO E FUNDAÇÕES
Aplicação web completa para análise geotécnica
Versão 2.2.0 - Focado no Bulbo de Tensões Boussinesq
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
    from src.models import Solo, Fundacao
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
    st.info("""
    Verifique se todos os arquivos estão na pasta `src/`:
    - models.py
    - mohr_coulomb.py
    - bulbo_tensoes.py
    - foundation_calculations.py
    - export_system.py
    - nbr_validation.py
    """)
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
    if 'current_solo' not in st.session_state:
        st.session_state.current_solo = None
    if 'current_fundacao' not in st.session_state:
        st.session_state.current_fundacao = None

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
        
        # Criar objeto Solo atual
        try:
            solo_atual = Solo(
                nome="Solo Atual",
                peso_especifico=gamma,
                angulo_atrito=phi,
                coesao=c,
                coeficiente_poisson=0.3
            )
            st.session_state.current_solo = solo_atual
        except Exception as e:
            st.warning(f"Não foi possível criar objeto Solo: {e}")
        
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
        Versão 2.2.0 - Bulbo de Tensões Boussinesq  
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
        ✅ **Bulbo de tensões real** (Solução de Boussinesq)  
        ✅ **Banco de dados de solos**  
        ✅ **Arquitetura moderna** com dataclasses  
        
        ## 🎯 Destaques da Versão 2.2.0
        
        1. **Foco no Bulbo de Tensões Boussinesq** (Método 2:1 removido)
        2. **Correção de warnings do Streamlit**
        3. **Interface otimizada** para análise técnica
        4. **Performance melhorada** nos cálculos
        
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
        
        **Módulos Principais:**
        - ✅ Mohr-Coulomb
        - ✅ Fundações (Sapatas/Estacas)
        - ✅ Exportação de Dados
        - ✅ Validação NBR
        - ✅ Bulbo de Tensões (Boussinesq)
        - ✅ Banco de Dados de Solos
        
        **Atualizações Recentes:**
        1. ✅ Remoção do Método 2:1
        2. ✅ Correção de warnings do Streamlit
        3. ✅ Foco na solução de Boussinesq
        """)
        
        # Métricas rápidas
        st.metric("Versão", "2.2.0")
        st.metric("Última Atualização", datetime.now().strftime("%d/%m/%Y"))
        
        # Verificar objetos carregados
        if st.session_state.current_solo:
            st.success("✅ Objeto Solo carregado")
        else:
            st.warning("⚠️ Objeto Solo não carregado")
        
        # Início rápido
        with st.expander("⚡ Início Rápido"):
            if st.button("Ir para Bulbo de Tensões", width="stretch"):
                st.session_state.app_mode = "Sapatas"
                st.rerun()
            if st.button("Ir para Análise de Solo", width="stretch"):
                st.session_state.app_mode = "Análise de Solo"
                st.rerun()
    
    # Exemplos de aplicação
    st.divider()
    st.markdown("## 📚 Aplicações do Bulbo de Tensões")
    
    examples = st.columns(3)
    
    with examples[0]:
        st.markdown("""
        ### 🎓 Didática
        - Visualização da distribuição de tensões
        - Compreensão da profundidade de influência
        - Análise da interação solo-estrutura
        """)
    
    with examples[1]:
        st.markdown("""
        ### 🏢 Profissional
        - Dimensionamento de fundações
        - Análise de capacidade de carga
        - Estudo de interação entre fundações
        """)
    
    with examples[2]:
        st.markdown("""
        ### 📝 Acadêmica
        - Validação de resultados teóricos
        - Análise paramétrica
        - Estudos de pesquisa
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
            width="stretch"
        )
    
    with col1:
        # Usar Solo da sessão se disponível
        if st.session_state.current_solo:
            solo = st.session_state.current_solo
        else:
            # Fallback
            solo = Solo(
                nome="Solo Padrão",
                peso_especifico=st.session_state.soil_params['gamma'],
                angulo_atrito=st.session_state.soil_params['phi'],
                coesao=st.session_state.soil_params['c']
            )
        
        # Inicializar classe MohrCoulomb
        try:
            soil = MohrCoulomb(
                c=solo.coesao or st.session_state.soil_params['c'],
                phi=solo.angulo_atrito or st.session_state.soil_params['phi'],
                unit_weight=solo.peso_especifico
            )
        except Exception as e:
            st.error(f"Erro ao criar MohrCoulomb: {e}")
            return
        
        if analyze_button:
            # Criar gráfico do círculo de Mohr
            try:
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
                    'mobilization_percent': safety['mobilization_percent'],
                    'solo_utilizado': solo.__dict__
                })
                
                st.session_state.figures = [fig]
                
                st.plotly_chart(fig, width="stretch")
                
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
                    
            except Exception as e:
                st.error(f"Erro na análise: {e}")
        
        else:
            # Mostrar gráfico padrão
            try:
                fig, _ = soil.create_mohr_circle_plot(100, 200, 50, 0, True, True)
                st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.error(f"Erro ao criar gráfico padrão: {e}")
    
    # Abas adicionais
    tab1, tab2, tab3 = st.tabs(["📈 Transformação", "🔄 Caminho das Tensões", "📋 Relatório"])
    
    with tab1:
        st.markdown("### Transformação de Tensões")
        
        theta_deg = st.slider(
            "Ângulo do plano (θ) [°]",
            min_value=0.0,
            max_value=180.0,
            value=45.0,
            step=5.0,
            key="theta_transform"
        )
        
        try:
            transformed = soil.stress_transformation(sigma_x, sigma_z, tau_xz, theta_deg)
            
            col_t1, col_t2, col_t3 = st.columns(3)
            
            with col_t1:
                st.metric("σθ [kPa]", f"{transformed['sigma_theta']:.1f}")
            with col_t2:
                st.metric("τθ [kPa]", f"{transformed['tau_theta']:.1f}")
            with col_t3:
                st.metric("τmáx [kPa]", f"{transformed['tau_max_theta']:.1f}")
                
        except Exception as e:
            st.error(f"Erro na transformação: {e}")
    
    with tab2:
        st.markdown("### Caminho das Tensões (Stress Path)")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            delta_sigma_x = st.number_input("Δσx [kPa]", -200.0, 200.0, 100.0, 10.0, key="delta_sx")
            delta_sigma_z = st.number_input("Δσz [kPa]", -200.0, 200.0, 150.0, 10.0, key="delta_sz")
            delta_tau_xz = st.number_input("Δτxz [kPa]", -100.0, 100.0, 50.0, 5.0, key="delta_tau")
        
        with col_s2:
            steps = st.slider("Número de etapas", 2, 20, 10, key="steps_path")
            
            if st.button("Traçar Caminho", key="btn_path"):
                try:
                    fig_path = soil.stress_path_plot(
                        initial_stress=(sigma_x, sigma_z, tau_xz),
                        stress_increment=(delta_sigma_x, delta_sigma_z, delta_tau_xz),
                        steps=steps
                    )
                    st.plotly_chart(fig_path, width="stretch")
                except Exception as e:
                    st.error(f"Erro ao traçar caminho: {e}")
    
    with tab3:
        # Gerar relatório da análise
        if 'analysis_results' in st.session_state and st.session_state.analysis_results:
            try:
                params = {
                    'Coesão (c)': f"{solo.coesao or st.session_state.soil_params['c']} kPa",
                    'Ângulo (φ)': f"{solo.angulo_atrito or st.session_state.soil_params['phi']}°",
                    'Peso (γ)': f"{solo.peso_especifico} kN/m³",
                    'σx': f"{sigma_x} kPa",
                    'σz': f"{sigma_z} kPa",
                    'τxz': f"{tau_xz} kPa",
                    'Nome do Solo': solo.nome
                }
                
                if 'FS_simple' in st.session_state.analysis_results:
                    results = {
                        'σ₁': f"{st.session_state.analysis_results['sigma_1']:.1f} kPa",
                        'σ₃': f"{st.session_state.analysis_results['sigma_3']:.1f} kPa",
                        'Fator Segurança': f"{st.session_state.analysis_results['FS_simple']:.2f}",
                        'φ mobilizado': f"{st.session_state.analysis_results.get('phi_mobilized', 0):.1f}°",
                        'Mobilização': f"{st.session_state.analysis_results.get('mobilization_percent', 0):.1f}%"
                    }
                    
                    report = generate_report('soil', params, results)
                    
                    with st.expander("📄 Relatório Completo"):
                        st.text(report)
                    
                    # Opção de download
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=report,
                        file_name=f"relatorio_solo_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        width="content"
                    )
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")

def shallow_foundation_page():
    """Página de análise de sapatas - Focada no Bulbo de Tensões Boussinesq"""
    st.title("📐 Análise de Sapatas - Bulbo de Tensões Boussinesq")
    
    if not MODULES_LOADED:
        st.error("Módulo de fundações não carregado!")
        return
    
    col_config, col_viz = st.columns([1, 2])
    
    with col_config:
        st.markdown("### ⚙️ Configuração da Sapata")
        
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
        
        q_applied = st.number_input(
            "Pressão aplicada (q) [kPa]",
            min_value=50.0,
            max_value=5000.0,
            value=200.0,
            step=10.0,
            help="Pressão uniforme na base da sapata"
        )
        
        st.markdown("### 🎛️ Parâmetros do Cálculo")
        
        resolucao = st.slider(
            "Resolução da malha",
            min_value=20,
            max_value=80,
            value=40,
            step=5,
            help="Maior resolução = mais preciso, porém mais lento"
        )
        
        depth_ratio = st.slider(
            "Profundidade relativa (Z/B)",
            min_value=1.0,
            max_value=5.0,
            value=3.0,
            step=0.5,
            help="Razão entre profundidade máxima analisada e largura B"
        )
        
        metodo = st.selectbox(
            "Método de cálculo",
            ["newmark", "integration"],
            format_func=lambda x: "Newmark (rápido)" if x == "newmark" else "Integração (preciso)",
            help="Método para cálculo do fator de influência"
        )
        
        analyze_button = st.button(
            "🔍 Calcular Bulbo de Tensões",
            type="primary",
            width="stretch"
        )
    
    with col_viz:
        placeholder = st.empty()
        
        if analyze_button:
            try:
                # 1. Criar objetos de dados
                if st.session_state.current_solo:
                    solo = st.session_state.current_solo
                else:
                    solo = Solo(
                        nome="Solo Configurado",
                        peso_especifico=st.session_state.soil_params['gamma'],
                        coeficiente_poisson=0.3
                    )
                    st.session_state.current_solo = solo
                
                fundacao = Fundacao(largura=B, comprimento=L, carga=q_applied)
                st.session_state.current_fundacao = fundacao
                
                # 2. Instanciar calculador e gerar bulbo
                bulbo = BulboTensoes()
                
                with st.spinner("Calculando bulbo de tensões..."):
                    resultado = bulbo.gerar_bulbo_boussinesq_avancado(
                        fundacao=fundacao,
                        solo=solo,
                        depth_ratio=depth_ratio,
                        grid_size=resolucao,
                        method=metodo
                    )
                
                # 3. Extrair dados para visualização
                sigma_b = resultado.tensoes
                coords = resultado.coordenadas
                
                # Pegar slice central (plano Y=0)
                slice_index = sigma_b.shape[1] // 2
                center_slice = sigma_b[:, slice_index, :] / fundacao.carga * 100
                X_slice = coords[:, slice_index, :, 0]
                Z_slice = coords[:, slice_index, :, 2]
                
                # 4. Criar gráfico de contorno
                fig = go.Figure(data=go.Contour(
                    z=center_slice,
                    x=X_slice[0, :],
                    y=Z_slice[:, 0],
                    colorscale='Plasma',
                    contours=dict(start=0, end=100, size=10),
                    colorbar=dict(title="Δσ/q [%]", titleside="right"),
                    hovertemplate=(
                        "<b>Distância X</b>: %{x:.2f} m<br>"
                        "<b>Profundidade Z</b>: %{y:.2f} m<br>"
                        "<b>Tensão Δσ/q</b>: %{z:.1f} %<br>"
                        "<b>Tensão absoluta</b>: %{customdata:.1f} kPa"
                        "<extra></extra>"
                    ),
                    customdata=center_slice * q_applied / 100,
                    line_smoothing=0.85
                ))
                
                # 5. Adicionar contorno da sapata
                fig.add_shape(
                    type="rect",
                    x0=-B/2, y0=0,
                    x1=B/2, y1=-0.05 * depth_ratio * B,
                    line=dict(color="red", width=3),
                    fillcolor="rgba(255, 0, 0, 0.15)",
                    name="Sapata"
                )
                
                # 6. Configurar layout
                fig.update_layout(
                    title=f"Bulbo de Tensões - Solução de Boussinesq (q = {q_applied} kPa)",
                    xaxis_title="Distância do Centro [m]",
                    yaxis_title="Profundidade [m]",
                    yaxis=dict(
                        autorange='reversed',
                        scaleanchor="x",
                        scaleratio=1
                    ),
                    height=600,
                    showlegend=False
                )
                
                placeholder.plotly_chart(fig, width="stretch")
                
                # 7. Exibir métricas de influência
                st.markdown("### 📊 Profundidades de Influência")
                
                z_10 = bulbo.calcular_profundidade_influencia(B, L, 0.10)
                z_20 = bulbo.calcular_profundidade_influencia(B, L, 0.20)
                z_05 = bulbo.calcular_profundidade_influencia(B, L, 0.05)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Até 20% de q", f"{z_20:.2f} m")
                with col2:
                    st.metric("Até 10% de q", f"{z_10:.2f} m")
                with col3:
                    st.metric("Até 5% de q", f"{z_05:.2f} m")
                
                # 8. Relatório técnico
                with st.expander("📄 Relatório Técnico do Bulbo"):
                    relatorio = bulbo.relatorio_tecnico_bulbo(q_applied, B, L)
                    st.text(relatorio)
                    
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=relatorio,
                        file_name=f"bulbo_tensoes_B{B}_L{L}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        width="content"
                    )
                
                # 9. Armazenar resultados
                st.session_state.analysis_results.update({
                    'foundation_type': 'shallow',
                    'fundacao': fundacao.__dict__,
                    'solo': solo.__dict__,
                    'q_applied': q_applied,
                    'depth_ratio': depth_ratio,
                    'grid_size': resolucao,
                    'method': metodo,
                    'z_10': z_10,
                    'z_20': z_20,
                    'z_05': z_05
                })
                
            except Exception as e:
                placeholder.error(f"❌ Erro no cálculo do bulbo: {str(e)}")
                st.info("""
                **Possíveis causas:**
                1. Módulo `src.bulbo_tensoes` não encontrado
                2. Erro nos parâmetros de entrada
                3. Limite de memória para alta resolução
                
                **Sugestões:**
                - Reduza a resolução da malha
                - Verifique se o módulo está instalado
                """)
        else:
            placeholder.info("""
            ### 🎯 Bulbo de Tensões - Solução de Boussinesq
            
            **Configure os parâmetros e clique em 'Calcular Bulbo de Tensões'**
            
            Esta ferramenta calcula a distribuição de tensões verticais (Δσ) no solo
            sob uma fundação retangular com carga uniforme, utilizando a **solução
            teórica de Boussinesq**.
            
            **Parâmetros importantes:**
            - **B, L**: Dimensões da sapata
            - **q**: Pressão aplicada
            - **Resolução**: Controla a precisão do cálculo
            - **Profundidade relativa**: Até que profundidade analisar
            
            **Resultado:** Gráfico de contorno mostrando as isócuras de tensão
            em porcentagem da pressão aplicada.
            """)

def deep_foundation_page():
    """Página de análise de estacas"""
    st.title("📏 Análise de Estacas (Fundações Profundas)")
    
    if not MODULES_LOADED:
        st.error("Módulo de fundações não carregado!")
        return
    
    st.info("""
    **Funcionalidade em desenvolvimento.**
    Para análise completa de fundações, use a página de **Sapatas** que já está
    com o bulbo de tensões Boussinesq implementado.
    """)
    
    col_geom, col_soil = st.columns(2)
    
    with col_geom:
        st.markdown("### 📐 Geometria da Estaca")
        
        pile_diameter = st.number_input(
            "Diâmetro [m]",
            min_value=0.3,
            max_value=2.0,
            value=0.5,
            step=0.1,
            key="pile_diameter"
        )
        
        pile_length = st.number_input(
            "Comprimento [m]",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            key="pile_length"
        )
    
    with col_soil:
        st.markdown("### 🌱 Solo Atual")
        if st.session_state.current_solo:
            solo = st.session_state.current_solo
            st.success(f"✅ Solo: {solo.nome}")
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("γ", f"{solo.peso_especifico} kN/m³")
            with col_s2:
                if solo.coesao:
                    st.metric("c", f"{solo.coesao} kPa")
                else:
                    st.metric("c", "0 kPa")
            with col_s3:
                if solo.angulo_atrito:
                    st.metric("φ", f"{solo.angulo_atrito}°")
                else:
                    st.metric("φ", "N/A")
        else:
            st.warning("Configure um solo na página de Sapatas primeiro.")
    
    if st.button("🧪 Ir para Análise de Sapatas", type="primary", width="stretch"):
        st.session_state.app_mode = "Sapatas"
        st.rerun()

def export_page():
    """Página de exportação de resultados"""
    st.title("📤 Exportação de Resultados")
    
    if not MODULES_LOADED:
        st.error("Sistema de exportação não carregado!")
        return
    
    # Mostrar objetos atuais
    st.markdown("### 📊 Dados Atuais para Exportação")
    
    cols = st.columns(2)
    
    with cols[0]:
        if st.session_state.current_solo:
            st.success("✅ Solo disponível")
            with st.expander("Detalhes do Solo"):
                st.json(st.session_state.current_solo.__dict__)
        else:
            st.warning("⚠️ Nenhum Solo configurado")
    
    with cols[1]:
        if st.session_state.current_fundacao:
            st.success("✅ Fundação disponível")
            with st.expander("Detalhes da Fundação"):
                st.json(st.session_state.current_fundacao.__dict__)
        else:
            st.warning("⚠️ Nenhuma Fundação configurada")
    
    # Usar o módulo de exportação
    try:
        streamlit_export_ui()
    except Exception as e:
        st.error(f"Erro no sistema de exportação: {e}")

def nbr_validation_page():
    """Página de validação normativa"""
    st.title("📐 Validação Normativa - NBR 6122/6118")
    
    if not MODULES_LOADED:
        st.error("Módulo de validação NBR não carregado!")
        return
    
    # Usar o módulo de validação
    try:
        nbr_validation_ui()
    except Exception as e:
        st.error(f"Erro no módulo de validação: {e}")

def soil_database_page():
    """Página do banco de dados de solos"""
    st.title("📊 Banco de Dados de Solos")
    
    soil_data = {
        "Argila Mole": {
            "c": 5.0, "phi": 0.0, "gamma": 16.0, 
            "coeficiente_poisson": 0.45,
            "descricao": "Baixa resistência, alta compressibilidade"
        },
        "Argila Rija": {
            "c": 50.0, "phi": 0.0, "gamma": 19.0, 
            "coeficiente_poisson": 0.4,
            "descricao": "Resistência média, compressibilidade moderada"
        },
        "Silte": {
            "c": 0.0, "phi": 28.0, "gamma": 18.0, 
            "coeficiente_poisson": 0.35,
            "descricao": "Granular fino, comportamento intermediário"
        },
        "Areia Fina": {
            "c": 0.0, "phi": 30.0, "gamma": 17.0, 
            "coeficiente_poisson": 0.3,
            "descricao": "Granular, drenante, baixa coesão"
        },
        "Areia Média": {
            "c": 0.0, "phi": 32.0, "gamma": 18.0, 
            "coeficiente_poisson": 0.3,
            "descricao": "Resistência boa, compactação média"
        },
        "Areia Grossa": {
            "c": 0.0, "phi": 35.0, "gamma": 19.0, 
            "coeficiente_poisson": 0.25,
            "descricao": "Alta resistência, boa compactação"
        },
    }
    
    tab_view, tab_import = st.tabs(["👁️ Visualizar", "📥 Importar"])
    
    with tab_view:
        st.markdown("### Solos Típicos para Análise")
        
        df = pd.DataFrame.from_dict(soil_data, orient='index')
        df.index.name = "Tipo de Solo"
        df.reset_index(inplace=True)
        
        st.dataframe(
            df,
            column_config={
                "Tipo de Solo": st.column_config.TextColumn("Tipo de Solo"),
                "c": st.column_config.NumberColumn("Coesão (kPa)", format="%.1f"),
                "phi": st.column_config.NumberColumn("Ângulo φ (°)", format="%.1f"),
                "gamma": st.column_config.NumberColumn("Peso γ (kN/m³)", format="%.1f"),
                "coeficiente_poisson": st.column_config.NumberColumn("ν", format="%.2f"),
                "descricao": st.column_config.TextColumn("Descrição")
            },
            hide_index=True,
            width="stretch"
        )
        
        selected_soil = st.selectbox("Selecione um tipo de solo:", list(soil_data.keys()))
        
        if st.button("Carregar Solo Selecionado", type="primary", width="stretch"):
            try:
                soil = soil_data[selected_soil]
                solo = Solo(
                    nome=selected_soil,
                    peso_especifico=soil['gamma'],
                    angulo_atrito=soil['phi'],
                    coesao=soil['c'],
                    coeficiente_poisson=soil['coeficiente_poisson']
                )
                
                st.session_state.current_solo = solo
                st.session_state.soil_params.update({
                    'c': soil['c'],
                    'phi': soil['phi'],
                    'gamma': soil['gamma']
                })
                
                st.success(f"✅ Solo '{selected_soil}' carregado!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao carregar solo: {e}")
    
    with tab_import:
        st.markdown("### Importar Dados Personalizados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            c_custom = st.number_input("Coesão [kPa]", 0.0, 200.0, 10.0, 1.0, key="c_custom")
            phi_custom = st.number_input("Ângulo φ [°]", 0.0, 45.0, 30.0, 1.0, key="phi_custom")
            gamma_custom = st.number_input("Peso γ [kN/m³]", 10.0, 25.0, 18.0, 0.1, key="gamma_custom")
        
        with col2:
            nu_custom = st.number_input("ν (Poisson)", 0.0, 0.49, 0.3, 0.01, key="nu_custom")
            soil_name = st.text_input("Nome do solo", "Meu Solo", key="soil_name")
        
        if st.button("Criar Solo Personalizado", type="primary", width="stretch"):
            try:
                solo_custom = Solo(
                    nome=soil_name,
                    peso_especifico=gamma_custom,
                    angulo_atrito=phi_custom,
                    coesao=c_custom,
                    coeficiente_poisson=nu_custom
                )
                
                st.session_state.current_solo = solo_custom
                st.session_state.soil_params.update({
                    'c': c_custom,
                    'phi': phi_custom,
                    'gamma': gamma_custom
                })
                
                st.success(f"✅ Solo '{soil_name}' criado e carregado!")
                
            except ValueError as e:
                st.error(f"❌ Erro de validação: {e}")

def documentation_page():
    """Página de documentação do projeto"""
    st.title("📚 Documentação do Projeto")
    
    tab1, tab2, tab3 = st.tabs(["📖 Teoria", "💻 Uso", "🏗️ Código"])
    
    with tab1:
        st.markdown("""
        ## 📖 Teoria do Bulbo de Tensões
        
        ### Solução de Boussinesq
        
        A solução de **Joseph Boussinesq (1885)** fornece as tensões em um meio
        elástico, homogêneo, isotrópico e semi-infinito devido a uma carga pontual.
        
        Para carga uniformemente distribuída sobre área retangular, integra-se
        a solução pontual sobre toda a área carregada.
        
        ### Equação Básica
        
        ```math
        σ_z = \\frac{3Qz^3}{2πR^5}
        ```
        
        Onde:
        - **σ_z**: Tensão vertical no ponto
        - **Q**: Carga pontual
        - **z**: Profundidade do ponto
        - **R**: Distância radial da carga ao ponto
        
        ### Aplicações Práticas
        
        1. **Dimensionamento de fundações**
        2. **Análise de recalques**
        3. **Estudo de interação entre fundações**
        4. **Determinação da profundidade de influência**
        """)
    
    with tab2:
        st.markdown("""
        ## 💻 Guia de Uso
        
        ### 1. Configuração Inicial
        
        1. Acesse a página **"Sapatas"**
        2. Configure os parâmetros da sapata:
           - Largura (B) e Comprimento (L)
           - Pressão aplicada (q)
        
        3. Ajuste os parâmetros do cálculo:
           - Resolução da malha (20-80)
           - Profundidade relativa (Z/B)
           - Método (Newmark ou Integração)
        
        ### 2. Cálculo e Visualização
        
        1. Clique em **"Calcular Bulbo de Tensões"**
        2. Aguarde o processamento
        3. Visualize o gráfico de contorno
        4. Analise as profundidades de influência
        
        ### 3. Exportação
        
        1. Gere relatório técnico
        2. Baixe os resultados
        3. Use os dados em outros softwares
        """)
    
    with tab3:
        st.markdown("""
        ## 🏗️ Estrutura do Código
        
        ### Arquitetura Principal
        
        ```
        app.py
        ├── Configuração inicial
        ├── Barra lateral (create_sidebar)
        ├── Páginas do sistema
        └── Navegação principal
        ```
        
        ### Módulos Especializados
        
        - **`src/models.py`**: Dataclasses (Solo, Fundacao)
        - **`src/bulbo_tensoes.py`**: Cálculo do bulbo Boussinesq
        - **`src/mohr_coulomb.py`**: Análise de tensões
        - **`src/export_system.py`**: Sistema de exportação
        
        ### Tecnologias Utilizadas
        
        - **Streamlit**: Interface web
        - **Plotly**: Visualizações gráficas
        - **NumPy**: Cálculos numéricos
        - **Pandas**: Manipulação de dados
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
    🏗️ Simulador Solo-Fundações v2.2.0 | 
    Focado no Bulbo de Tensões Boussinesq | 
    {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)

if __name__ == "__main__":
    main()
