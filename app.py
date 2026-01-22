"""
🏗️ SIMULADOR INTERATIVO DE SOLO E FUNDAÇÕES
Aplicação web completa para análise geotécnica
Integração dos módulos: Mohr-Coulomb, Exportação e Validação NBR
Versão 2.1.0 - Refatorada com dataclasses
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
    - models.py (novo)
    - mohr_coulomb.py
    - bulbo_tensoes.py (refatorado)
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
        Versão 2.1.0 - Com dataclasses  
        Python + Streamlit + Plotly
        """)
        
        return app_mode

def home_page():
    """Página inicial do simulador"""
    st.title("🏗️ Simulador Interativo de Solo e Fundações")
    st.markdown("### Laboratório Virtual para Análise Geotécnica - Versão Refatorada")
    
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
        ✅ **Arquitetura moderna** com dataclasses  
        
        ## 🎯 Novidades da Versão 2.1.0
        
        1. **Dataclasses** para modelagem de dados (Solo, Fundacao)
        2. **Validação automática** de parâmetros de entrada
        3. **Código mais seguro** e manutenível
        4. **Preparado para testes** automatizados
        
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
        - ✅ Dataclasses (Novo!)
        
        **Status da Refatoração:**
        1. ✅ models.py criado
        2. ✅ bulbo_tensoes.py refatorado
        3. 🔄 app.py atualizado
        4. ⏳ Testes em desenvolvimento
        
        **Próximos Passos:**
        1. Expandir testes automatizados
        2. Implementar validação numérica
        3. Melhorar UI/UX
        """)
        
        # Métricas rápidas
        st.metric("Versão", "2.1.0")
        st.metric("Última Atualização", datetime.now().strftime("%d/%m/%Y"))
        
        # Verificar objetos carregados
        if st.session_state.current_solo:
            st.success("✅ Objeto Solo carregado")
        else:
            st.warning("⚠️ Objeto Solo não carregado")
        
        # Início rápido
        with st.expander("⚡ Início Rápido"):
            if st.button("Ir para Análise de Solo"):
                st.session_state.app_mode = "Análise de Solo"
                st.rerun()
            if st.button("Ir para Sapatas"):
                st.session_state.app_mode = "Sapatas"
                st.rerun()
            if st.button("Testar Dataclasses"):
                test_dataclasses()
    
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

def test_dataclasses():
    """Teste rápido das dataclasses"""
    st.info("### Teste das Dataclasses")
    
    try:
        # Teste Solo
        solo_teste = Solo(
            nome="Areia Média",
            peso_especifico=18.5,
            angulo_atrito=32.0,
            coesao=0.0,
            modulo_elasticidade=50.0,
            coeficiente_poisson=0.3
        )
        
        # Teste Fundacao
        fundacao_teste = Fundacao(
            largura=1.5,
            comprimento=1.5,
            carga=200.0
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ Solo criado com sucesso!")
            st.json(solo_teste.__dict__)
        
        with col2:
            st.success("✅ Fundacao criada com sucesso!")
            st.json(fundacao_teste.__dict__)
            
        # Teste de validação
        st.markdown("#### Teste de Validação")
        
        try:
            solo_invalido = Solo(nome="Inválido", peso_especifico=-10.0)
            st.error("❌ VALIDAÇÃO FALHOU: Solo com peso específico negativo não deveria ser criado")
        except ValueError as e:
            st.success(f"✅ Validação funcionou: {e}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erro no teste: {e}")
        return False

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
                    
            except Exception as e:
                st.error(f"Erro na análise: {e}")
        
        else:
            # Mostrar gráfico padrão
            try:
                fig, _ = soil.create_mohr_circle_plot(100, 200, 50, 0, True, True)
                st.plotly_chart(fig, use_container_width=True)
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
                    st.plotly_chart(fig_path, use_container_width=True)
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
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")

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
            use_container_width=True,
            key="btn_analisar_sapata"
        )
    
    with col_viz:
        # Espaço para visualizações
        placeholder = st.empty()
        
        if analyze_button:
            # Criar objetos Solo e Fundacao
            try:
                # Usar Solo da sessão se disponível
                if st.session_state.current_solo:
                    solo = st.session_state.current_solo
                else:
                    # Criar novo Solo com parâmetros atuais
                    solo = Solo(
                        nome="Solo Atual",
                        peso_especifico=st.session_state.soil_params['gamma'],
                        angulo_atrito=st.session_state.soil_params['phi'],
                        coesao=st.session_state.soil_params['c'],
                        coeficiente_poisson=0.3
                    )
                    st.session_state.current_solo = solo
                
                # Criar Fundacao
                fundacao = Fundacao(
                    largura=B,
                    comprimento=L,
                    carga=q_applied
                )
                st.session_state.current_fundacao = fundacao
                
                st.success(f"✅ Criados: {solo.nome} e Fundação {B}x{L}m")
                
            except ValueError as e:
                st.error(f"❌ Erro na criação dos objetos: {e}")
                return
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")
                return
            
            with st.spinner("Calculando capacidade de carga..."):
                try:
                    # Calcular capacidade de carga
                    q_ult, (Nc, Nq, Nγ) = bearing_capacity_terzaghi(
                        solo.coesao or 0,
                        solo.angulo_atrito or 0,
                        solo.peso_especifico,
                        B, L, D_f, foundation_type
                    )
                    
                    # Calcular recalque (simplificado)
                    E_s = 50000  # kPa (valor padrão)
                    mu = solo.coeficiente_poisson or 0.3
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
                        'fundacao': fundacao.__dict__,
                        'solo': solo.__dict__,
                        'D_f': D_f,
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
                            
                except Exception as e:
                    st.error(f"❌ Erro nos cálculos: {e}")
                    placeholder.error("Verifique os parâmetros e tente novamente.")
        else:
            # Exibir imagem ilustrativa inicial
            placeholder.info("""
            ### Configure a sapata e clique em "Analisar Sapata"
            
            **Parâmetros a serem definidos:**
            1. **Tipo de sapata**: Forma da base
            2. **Dimensões**: Largura, comprimento, profundidade
            3. **Carregamento**: Pressão aplicada
            4. **Concreto**: Resistência característica
            
            **Novo na versão 2.1.0:**
            • Objetos Solo e Fundacao criados automaticamente
            • Validação automática dos parâmetros
            • Estrutura preparada para testes
            
            **Resultados obtidos:**
            • Capacidade de carga última
            • Fator de segurança
            • Recalque estimado
            • Bulbo de tensões
            • Validação conforme NBR 6122
            """)
    
    # Abas para bulbos de tensões (apenas se análise foi realizada)
    if analyze_button and 'analysis_results' in st.session_state:
        st.divider()
        st.markdown("### 📈 Bulbos de Tensões")
        
        tab_bulbo1, tab_bulbo2, tab_bulbo3 = st.tabs(["Método 2:1", "Método Boussinesq", "Comparativo"])
        
        with tab_bulbo1:
            try:
                st.markdown("#### Método 2:1 Simplificado")
                # Gerar bulbo 2:1 usando a nova classe
                bulbo = BulboTensoes()
                X_21, Z_21, sigma_21 = bulbo.gerar_bulbo_21(B, L, depth_ratio=3.0)
                
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
                
            except Exception as e:
                st.error(f"Erro no método 2:1: {e}")
        
        with tab_bulbo2:
            try:
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
                    # Usar o método avançado com dataclasses
                    if st.session_state.current_solo and st.session_state.current_fundacao:
                        resultado = bulbo.gerar_bulbo_boussinesq_avancado(
                            st.session_state.current_fundacao,
                            st.session_state.current_solo,
                            depth_ratio=3.0,
                            grid_size=resolucao,
                            method=metodo
                        )
                        
                        # Extrair dados do resultado
                        sigma_b = resultado.tensoes
                        coords = resultado.coordenadas
                        
                        # Pegar slice central (y=0)
                        center_slice = sigma_b[:, sigma_b.shape[1]//2, :] / st.session_state.current_fundacao.carga * 100
                        X_b_slice = coords[:, sigma_b.shape[1]//2, :, 0]
                        Z_b_slice = coords[:, sigma_b.shape[1]//2, :, 2]
                        
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
                    else:
                        st.error("Objetos Solo ou Fundacao não encontrados na sessão.")
                        
            except Exception as e:
                st.error(f"Erro no método Boussinesq: {e}")
                st.info("Tente reduzir a resolução da malha para melhorar a performance.")
        
        with tab_bulbo3:
            try:
                st.markdown("#### Comparativo: Método 2:1 vs Boussinesq")
                
                bulbo = BulboTensoes()
                fig_comparativo = bulbo.plot_comparativo_bulbos(q_applied, B, L, depth_ratio=3.0)
                st.plotly_chart(fig_comparativo, use_container_width=True)
                
                # Relatório técnico
                with st.expander("📊 Relatório Técnico Comparativo"):
                    relatorio = bulbo.relatorio_tecnico_bulbo(q_applied, B, L)
                    st.text(relatorio)
                    
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=relatorio,
                        file_name=f"relatorio_bulbo_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key="btn_download_relatorio_bulbo"
                    )
                    
            except Exception as e:
                st.error(f"Erro no comparativo: {e}")
        
        # Validação NBR (apenas se análise foi realizada)
        st.divider()
        st.markdown("### 📋 Validação conforme NBR 6122")
        
        try:
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
                        
        except Exception as e:
            st.error(f"Erro na validação NBR: {e}")

def deep_foundation_page():
    """Página de análise de estacas"""
    st.title("📏 Análise de Estacas (Fundações Profundas)")
    
    if not MODULES_LOADED:
        st.error("Módulo de fundações não carregado!")
        return
    
    tab_config, tab_results = st.tabs(["⚙️ Configuração", "📊 Resultados"])
    
    with tab_config:
        st.info("""
        **Nota:** Esta página ainda está sendo adaptada para usar dataclasses.
        Para análise completa de estacas, use a página de Sapatas que já está refatorada.
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
            
            load_applied = st.number_input(
                "Carga aplicada [kN]",
                min_value=100,
                max_value=10000,
                value=1500,
                step=100,
                key="pile_load"
            )
        
        with col_soil:
            st.markdown("### 🌱 Perfil do Solo")
            st.warning("A criação de perfil de solo com dataclasses está em desenvolvimento.")
            
            # Usar Solo atual da sessão
            if st.session_state.current_solo:
                solo = st.session_state.current_solo
                st.success(f"Usando solo atual: {solo.nome}")
                st.json(solo.__dict__)
            else:
                st.warning("Nenhum solo carregado. Configure na página de Sapatas primeiro.")
    
    with tab_results:
        st.info("Funcionalidade de estacas em desenvolvimento com arquitetura de dataclasses.")
        
        # Botão para redirecionar para sapatas
        if st.button("🧪 Testar Nova Arquitetura em Sapatas", type="primary"):
            st.session_state.app_mode = "Sapatas"
            st.rerun()

