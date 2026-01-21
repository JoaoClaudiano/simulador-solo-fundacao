import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador Solo-Fundações", layout="wide")
st.title("🏗️ Simulador Interativo de Solo e Fundações")

# Sidebar com parâmetros
with st.sidebar:
    st.header("📐 Parâmetros do Solo")
    cohesion = st.slider("Coesão (c - kPa)", 0.0, 100.0, 10.0, 0.1)
    friction = st.slider("Ângulo de Atrito (φ - graus)", 0.0, 45.0, 30.0, 0.1)
    unit_weight = st.slider("Peso Específico (γ - kN/m³)", 10.0, 25.0, 18.0, 0.1)

# Cálculo básico de capacidade de carga (Terzaghi simplificado)
Nq = np.exp(np.pi * np.tan(np.radians(friction))) * (np.tan(np.radians(45 + friction/2)))**2
Nc = (Nq - 1) / np.tan(np.radians(friction)) if friction > 0 else 5.14
Nγ = 2 * (Nq + 1) * np.tan(np.radians(friction))

# Layout principal
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Resultados")
    st.metric("Fator Nq", f"{Nq:.2f}")
    st.metric("Fator Nc", f"{Nc:.2f}")
    st.metric("Fator Nγ", f"{Nγ:.2f}")

with col2:
    st.subheader("📈 Círculo de Mohr")
    # Cálculo das tensões principais
    sigma1 = 100  # Valor exemplo
    sigma3 = 50   # Valor exemplo
    center = (sigma1 + sigma3) / 2
    radius = (sigma1 - sigma3) / 2
    
    # Criar círculo de Mohr com Plotly
    theta = np.linspace(0, 2*np.pi, 100)
    x_circle = center + radius * np.cos(theta)
    y_circle = radius * np.sin(theta)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_circle, y=y_circle, mode='lines', name='Círculo'))
    fig.add_trace(go.Scatter(x=[sigma1, sigma3], y=[0, 0], mode='markers', 
                           marker=dict(size=10), name='Tensões Principais'))
    
    fig.update_layout(title="Círculo de Mohr", xaxis_title="Tensão Normal", 
                     yaxis_title="Tensão Cisalhante")
    st.plotly_chart(fig)

# ====================== NOVAS IMPORTACOES ======================
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src import foundation_calculations as fc

# ====================== SEÇÃO DE FUNDAÇÕES ======================

st.header("🏗️ Módulo de Fundações")

tab1, tab2, tab3 = st.tabs(["📐 Sapatas (Rasas)", "📏 Estacas (Profundas)", "📊 Comparativo"])

