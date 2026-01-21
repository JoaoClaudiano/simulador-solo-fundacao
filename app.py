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

# Rodapé
st.divider()
st.caption("Desenvolvido para TCC em Engenharia Civil | Python + Streamlit")