def export_page():
    """Página de exportação de resultados"""
    st.title("📤 Exportação de Resultados")
    
    if not MODULES_LOADED:
        st.error("Sistema de exportação não carregado!")
        return
    
    st.info("""
    **Novidade:** O sistema de exportação agora inclui informações dos objetos
    Solo e Fundacao nas dataclasses.
    """)
    
    # Mostrar objetos atuais se existirem
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.current_solo:
            st.success("✅ Solo disponível para exportação")
            with st.expander("Ver Solo"):
                st.json(st.session_state.current_solo.__dict__)
        else:
            st.warning("⚠️ Nenhum Solo configurado")
    
    with col2:
        if st.session_state.current_fundacao:
            st.success("✅ Fundacao disponível para exportação")
            with st.expander("Ver Fundacao"):
                st.json(st.session_state.current_fundacao.__dict__)
        else:
            st.warning("⚠️ Nenhuma Fundacao configurada")
    
    # Usar a UI do módulo de exportação
    try:
        streamlit_export_ui()
    except Exception as e:
        st.error(f"Erro no sistema de exportação: {e}")
        st.info("Configure uma análise primeiro para exportar resultados.")

def nbr_validation_page():
    """Página de validação normativa"""
    st.title("📐 Validação Normativa - NBR 6122/6118")
    
    if not MODULES_LOADED:
        st.error("Módulo de validação NBR não carregado!")
        return
    
    # Mostrar objetos atuais
    st.markdown("### Objetos Atuais para Validação")
    
    if st.session_state.current_solo:
        st.info(f"**Solo atual:** {st.session_state.current_solo.nome}")
    
    if st.session_state.current_fundacao:
        st.info(f"**Fundação atual:** {st.session_state.current_fundacao.largura}x{st.session_state.current_fundacao.comprimento}m")
    
    # Usar a UI do módulo de validação
    try:
        nbr_validation_ui()
    except Exception as e:
        st.error(f"Erro no módulo de validação: {e}")