with tab1:
    st.subheader("Análise de Sapatas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Parâmetros da Sapata**")
        B = st.number_input("Largura B (m)", 0.5, 10.0, 1.5, 0.1)
        L = st.number_input("Comprimento L (m)", 0.5, 10.0, 1.5, 0.1)
        D_f = st.number_input("Profundidade D_f (m)", 0.0, 5.0, 1.0, 0.1)
        foundation_shape = st.selectbox("Forma", ["strip", "square", "circular"])
        
        st.markdown("**Carregamento**")
        q_applied = st.number_input("Pressão aplicada (kPa)", 50, 5000, 200, 10)
    
    with col2:
        st.markdown("**Parâmetros do Solo**")
        c = st.slider("Coesão c (kPa)", 0.0, 200.0, 10.0, 0.1)
        phi = st.slider("Ângulo φ (graus)", 0.0, 45.0, 30.0, 0.1)
        gamma = st.slider("Peso γ (kN/m³)", 10.0, 25.0, 18.0, 0.1)
        E_s = st.number_input("Módulo Es (MPa)", 10, 500, 50, 10) * 1000  # converter para kPa
        mu = st.slider("Coeficiente de Poisson ν", 0.2, 0.5, 0.3, 0.01)
    
    if st.button("Calcular Sapata", type="primary"):
        # Cálculos
        q_ult, (Nc, Nq, Nγ) = fc.bearing_capacity_terzaghi(
            c, phi, gamma, B, L, D_f, foundation_shape
        )
        
        settlement = fc.elastic_settlement(
            q_applied, B, E_s, mu, 
            'rectangular' if foundation_shape != 'circular' else 'circular',
            L/B if L != 0 else 1.0
        )
        
        FS, is_safe = fc.safety_factor(q_ult, q_applied)
        
        # Bulbo de tensões
        X, Z, stress_ratio = fc.stress_bulb(B, L)
        
        # Resultados
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("Capacidade Última", f"{q_ult:.0f} kPa")
            st.metric("Fator Nq", f"{Nq:.2f}")
        with col_res2:
            st.metric("Fator de Segurança", f"{FS:.2f}")
            st.metric("Fator Nγ", f"{Nγ:.2f}")
        with col_res3:
            st.metric("Recalque Estimado", f"{settlement*1000:.1f} mm")
            st.metric("Fator Nc", f"{Nc:.2f}")
        
        # Visualização do bulbo
        st.subheader("📈 Bulbo de Tensões")
        fig = go.Figure(data=
            go.Contour(
                z=stress_ratio*100,  # em porcentagem
                x=X[0,:],
                y=Z[:,0],
                colorscale='Viridis',
                contours=dict(
                    start=0,
                    end=100,
                    size=10
                ),
                colorbar=dict(title="Δσ/q (%)")
            )
        )
        
        fig.update_layout(
            title="Distribuição de Tensões no Solo",
            xaxis_title="Distância do centro (m)",
            yaxis_title="Profundidade (m)",
            yaxis=dict(autorange='reversed')  # Profundidade para baixo
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Relatório
        with st.expander("📄 Ver Relatório Completo"):
            params = {
                'Largura B': B, 'Comprimento L': L, 'Profundidade D_f': D_f,
                'Coesão c': c, 'Ângulo φ': phi, 'Peso γ': gamma
            }
            results = {
                'Capacidade última q_ult': q_ult,
                'Fatores (Nc, Nq, Nγ)': (Nc, Nq, Nγ),
                'Recalque estimado': settlement,
                'Fator de segurança FS': FS,
                'is_safe': is_safe
            }
            report = fc.generate_report('shallow', params, results)
            st.text(report)

with tab2:
    st.subheader("Análise de Estacas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Parâmetros da Estaca**")
        pile_dia = st.number_input("Diâmetro (m)", 0.3, 2.0, 0.5, 0.1)
        pile_length = st.number_input("Comprimento (m)", 5.0, 50.0, 15.0, 1.0)
        pile_type = st.selectbox("Tipo", ["driven", "bored"])
        load_applied = st.number_input("Carga aplicada (kN)", 100, 10000, 1500, 100)
        
        # Camadas de solo (simplificado - 3 camadas)
        st.markdown("**Perfil do Solo**")
        layers = []
        
        st.write("Camada 1 (Superior):")
        c1 = st.number_input("c1 (kPa)", 0.0, 100.0, 5.0, 1.0)
        phi1 = st.number_input("φ1 (graus)", 0.0, 40.0, 28.0, 1.0)
        gamma1 = st.number_input("γ1 (kN/m³)", 15.0, 22.0, 18.0, 0.1)
        depth1 = st.number_input("Espessura (m)", 1.0, pile_length/2, 5.0, 1.0)
        
        layers.append({
            'depth_top': 0,
            'depth_bottom': depth1,
            'c': c1,
            'phi': phi1,
            'gamma': gamma1
        })
    
    with col2:
        # Cálculo e visualização
        if st.button("Analisar Estaca", type="primary"):
            # Adicionar mais camadas (simplificado)
            # Camada 2 (intermediária)
            layers.append({
                'depth_top': depth1,
                'depth_bottom': depth1 + 5,
                'c': c1 * 1.5,  # Aumento simplificado
                'phi': phi1 + 2,
                'gamma': gamma1 + 1
            })
            
            # Camada 3 (de ponta)
            layers.append({
                'depth_top': depth1 + 5,
                'depth_bottom': pile_length + 5,  # Garantir que cubra a ponta
                'c': c1 * 2,
                'phi': phi1 + 5,
                'gamma': gamma1 + 2
            })
            
            # Cálculos
            total_capacity, shaft_capacity, tip_capacity = fc.pile_ultimate_capacity(
                layers, pile_dia, pile_length, pile_type
            )
            
            settlement, breakdown = fc.pile_settlement(
                load_applied, shaft_capacity, tip_capacity,
                pile_dia, pile_length, 50000  # Es simplificado
            )
            
            FS, is_safe = fc.safety_factor(total_capacity, load_applied, 2.0)
            
            # Resultados
            st.markdown("### 📊 Resultados")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("Capacidade Total", f"{total_capacity:.0f} kN")
                st.metric("Atrito Lateral", f"{shaft_capacity:.0f} kN")
                st.metric("Recalque", f"{settlement*1000:.1f} mm")
            with col_res2:
                st.metric("Capacidade de Ponta", f"{tip_capacity:.0f} kN")
                st.metric("Fator de Segurança", f"{FS:.2f}")
                
                if is_safe:
                    st.success("✅ Estaca segura para a carga aplicada")
                else:
                    st.warning("⚠️  Capacidade insuficiente - aumentar comprimento/diâmetro")
            
            # Visualização do perfil
            st.subheader("📈 Perfil da Estaca e Capacidades")
            
            # Criar visualização simplificada
            fig = go.Figure()
            
            # Adicionar camadas de solo
            colors = ['#8B4513', '#D2691E', '#A0522D']
            for i, layer in enumerate(layers):
                fig.add_trace(go.Scatter(
                    x=[0, 1, 1, 0],
                    y=[-layer['depth_top'], -layer['depth_top'], 
                       -layer['depth_bottom'], -layer['depth_bottom']],
                    fill='toself',
                    fillcolor=colors[i % len(colors)],
                    opacity=0.6,
                    line=dict(width=0),
                    name=f"Camada {i+1}"
                ))
            
            # Adicionar estaca
            fig.add_trace(go.Scatter(
                x=[0.4, 0.6, 0.6, 0.4],
                y=[0, 0, -pile_length, -pile_length],
                fill='toself',
                fillcolor='gray',
                opacity=0.8,
                line=dict(color='black', width=2),
                name="Estaca"
            ))
            
            fig.update_layout(
                title="Perfil Geotécnico e Estaca",
                xaxis=dict(showticklabels=False, range=[0, 1]),
                yaxis=dict(title="Profundidade (m)", autorange='reversed'),
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Comparativo: Sapatas vs Estacas")
    
    st.write("""
    ### 📋 Análise Comparativa
    
    **Sapatas (Fundações Rasas):**
    - ✅ Mais econômicas para solos competentes
    - ✅ Execução mais rápida
    - ⚠️  Limitadas pela capacidade do solo superficial
    - ⚠️  Sensíveis a variações do lençol freático
    
    **Estacas (Fundações Profundas):**
    - ✅ Atravessam solos fracos
    - ✅ Menor recalque diferencial
    - ⚠️  Custo mais elevado
    - ⚠️  Necessidade de equipamentos especializados
    
    ### 🎯 Recomendação Inicial
    """)
    
    # Calculadora de recomendação simples
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        soil_strength = st.select_slider(
            "Resistência do solo superficial",
            options=["Muito Fraca", "Fraca", "Média", "Boa", "Excelente"],
            value="Média"
        )
    
    with col_rec2:
        water_table = st.select_slider(
            "Nível do lençol freático",
            options=["Muito Profundo", "Profundo", "Moderado", "Raso", "Superficial"],
            value="Moderado"
        )
    
    if st.button("Obter Recomendação"):
        # Lógica simplificada de recomendação
        strength_score = {"Muito Fraca": 1, "Fraca": 2, "Média": 3, "Boa": 4, "Excelente": 5}
        water_score = {"Superficial": 1, "Raso": 2, "Moderado": 3, "Profundo": 4, "Muito Profundo": 5}
        
        total_score = strength_score[soil_strength] + water_score[water_table]
        
        if total_score >= 7:
            recommendation = "SAPATAS"
            reason = "Solo superficial competente e condições favoráveis"
            color = "green"
        else:
            recommendation = "ESTACAS"
            reason = "Solo fraco ou condições desfavoráveis do lençol freático"
            color = "blue"
        
        st.markdown(f"""
        <div style='padding: 20px; border-radius: 10px; background-color: {color}20; border-left: 5px solid {color};'>
            <h3 style='color: {color};'>Recomendação: {recommendation}</h3>
            <p><strong>Motivo:</strong> {reason}</p>
            <p><strong>Pontuação:</strong> {total_score}/10</p>
        </div>
        """, unsafe_allow_html=True)




# Rodapé
st.divider()
st.caption("Desenvolvido para TCC em Engenharia Civil | Python + Streamlit")