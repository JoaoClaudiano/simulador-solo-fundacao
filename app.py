"""
🏗️ SIMULADOR INTERATIVO DE SOLO E FUNDAÇÕES
Aplicação web completa para análise geotécnica
Versão 2.4.0 - Boussinesq + Terzaghi Integrados (Corrigido)
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
    from src.bulbo_tensoes import BulboTensoes
    from src.terzaghi import FoundationDesign as FoundationDesigner, TerzaghiCapacity
    
    MODULES_LOADED = True
except ImportError as e:
    st.error(f"❌ Erro ao carregar módulos: {e}")
    st.info("""
    Verifique se todos os arquivos estão na pasta `src/`:
    - models.py
    - mohr_coulomb.py
    - bulbo_tensoes.py (VERIFIQUE SE TEM O MÉTODO plot_bulbo_2d_com_isobaras)
    - terzaghi.py
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
            'unit_weight': 18.0,
            'E': 30000.0
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
    if 'terzaghi_results' not in st.session_state:
        st.session_state.terzaghi_results = None
    if 'project_name' not in st.session_state:
        st.session_state.project_name = "Projeto_TCC"
    if 'analyst' not in st.session_state:
        st.session_state.analyst = "Estudante Engenharia"
    if 'analysis_date' not in st.session_state:
        st.session_state.analysis_date = datetime.now().date()
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'water_table' not in st.session_state:
        st.session_state.water_table = 5.0

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
        
        # Módulo de Elasticidade para recalques
        E = st.number_input(
            "Módulo Elasticidade (E) [kPa]",
            min_value=1000.0,
            max_value=1000000.0,
            value=st.session_state.soil_params.get('E', 30000.0),
            step=1000.0,
            help="Para cálculo de recalques"
        )
        
        # Coeficiente de Poisson
        mu = st.number_input(
            "Coeficiente de Poisson (ν)",
            min_value=0.1,
            max_value=0.49,
            value=0.3,
            step=0.01,
            help="Razão entre deformações"
        )
        
        # Atualizar sessão
        st.session_state.soil_params.update({
            'c': c,
            'phi': phi,
            'gamma': gamma,
            'unit_weight': gamma,
            'E': E,
            'mu': mu
        })
        
        # Criar objeto Solo atual
        try:
            solo_atual = Solo(
                nome="Solo Atual",
                peso_especifico=gamma,
                angulo_atrito=phi,
                coesao=c,
                coeficiente_poisson=mu,
                modulo_elasticidade=E
            )
            st.session_state.current_solo = solo_atual
        except Exception as e:
            st.warning(f"Não foi possível criar objeto Solo: {e}")
        
        st.divider()
        
        # Informações do projeto
        with st.expander("📋 Informações do Projeto"):
            project_name = st.text_input("Nome do Projeto", st.session_state.project_name)
            st.session_state.project_name = project_name
            
            analyst = st.text_input("Responsável", st.session_state.analyst)
            st.session_state.analyst = analyst
            
            date = st.date_input("Data da Análise", st.session_state.analysis_date)
            st.session_state.analysis_date = date
        
        st.divider()
        
        # Opções avançadas
        with st.expander("⚙️ Opções Avançadas"):
            debug_mode = st.checkbox("Modo Debug", st.session_state.debug_mode)
            st.session_state.debug_mode = debug_mode
            
            water_table = st.number_input(
                "Nível d'água [m]",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.water_table,
                step=0.5,
                help="Profundidade do lençol freático"
            )
            st.session_state.water_table = water_table
        
        # Rodapé
        st.caption("""
        **Simulador Solo-Fundações**  
        Versão 2.4.0 - Boussinesq + Terzaghi (Corrigido)  
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
        ✅ **Distribuição de tensões** (Solução de Boussinesq)  
        ✅ **Capacidade de carga** (Teoria de Terzaghi)  
        ✅ **Cálculo de recalques** (Solução elástica)  
        ✅ **Validação normativa** (NBR 6122 e NBR 6118)  
        ✅ **Sistema de exportação** (CSV, Excel, PDF, HTML)  
        ✅ **Banco de dados de solos**  
        ✅ **Arquitetura moderna** com dataclasses  
        
        ## 🎯 Destaques da Versão 2.4.0
        
        1. **Isóbaras visíveis** no bulbo de tensões
        2. **Exportação em PDF/HTML** para todos os relatórios
        3. **Correção completa do método de Terzaghi**
        4. **Interface otimizada** com melhor visualização
        5. **Performance melhorada** nos cálculos
        
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
        - ✅ Boussinesq (Bulbo de Tensões)
        - ✅ Terzaghi (Capacidade de Carga)
        - ✅ Exportação de Dados
        - ✅ Validação NBR
        - ✅ Banco de Dados de Solos
        
        **Análises Disponíveis:**
        1. Distribuição de tensões (Δσ)
        2. Capacidade última (q_ult)
        3. Fator de segurança (FS)
        4. Recalques (δ)
        5. Recomendações de projeto
        
        **Integração Completa:**
        - Boussinesq → Terzaghi → Projeto
        """)
        
        # Métricas rápidas
        st.metric("Versão", "2.4.0")
        st.metric("Última Atualização", datetime.now().strftime("%d/%m/%Y"))
        
        # Verificar objetos carregados
        if st.session_state.current_solo:
            st.success("✅ Objeto Solo carregado")
        else:
            st.warning("⚠️ Objeto Solo não carregado")
        
        # Início rápido
        with st.expander("⚡ Início Rápido"):
            if st.button("Ir para Análise Completa", width="stretch"):
                st.session_state.app_mode = "Sapatas"
                st.rerun()
            if st.button("Ir para Análise de Solo", width="stretch"):
                st.session_state.app_mode = "Análise de Solo"
                st.rerun()
    
    # Exemplos de aplicação
    st.divider()
    st.markdown("## 📚 Aplicações do Simulador")
    
    examples = st.columns(3)
    
    with examples[0]:
        st.markdown("""
        ### 🎓 Didática
        - Visualização do bulbo de tensões
        - Compreensão da teoria de Terzaghi
        - Análise da interação solo-estrutura
        """)
    
    with examples[1]:
        st.markdown("""
        ### 🏢 Profissional
        - Dimensionamento de fundações
        - Análise de capacidade de carga
        - Verificação de segurança
        - Cálculo de recalques
        """)
    
    with examples[2]:
        st.markdown("""
        ### 📝 Acadêmica
        - Validação de resultados teóricos
        - Análise paramétrica
        - Estudos de pesquisa
        - Trabalhos de conclusão
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

def shallow_foundation_page():
    """Página de análise de sapatas - Boussinesq + Terzaghi Integrados (CORRIGIDO)"""
    st.title("📐 Análise de Sapatas - Boussinesq + Terzaghi")
    
    if not MODULES_LOADED:
        st.error("Módulos necessários não carregados!")
        return
    
    # Abas principais
    tab1, tab2 = st.tabs(["🏗️ Distribuição de Tensões (Boussinesq)", "🔒 Capacidade de Carga (Terzaghi)"])
    
    with tab1:
        col_config, col_viz = st.columns([1, 2])
        
        with col_config:
            st.markdown("### ⚙️ Configuração da Sapata")
            
            B = st.number_input(
                "Largura (B) [m]",
                min_value=0.5,
                max_value=10.0,
                value=1.5,
                step=0.1,
                help="Largura da base da sapata",
                key="bulbo_B"
            )
            
            L = st.number_input(
                "Comprimento (L) [m]",
                min_value=0.5,
                max_value=10.0,
                value=1.5,
                step=0.1,
                help="Comprimento da sapata",
                key="bulbo_L"
            )
            
            q_applied = st.number_input(
                "Pressão aplicada (q) [kPa]",
                min_value=50.0,
                max_value=5000.0,
                value=200.0,
                step=10.0,
                help="Pressão uniforme na base da sapata",
                key="bulbo_q"
            )
            
            st.markdown("### 🎛️ Parâmetros do Cálculo")
            
            resolucao = st.slider(
                "Resolução da malha",
                min_value=20,
                max_value=80,
                value=40,
                step=5,
                help="Maior resolução = mais preciso, porém mais lento",
                key="bulbo_res"
            )
            
            depth_ratio = st.slider(
                "Profundidade relativa (Z/B)",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
                help="Razão entre profundidade máxima analisada e largura B",
                key="bulbo_depth"
            )
            
            metodo = st.selectbox(
                "Método de cálculo",
                ["newmark", "integration"],
                format_func=lambda x: "Newmark (rápido)" if x == "newmark" else "Integração (preciso)",
                help="Método para cálculo do fator de influência",
                key="bulbo_method"
            )
            
            analyze_bulbo = st.button(
                "🔍 Calcular Bulbo de Tensões",
                type="primary",
                width="stretch",
                key="btn_bulbo"
            )
        
        with col_viz:
            placeholder_bulbo = st.empty()
            
            if analyze_bulbo:
                try:
                    # 1. Criar objetos de dados
                    if st.session_state.current_solo:
                        solo = st.session_state.current_solo
                    else:
                        solo = Solo(
                            nome="Solo Configurado",
                            peso_especifico=st.session_state.soil_params['gamma'],
                            coeficiente_poisson=st.session_state.soil_params.get('mu', 0.3)
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
                    
                    # 3. Criar gráfico com isóbaras corrigidas
                    try:
                        # Tenta usar o método corrigido
                        fig = bulbo.plot_bulbo_2d_com_isobaras(resultado)
                    except AttributeError:
                        # Fallback para o método original
                        st.warning("Usando método de visualização padrão (plot_bulbo_2d)")
                        try:
                            fig = bulbo.plot_bulbo_2d(resultado)
                        except AttributeError:
                            st.error("Método de plotagem não encontrado no módulo bulbo_tensoes")
                            return
                    
                    placeholder_bulbo.plotly_chart(fig, use_container_width=True)
                    
                    # 4. Exibir métricas de influência
                    st.markdown("### 📊 Profundidades de Influência")
                    
                    z_10 = bulbo.calcular_profundidade_influencia(B, L, 0.10)
                    z_20 = bulbo.calcular_profundidade_influencia(B, L, 0.20)
                    z_05 = bulbo.calcular_profundidade_influencia(B, L, 0.05)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Até 20% de q", f"{z_20:.2f} m", f"{z_20/B:.1f}×B")
                    with col2:
                        st.metric("Até 10% de q", f"{z_10:.2f} m", f"{z_10/B:.1f}×B")
                    with col3:
                        st.metric("Até 5% de q", f"{z_05:.2f} m", f"{z_05/B:.1f}×B")
                    
                    # 5. Relatório técnico com opção PDF
                    with st.expander("📄 Relatório Técnico do Bulbo"):
                        relatorio = bulbo.relatorio_tecnico_bulbo(q_applied, B, L)
                        st.text_area("Resumo do Relatório", relatorio, height=300)
                        
                        # Botões de exportação
                        col_txt, col_pdf = st.columns(2)
                        
                        with col_txt:
                            st.download_button(
                                label="📥 Baixar Relatório (TXT)",
                                data=relatorio,
                                file_name=f"bulbo_tensoes_B{B}_L{L}_{datetime.now().strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        with col_pdf:
                            try:
                                # Gerar HTML/PDF
                                pdf_file = bulbo.exportar_pdf_bulbo(resultado)
                                with open(pdf_file, 'rb') as f:
                                    st.download_button(
                                        label="📄 Baixar Relatório (HTML/PDF)",
                                        data=f,
                                        file_name=f"bulbo_tensoes_B{B}_L{L}_{datetime.now().strftime('%Y%m%d')}.html",
                                        mime="text/html",
                                        use_container_width=True
                                    )
                            except AttributeError:
                                st.info("Exportação PDF não disponível nesta versão")
                    
                    # 6. Armazenar resultados
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
                    
                    # DEBUG (se ativado)
                    if st.session_state.get('debug_mode', False):
                        st.markdown("### 🔍 DEBUG - Valores do Bulbo")
                        st.write(f"Shape do tensões: {resultado.tensoes.shape}")
                        st.write(f"Valor máximo: {resultado.tensoes.max():.1f} kPa")
                        st.write(f"Valor mínimo: {resultado.tensoes.min():.1f} kPa")
                        st.write(f"Média: {resultado.tensoes.mean():.1f} kPa")
                        
                        if resultado.tensoes.max() < 0.001:
                            st.warning("⚠️ Valores de tensão próximos de zero!")
                            
                except Exception as e:
                    placeholder_bulbo.error(f"❌ Erro no cálculo do bulbo: {str(e)}")
                    if st.session_state.get('debug_mode', False):
                        import traceback
                        st.error(f"Traceback: {traceback.format_exc()}")
            else:
                placeholder_bulbo.info("""
                ### 🎯 Bulbo de Tensões - Solução de Boussinesq
                
                **Configure os parâmetros e clique em 'Calcular Bulbo de Tensões'**
                
                Esta ferramenta calcula a distribuição de tensões verticais (Δσ) no solo
                sob uma fundação retangular com carga uniforme, utilizando a **solução
                teórica de Boussinesq**.
                
                **Resultado:** Gráfico de contorno mostrando as isócuras de tensão
                em porcentagem da pressão aplicada.
                
                **Isóbaras corrigidas:** As linhas de tensão constante agora são visíveis!
                """)
    
    with tab2:
        st.markdown("## 🏗️ Análise de Capacidade de Carga (Terzaghi)")
        
        col_terz1, col_terz2 = st.columns([1, 2])
        
        with col_terz1:
            st.markdown("### ⚙️ Configuração Terzaghi")
            
            # Usar valores do bulbo ou personalizados
            use_bulbo_values = st.checkbox("Usar valores do Bulbo", True, 
                                         help="Usa B, L, q da análise anterior")
            
            if use_bulbo_values and st.session_state.current_fundacao:
                B_terz = st.session_state.current_fundacao.largura
                L_terz = st.session_state.current_fundacao.comprimento
                q_terz = st.session_state.current_fundacao.carga
            else:
                B_terz = st.number_input("B [m]", 0.5, 10.0, 1.5, 0.1, key="terz_B")
                L_terz = st.number_input("L [m]", 0.5, 10.0, 1.5, 0.1, key="terz_L")
                q_terz = st.number_input("q [kPa]", 50.0, 5000.0, 200.0, 10.0, key="terz_q")
            
            D_f = st.number_input(
                "Profundidade assentamento (D_f) [m]",
                min_value=0.5,
                max_value=10.0,
                value=1.0,
                step=0.1,
                help="Profundidade da base da sapata"
            )
            
            shape = st.selectbox(
                "Forma da sapata",
                ["square", "rectangular", "strip", "circular"],
                format_func=lambda x: {
                    "square": "Quadrada",
                    "rectangular": "Retangular", 
                    "strip": "Corrida",
                    "circular": "Circular"
                }[x]
            )
            
            foundation_type = st.selectbox(
                "Tipo de sapata",
                ["flexible", "rigid"],
                format_func=lambda x: "Flexível" if x == "flexible" else "Rígida"
            )
            
            analyze_terzaghi = st.button(
                "🔒 Analisar Capacidade de Carga",
                type="primary",
                width="stretch"
            )
        
        with col_terz2:
            placeholder_terz = st.empty()
            
            if analyze_terzaghi:
                try:
                    # Verificar se temos solo
                    if not st.session_state.current_solo:
                        st.error("Configure primeiro os parâmetros do solo na barra lateral")
                        return
                    
                    solo = st.session_state.current_solo
                    
                    # Criar designer
                    designer = FoundationDesigner()
                    
                    # Preparar parâmetros
                    soil_params = {
                        'c': solo.coesao if solo.coesao is not None else st.session_state.soil_params['c'],
                        'phi': solo.angulo_atrito if solo.angulo_atrito is not None else st.session_state.soil_params['phi'],
                        'gamma': solo.peso_especifico,
                        'E': solo.modulo_elasticidade or st.session_state.soil_params.get('E', 30000),
                        'mu': solo.coeficiente_poisson or st.session_state.soil_params.get('mu', 0.3)
                    }
                    
                    foundation_params = {
                        'B': B_terz,
                        'L': L_terz,
                        'D_f': D_f,
                        'shape': shape
                    }
                    
                    # CORREÇÃO: Usar load_params (não loading_params)
                    load_params = {
                        'q_applied': q_terz,
                        'load_type': 'static'
                    }
                    
                    # Calcular
                    with st.spinner("Calculando capacidade de carga..."):
                        design = designer.complete_design(soil_params, foundation_params, load_params)
                    
                    if design['success']:
                        # Armazenar resultados
                        st.session_state.terzaghi_results = design
                        
                        # Mostrar resultados principais
                        st.markdown("### 📊 Resultados Principais")
                        
                        col_res1, col_res2, col_res3 = st.columns(3)
                        
                        with col_res1:
                            q_ult = design['bearing_capacity']['q_ult']
                            q_adm = design['bearing_capacity']['q_adm']
                            st.metric("q_ult", f"{q_ult:.0f} kPa")
                            st.metric("q_adm (FS=3)", f"{q_adm:.0f} kPa")
                        
                        with col_res2:
                            fs = design['safety_check']['fs_calculated']
                            status = design['safety_check']['status']
                            color = design['safety_check'].get('color', 'green' if status == 'SAFE' else 'red')
                            
                            st.metric("Fator Segurança", f"{fs:.2f}")
                            st.markdown(f"<h4 style='color:{color};'>{status}</h4>", 
                                      unsafe_allow_html=True)
                        
                        with col_res3:
                            if design.get('settlement'):
                                sett = design['settlement']['settlement_mm']
                                st.metric("Recalque", f"{sett:.1f} mm")
                                
                                if sett > 25:
                                    st.error("> 25 mm (limite)")
                                elif sett > 15:
                                    st.warning("> 15 mm (recomendado)")
                                else:
                                    st.success("< 15 mm (ótimo)")
                            else:
                                st.info("Sem dados de recalque")
                        
                        # Gráfico de interação
                        st.markdown("### 📈 Diagrama de Interação")
                        
                        # Preparar dados para o gráfico
                        q_max = q_ult * 1.2
                        q_values = np.linspace(0.1, q_max, 50)
                        fs_values = q_ult / q_values
                        
                        fig_terz = go.Figure()
                        
                        # Curva de capacidade
                        fig_terz.add_trace(go.Scatter(
                            x=q_values, y=fs_values,
                            mode='lines',
                            name='Curva de Capacidade',
                            line=dict(color='blue', width=3),
                            hovertemplate="q=%{x:.0f} kPa<br>FS=%{y:.2f}<extra></extra>"
                        ))
                        
                        # Ponto de projeto
                        fig_terz.add_trace(go.Scatter(
                            x=[q_terz],
                            y=[fs],
                            mode='markers+text',
                            marker=dict(size=15, color='red'),
                            text=[f'Projeto<br>FS={fs:.2f}'],
                            textposition='top center',
                            name='Ponto Atual'
                        ))
                        
                        # Linhas de referência
                        fig_terz.add_hline(y=3.0, line_dash="dash", line_color="green",
                                         annotation_text="FS mínimo=3.0")
                        fig_terz.add_hline(y=1.0, line_dash="dash", line_color="red",
                                         annotation_text="Ruptura (FS=1)")
                        
                        fig_terz.update_layout(
                            title="Diagrama Pressão vs Fator de Segurança",
                            xaxis_title="Pressão Aplicada q [kPa]",
                            yaxis_title="Fator de Segurança FS",
                            height=400
                        )
                        
                        st.plotly_chart(fig_terz, use_container_width=True)
                        
                        # Fatores de capacidade
                        with st.expander("📐 Fatores de Capacidade de Carga"):
                            bearing = design['bearing_capacity']
                            col_f1, col_f2, col_f3 = st.columns(3)
                            
                            with col_f1:
                                st.metric("N_c", f"{bearing['Nc']:.2f}")
                                st.metric("s_c", f"{bearing['sc']:.2f}")
                                st.metric("d_c", f"{bearing['dc']:.2f}")
                            
                            with col_f2:
                                st.metric("N_q", f"{bearing['Nq']:.2f}")
                                st.metric("s_q", f"{bearing['sq']:.2f}")
                                st.metric("d_q", f"{bearing['dq']:.2f}")
                            
                            with col_f3:
                                st.metric("N_γ", f"{bearing['Ngamma']:.2f}")
                                st.metric("s_γ", f"{bearing['sgamma']:.2f}")
                                st.metric("d_γ", f"{bearing['dgamma']:.2f}")
                        
                        # Recomendações
                        st.markdown("### 📋 Recomendações de Projeto")
                        if 'recommendations' in design:
                            for rec in design['recommendations']:
                                if rec.startswith("❌"):
                                    st.error(rec)
                                elif rec.startswith("⚠️"):
                                    st.warning(rec)
                                elif rec.startswith("✅"):
                                    st.success(rec)
                                else:
                                    st.info(rec)
                        else:
                            st.info("Sem recomendações disponíveis")
                        
                        # Resumo completo
                        with st.expander("📄 Resumo Completo do Projeto"):
                            if 'design_summary' in design:
                                st.text_area("Resumo do Projeto", design['design_summary'], height=300)
                                
                                # Botões de download
                                col_txt2, col_pdf2 = st.columns(2)
                                
                                with col_txt2:
                                    st.download_button(
                                        label="📥 Baixar Relatório (TXT)",
                                        data=design['design_summary'],
                                        file_name=f"terzaghi_B{B_terz}_L{L_terz}.txt",
                                        mime="text/plain",
                                        use_container_width=True
                                    )
                                
                                with col_pdf2:
                                    try:
                                        # Exportar para HTML/PDF
                                        pdf_file = designer.exportar_pdf_terzaghi(design)
                                        with open(pdf_file, 'rb') as f:
                                            st.download_button(
                                                label="📄 Baixar Relatório (HTML/PDF)",
                                                data=f,
                                                file_name=f"terzaghi_B{B_terz}_L{L_terz}.html",
                                                mime="text/html",
                                                use_container_width=True
                                            )
                                    except AttributeError:
                                        st.info("Exportação PDF não disponível nesta versão")
                            else:
                                st.info("Resumo não disponível")
                    else:
                        st.error(f"Erro no cálculo: {design.get('error', 'Erro desconhecido')}")
                        
                except Exception as e:
                    placeholder_terz.error(f"❌ Erro na análise de Terzaghi: {str(e)}")
                    if st.session_state.get('debug_mode', False):
                        import traceback
                        st.error(f"Traceback: {traceback.format_exc()}")
            else:
                placeholder_terz.info("""
                ### 🔒 Análise de Capacidade de Carga - Teoria de Terzaghi
                
                **Configure os parâmetros e clique em 'Analisar Capacidade de Carga'**
                
                Esta análise calcula:
                1. **Capacidade de carga última (q_ult)**
                2. **Fator de segurança (FS)**
                3. **Recalques elásticos (δ)**
                4. **Recomendações de projeto**
                
                **Equação de Terzaghi:**
                ```
                q_ult = c·N_c·s_c·d_c + γ·D_f·N_q·s_q·d_q + 0.5·γ·B·N_γ·s_γ·d_γ
                ```
                
                **Critérios:**
                - FS ≥ 3.0 (segurança)
                - δ ≤ 25 mm (recalque máximo)
                - δ ≤ 15 mm (recomendado)
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
    com o bulbo de tensões Boussinesq e capacidade de carga Terzaghi implementados.
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
    
    # Resultados de Terzaghi
    if st.session_state.terzaghi_results:
        st.markdown("### 🏗️ Resultados de Terzaghi")
        with st.expander("Ver resultados"):
            st.json(st.session_state.terzaghi_results)
    
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
            "E": 5000.0,
            "descricao": "Baixa resistência, alta compressibilidade"
        },
        "Argila Rija": {
            "c": 50.0, "phi": 0.0, "gamma": 19.0, 
            "coeficiente_poisson": 0.4,
            "E": 25000.0,
            "descricao": "Resistência média, compressibilidade moderada"
        },
        "Silte": {
            "c": 0.0, "phi": 28.0, "gamma": 18.0, 
            "coeficiente_poisson": 0.35,
            "E": 15000.0,
            "descricao": "Granular fino, comportamento intermediário"
        },
        "Areia Fina": {
            "c": 0.0, "phi": 30.0, "gamma": 17.0, 
            "coeficiente_poisson": 0.3,
            "E": 20000.0,
            "descricao": "Granular, drenante, baixa coesão"
        },
        "Areia Média": {
            "c": 0.0, "phi": 32.0, "gamma": 18.0, 
            "coeficiente_poisson": 0.3,
            "E": 30000.0,
            "descricao": "Resistência boa, compactação média"
        },
        "Areia Grossa": {
            "c": 0.0, "phi": 35.0, "gamma": 19.0, 
            "coeficiente_poisson": 0.25,
            "E": 40000.0,
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
                "E": st.column_config.NumberColumn("Módulo E (kPa)", format="%.0f"),
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
                    coeficiente_poisson=soil['coeficiente_poisson'],
                    modulo_elasticidade=soil['E']
                )
                
                st.session_state.current_solo = solo
                st.session_state.soil_params.update({
                    'c': soil['c'],
                    'phi': soil['phi'],
                    'gamma': soil['gamma'],
                    'E': soil['E']
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
            E_custom = st.number_input("E [kPa]", 1000.0, 1000000.0, 30000.0, 1000.0, key="E_custom")
            soil_name = st.text_input("Nome do solo", "Meu Solo", key="soil_name")
        
        if st.button("Criar Solo Personalizado", type="primary", width="stretch"):
            try:
                solo_custom = Solo(
                    nome=soil_name,
                    peso_especifico=gamma_custom,
                    angulo_atrito=phi_custom,
                    coesao=c_custom,
                    coeficiente_poisson=nu_custom,
                    modulo_elasticidade=E_custom
                )
                
                st.session_state.current_solo = solo_custom
                st.session_state.soil_params.update({
                    'c': c_custom,
                    'phi': phi_custom,
                    'gamma': gamma_custom,
                    'E': E_custom
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
        ## 📖 Teoria do Simulador
        
        ### Solução de Boussinesq (1885)
        
        Distribuição de tensões em meio elástico, homogêneo, isotrópico:
        ```math
        σ_z = \\frac{3Qz^3}{2πR^5}
        ```
        
        ### Teoria de Terzaghi (1943)
        
        Capacidade de carga de fundações superficiais:
        ```math
        q_ult = c·N_c·s_c·d_c + γ·D_f·N_q·s_q·d_q + 0.5·γ·B·N_γ·s_γ·d_γ
        ```
        
        ### Fatores de Segurança
        
        - **Capacidade de carga**: FS ≥ 3.0
        - **Recalques**: δ ≤ 25 mm (estruturas convencionais)
        - **Mobilização**: φ_mobilizado ≤ 0.67·φ
        
        ### Aplicações Práticas
        
        1. **Dimensionamento de fundações**
        2. **Análise de capacidade de carga**
        3. **Cálculo de recalques**
        4. **Verificação de segurança**
        5. **Estudo de interação entre fundações**
        """)
    
    with tab2:
        st.markdown("""
        ## 💻 Guia de Uso
        
        ### 1. Configuração Inicial
        
        1. Acesse a página **"Sapatas"**
        2. Configure os parâmetros na barra lateral:
           - Coesão (c), Ângulo (φ), Peso (γ)
           - Módulo de elasticidade (E)
        
        3. Configure a sapata:
           - Largura (B) e Comprimento (L)
           - Pressão aplicada (q)
        
        ### 2. Análise de Distribuição de Tensões
        
        1. Clique em **"Calcular Bulbo de Tensões"**
        2. Visualize o gráfico de contorno
        3. Analise as profundidades de influência
        
        ### 3. Análise de Capacidade de Carga
        
        1. Clique em **"Analisar Capacidade de Carga"**
        2. Verifique o fator de segurança
        3. Analise os recalques
        4. Siga as recomendações
        
        ### 4. Exportação
        
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
        - **`src/terzaghi.py`**: Capacidade de carga + recalques
        - **`src/mohr_coulomb.py`**: Análise de tensões
        - **`src/export_system.py`**: Sistema de exportação
        
        ### Tecnologias Utilizadas
        
        - **Streamlit**: Interface web
        - **Plotly**: Visualizações gráficas
        - **NumPy**: Cálculos numéricos
        - **Pandas**: Manipulação de dados
        - **SciPy**: Integração numérica
        
        ### Licença
        
        MIT License - Livre para uso acadêmico e profissional.
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
    🏗️ Simulador Solo-Fundações v2.4.0 | Boussinesq + Terzaghi (Corrigido) | 
    {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)

if __name__ == "__main__":
    main()