def soil_database_page():
    """Página do banco de dados de solos"""
    st.title("📊 Banco de Dados de Solos")
    
    # Dados de solos típicos
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
        "Pedregulho": {
            "c": 0.0, "phi": 40.0, "gamma": 20.0, 
            "coeficiente_poisson": 0.2,
            "descricao": "Alta resistência, excelente capacidade de carga"
        },
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
                "coeficiente_poisson": st.column_config.NumberColumn("ν", format="%.2f"),
                "descricao": st.column_config.TextColumn("Descrição", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Seleção para carregar dados
        st.markdown("### 🚀 Carregar para Análise")
        selected_soil = st.selectbox("Selecione um tipo de solo:", list(soil_data.keys()))
        
        if st.button("Carregar Parâmetros", type="primary"):
            try:
                soil = soil_data[selected_soil]
                
                # Criar objeto Solo
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
                
                st.success(f"✅ Solo '{selected_soil}' carregado como objeto!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao carregar solo: {e}")
    
    with tab_import:
        st.markdown("### Importar Dados Personalizados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            c_custom = st.number_input("Coesão personalizada [kPa]", 0.0, 200.0, 10.0, 1.0, key="c_custom")
            phi_custom = st.number_input("Ângulo personalizado [°]", 0.0, 45.0, 30.0, 1.0, key="phi_custom")
            gamma_custom = st.number_input("Peso personalizado [kN/m³]", 10.0, 25.0, 18.0, 0.1, key="gamma_custom")
        
        with col2:
            nu_custom = st.number_input("Coef. Poisson (ν)", 0.0, 0.49, 0.3, 0.01, key="nu_custom")
            soil_name = st.text_input("Nome do solo personalizado", "Meu Solo", key="soil_name")
            description = st.text_area("Descrição", "Solo com parâmetros personalizados", key="soil_desc")
        
        if st.button("Salvar Solo Personalizado"):
            try:
                # Criar objeto Solo
                solo_custom = Solo(
                    nome=soil_name,
                    peso_especifico=gamma_custom,
                    angulo_atrito=phi_custom,
                    coesao=c_custom,
                    coeficiente_poisson=nu_custom
                )
                
                # Atualizar estado
                st.session_state.current_solo = solo_custom
                st.session_state.soil_params.update({
                    'c': c_custom,
                    'phi': phi_custom,
                    'gamma': gamma_custom
                })
                
                # Adicionar ao dicionário
                soil_data[soil_name] = {
                    "c": c_custom,
                    "phi": phi_custom,
                    "gamma": gamma_custom,
                    "coeficiente_poisson": nu_custom,
                    "descricao": description
                }
                
                st.success(f"✅ Solo '{soil_name}' salvo e carregado como objeto!")
                
                # Mostrar objeto criado
                with st.expander("Ver objeto Solo criado"):
                    st.json(solo_custom.__dict__)
                    
            except ValueError as e:
                st.error(f"❌ Erro de validação: {e}")
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

def documentation_page():
    """Página de documentação do projeto"""
    st.title("📚 Documentação do Projeto - Versão 2.1.0")
    
    tab_docs, tab_code, tab_about, tab_dataclasses = st.tabs([
        "📖 Documentação", "💻 Código", "👨‍🎓 Sobre", "🏗️ Dataclasses"
    ])
    
    with tab_docs:
        st.markdown("""
        ## 📖 Documentação Técnica - Versão 2.1.0
        
        ### 1. Arquitetura do Sistema (Refatorada)
        
        ```
        simulador_interativo_solo_fundacoes/
        ├── app.py                          # Aplicação principal (REFATORADA)
        ├── requirements.txt                # Dependências
        ├── src/                           # Módulos Python
        │   ├── models.py                  # NOVO: Dataclasses (Solo, Fundacao)
        │   ├── mohr_coulomb.py            # Análise de tensões
        │   ├── bulbo_tensoes.py           # REFATORADO: Bulbo de tensões
        │   ├── foundation_calculations.py # Cálculos de fundações
        │   ├── soil_calculations.py       # Propriedades do solo
        │   ├── export_system.py           # Sistema de exportação
        │   └── nbr_validation.py          # Validação normativa
        ├── tests/                         # Testes unitários
        │   ├── test_models.py             # NOVO: Testes das dataclasses
        │   └── test_foundation.py         # Testes de fundações
        ├── examples/                      # Exemplos de uso
        └── docs/                          # Documentação
        ```
        """)
    
    with tab_code:
        st.markdown("""
        ## 💻 Guia de Desenvolvimento - Refatoração
        
        ### 1. Nova Estrutura com Dataclasses
        
        #### 1.1 Modelos de Dados (`src/models.py`)
        ```python
        @dataclass
        class Solo:
            nome: str
            peso_especifico: float  # kN/m³
            angulo_atrito: Optional[float] = None
            coesao: Optional[float] = None
            coeficiente_poisson: float = 0.3
            
            def __post_init__(self):
                # Validação automática!
                if self.peso_especifico <= 0:
                    raise ValueError("Peso específico deve ser positivo")
        
        @dataclass
        class Fundacao:
            largura: float  # m
            comprimento: float  # m
            carga: float  # kN/m²
        ```
        
        #### 1.2 Uso no Código
        ```python
        # Antes (dicionários)
        solo_params = {'c': 10, 'phi': 30, 'gamma': 18}
        
        # Depois (dataclasses)
        solo = Solo(nome="Areia", coesao=10, angulo_atrito=30, peso_especifico=18)
        fundacao = Fundacao(largura=1.5, comprimento=1.5, carga=200)
        
        # Validação automática
        try:
            solo_invalido = Solo(nome="Inválido", peso_especifico=-10)
        except ValueError as e:
            print(f"Erro: {e}")  # "Peso específico deve ser positivo"
        ```
        """)
    
    with tab_about:
        st.markdown("""
        ## 👨‍🎓 Sobre o Projeto - Refatoração
        
        ### Informações da Refatoração
        
        **Versão:** 2.1.0 (Com dataclasses)
        
        **Data da Refatoração:** Janeiro 2024
        
        **Objetivos da Refatoração:**
        1. **Segurança:** Validação automática de dados
        2. **Manutenibilidade:** Código mais limpo e organizado
        3. **Testabilidade:** Facilidade para criar testes unitários
        4. **Extensibilidade:** Preparado para novas funcionalidades
        
        ### Progresso da Refatoração
        
        ✅ **Fase 1 - Modelos de Dados:**
        - [x] Criar dataclasses Solo e Fundacao
        - [x] Implementar validação automática
        - [x] Atualizar bulbo_tensoes.py
        - [x] Integrar com app.py
        
        🔄 **Fase 2 - Testes e Validação:**
        - [ ] Criar testes para dataclasses
        - [ ] Implementar validação numérica
        - [ ] Expandir suite de testes
        
        ⏳ **Fase 3 - UI/UX e Funcionalidades:**
        - [ ] Melhorar interface do usuário
        - [ ] Adicionar novos métodos teóricos
        - [ ] Implementar análise de capacidade de carga
        """)
    
    with tab_dataclasses:
        st.markdown("""
        ## 🏗️ Guia das Dataclasses
        
        ### 1. Benefícios
        
        #### 1.1 Validação Automática
        ```python
        # Erro capturado automaticamente
        solo = Solo(nome="Teste", peso_especifico=-10)  # ValueError!
        ```
        
        #### 1.2 Documentação Integrada
        ```python
        help(Solo)  # Mostra todos os campos e tipos
        solo.__annotations__  # Mostra anotações de tipo
        ```
        
        #### 1.3 Imutabilidade (Opcional)
        ```python
        @dataclass(frozen=True)
        class SoloImutavel:
            # Não pode ser modificado após criação
            nome: str
            peso_especifico: float
        ```
        
        ### 2. Padrões de Uso
        
        #### 2.1 Criação
        ```python
        # Com todos os parâmetros
        solo1 = Solo(
            nome="Areia Média",
            peso_especifico=18.5,
            angulo_atrito=32.0,
            coesao=0.0,
            coeficiente_poisson=0.3
        )
        
        # Com valores padrão
        solo2 = Solo(nome="Argila", peso_especifico=17.0)
        ```
        
        #### 2.2 Serialização
        ```python
        # Para JSON
        import json
        solo_dict = solo1.__dict__
        solo_json = json.dumps(solo_dict)
        
        # Para DataFrame
        import pandas as pd
        df = pd.DataFrame([solo1.__dict__, solo2.__dict__])
        ```
        
        #### 2.3 Validação Avançada
        ```python
        @dataclass
        class SoloAvancado(Solo):
            def __post_init__(self):
                super().__post_init__()
                # Validações adicionais
                if self.angulo_atrito and self.angulo_atrito > 45:
                    raise ValueError("Ângulo de atrito muito alto")
        ```
        
        ### 3. Integração com Streamlit
        
        #### 3.1 Na Barra Lateral
        ```python
        # Atualizar objeto Solo conforme sliders
        solo_atual = Solo(
            nome="Solo Atual",
            peso_especifico=st.session_state.soil_params['gamma'],
            angulo_atrito=st.session_state.soil_params['phi'],
            coesao=st.session_state.soil_params['c']
        )
        ```
        
        #### 3.2 Em Análises
        ```python
        # Passar objetos para funções
        resultado = calcular_capacidade_carga(solo_atual, fundacao_atual)
        
        # Acessar propriedades
        st.write(f"Coesão: {solo_atual.coesao} kPa")
        st.write(f"Largura: {fundacao_atual.largura} m")
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
    🏗️ Simulador Solo-Fundações v2.1.0 | 
    Refatorado com dataclasses | 
    {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)

if __name__ == "__main__":
    main()
