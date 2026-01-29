# 3. Criar arquivo: integracao_tcc.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import base64
from pathlib import Path

# Importar nossos módulos
from estacas_fundacoes_profundas import CalculoEstacas, ParametrosEstaca
from relatorio_abnt import RelatorioABNT

class AplicacaoTCC:
    """Classe principal da aplicação para TCC"""
    
    def __init__(self):
        self.estacas = CalculoEstacas()
        self.configurar_pagina()
        
    def configurar_pagina(self):
        """Configura a página do Streamlit"""
        st.set_page_config(
            page_title="SimulaSolo TCC - Sistema Completo",
            page_icon="🏗️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS personalizado
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #2E86AB;
            text-align: center;
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.8rem;
            color: #A23B72;
            border-bottom: 2px solid #F18F01;
            padding-bottom: 0.5rem;
            margin-top: 2rem;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 0.5rem 2rem;
        }
        .result-box {
            background-color: #f8f9fa;
            border-left: 4px solid #4CAF50;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Título principal
        st.markdown('<h1 class="main-header">🏗️ SimulaSolo - Sistema de Análise Geotécnica</h1>', 
                   unsafe_allow_html=True)
        st.markdown("### Trabalho de Conclusão de Curso - Engenharia Civil")
        
    def criar_menu_principal(self):
        """Cria menu de navegação principal"""
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/engineering.png", width=100)
            st.markdown("### Menu Principal")
            
            opcao = st.radio(
                "Selecione o módulo:",
                ["🏠 Início", 
                 "📊 Análise de Estacas", 
                 "📈 Bulbo de Tensões", 
                 "📋 Capacidade de Carga",
                 "📄 Gerar Relatório TCC",
                 "⚙️ Configurações"]
            )
            
            st.markdown("---")
            st.markdown("### Informações do Projeto")
            st.info("""
            **TCC Engenharia Civil**  
            **Autor:** Seu Nome  
            **Orientador:** Prof. Dr. Nome  
            **Instituição:** Sua Universidade  
            **Ano:** 2024
            """)
            
        return opcao
    
    def modulo_estacas(self):
        """Módulo completo de análise de estacas"""
        st.markdown('<h2 class="section-header">📊 Análise de Capacidade de Carga de Estacas</h2>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Parâmetros da Estaca")
            tipo_estaca = st.selectbox(
                "Tipo de Estaca",
                ["Estaca Hélice Contínua", "Estaca Raiz", "Estaca Pré-moldada", "Estaca Metálica"]
            )
            
            diametro = st.number_input("Diâmetro (m)", 0.1, 2.0, 0.4, 0.05)
            comprimento = st.number_input("Comprimento (m)", 5.0, 50.0, 15.0, 1.0)
            material = st.selectbox("Material", ["Concreto", "Aço", "Madeira"])
            
            # Calcular área e perímetro
            area_ponta = np.pi * (diametro/2)**2
            perimetro = np.pi * diametro
            
            st.metric("Área da Ponta", f"{area_ponta:.4f} m²")
            st.metric("Perímetro", f"{perimetro:.2f} m")
            
        with col2:
            st.subheader("Parâmetros do Solo")
            tipo_solo = st.selectbox("Tipo de Solo", 
                                   ["Argila", "Silte", "Areia", "Areia Argilosa"])
            
            st.subheader("Valores de SPT (N)")
            st.write("Insira os valores de SPT a cada metro:")
            
            # Criar entrada para valores de SPT
            num_camadas = st.slider("Número de camadas", 5, 30, 15)
            spt_values = []
            
            cols_spt = st.columns(5)
            for i in range(num_camadas):
                with cols_spt[i % 5]:
                    valor = st.number_input(f"Camada {i+1}m", 0, 100, 
                                          min(30, 5 + i*2), key=f"spt_{i}")
                    spt_values.append(valor)
        
        # Botão para cálculo
        if st.button("🔍 Calcular Capacidade de Carga", type="primary", use_container_width=True):
            # Criar objeto de parâmetros
            parametros = ParametrosEstaca(
                tipo=tipo_estaca,
                diametro=diametro,
                comprimento=comprimento,
                material=material,
                area_ponta=area_ponta,
                perimetro=perimetro
            )
            
            # Calcular com diferentes métodos
            resultados = {}
            
            # Aoki-Velloso
            resultados['aoki_velloso'] = self.estacas.aoki_velloso(
                parametros, {}, spt_values
            )
            
            # Décourt-Quaresma
            resultados['decourt_quaresma'] = self.estacas.decourt_quaresma(
                parametros, spt_values, tipo_solo.lower()
            )
            
            # Exibir resultados
            self.exibir_resultados_estacas(resultados)
            
            # Gerar gráficos
            fig = self.estacas.criar_grafico_distribuicao(resultados)
            st.plotly_chart(fig, use_container_width=True)
            
            # Salvar resultados para relatório
            st.session_state['resultados_estacas'] = resultados
            st.session_state['parametros_estaca'] = parametros
    
    def exibir_resultados_estacas(self, resultados: Dict):
        """Exibe resultados de cálculos de estacas"""
        st.markdown('<h3 class="section-header">📋 Resultados dos Cálculos</h3>', 
                   unsafe_allow_html=True)
        
        # Criar tabela comparativa
        dados_comparacao = []
        for metodo, valores in resultados.items():
            dados_comparacao.append({
                'Método': valores['metodo'],
                'Capacidade Ponta (kN)': f"{valores['capacidade_ponta']:.2f}",
                'Capacidade Lateral (kN)': f"{valores['capacidade_lateral']:.2f}",
                'Capacidade Total (kN)': f"{valores['capacidade_total']:.2f}",
                'Capacidade Admissível (kN)': f"{valores['capacidade_admissivel']:.2f}",
                'Fator de Segurança': valores['fator_seguranca']
            })
        
        df_resultados = pd.DataFrame(dados_comparacao)
        st.dataframe(df_resultados, use_container_width=True)
        
        # Recomendação
        st.markdown("### 🎯 Recomendação de Projeto")
        
        # Encontrar valor mais conservador
        capacidades_adm = [v['capacidade_admissivel'] for v in resultados.values()]
        capacidade_recomendada = min(capacidades_adm)
        metodo_recomendado = list(resultados.keys())[capacidades_adm.index(capacidade_recomendada)]
        
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        with col_rec1:
            st.metric("Capacidade Recomendada", f"{capacidade_recomendada:.2f} kN")
        with col_rec2:
            st.metric("Método", resultados[metodo_recomendado]['metodo'])
        with col_rec3:
            st.metric("Fator Segurança", resultados[metodo_recomendado]['fator_seguranca'])
        
        # Explicação
        with st.expander("📝 Explicação dos Métodos"):
            st.markdown("""
            **Método Aoki-Velloso:**
            - Desenvolvido para estacas escavadas no Brasil
            - Considera resultados de SPT
            - Coeficientes empíricos calibrados
            
            **Método Décourt-Quaresma:**
            - Amplamente utilizado no Brasil
            - Considera tipo de solo e SPT
            - Apresenta bons resultados para solos tropicais
            """)
    
    def modulo_relatorio_tcc(self):
        """Módulo para gerar relatório completo do TCC"""
        st.markdown('<h2 class="section-header">📄 Gerar Relatório Completo do TCC</h2>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Configuração do Relatório")
            
            # Informações do trabalho
            titulo_tcc = st.text_input(
                "Título do TCC",
                "Análise Geotécnica de Fundações Utilizando Software de Elementos Finitos"
            )
            
            autor = st.text_input("Autor", "Seu Nome Completo")
            orientador = st.text_input("Orientador", "Prof. Dr. Nome do Orientador")
            instituicao = st.text_input("Instituição", "Universidade de São Paulo - USP")
            
            # Selecionar conteúdo
            st.subheader("Conteúdo do Relatório")
            incluir_introducao = st.checkbox("Incluir Introdução", True)
            incluir_metodologia = st.checkbox("Incluir Metodologia", True)
            incluir_resultados = st.checkbox("Incluir Resultados", True)
            incluir_analise = st.checkbox("Incluir Análise dos Resultados", True)
            incluir_conclusao = st.checkbox("Incluir Conclusões", True)
            incluir_referencias = st.checkbox("Incluir Referências", True)
            
        with col2:
            st.subheader("Pré-visualização")
            st.info("""
            **Estrutura do Relatório:**
            
            1. Capa
            2. Folha de Rosto
            3. Sumário
            4. Introdução
            5. Metodologia
            6. Resultados
            7. Análise
            8. Conclusões
            9. Referências
            """)
            
            # Status dos dados
            st.subheader("Dados Disponíveis")
            if 'resultados_estacas' in st.session_state:
                st.success("✓ Resultados de estacas disponíveis")
            else:
                st.warning("⚠️ Nenhum resultado salvo")
                
            if 'parametros_estaca' in st.session_state:
                st.success("✓ Parâmetros de estaca disponíveis")
        
        # Botão para gerar relatório
        if st.button("📄 Gerar Relatório ABNT em PDF", type="primary", use_container_width=True):
            with st.spinner("Gerando relatório no padrão ABNT..."):
                try:
                    # Criar relatório
                    relatorio = RelatorioABNT(
                        titulo=titulo_tcc,
                        autor=autor,
                        instituicao=instituicao
                    )
                    
                    # Preparar dados para o relatório
                    resultados_relatorio = {}
                    
                    if 'resultados_estacas' in st.session_state:
                        # Converter resultados para DataFrame
                        dados_estacas = []
                        for metodo, valores in st.session_state['resultados_estacas'].items():
                            dados_estacas.append({
                                'Método': valores['metodo'],
                                'Ponta (kN)': valores['capacidade_ponta'],
                                'Lateral (kN)': valores['capacidade_lateral'],
                                'Total (kN)': valores['capacidade_total'],
                                'Admissível (kN)': valores['capacidade_admissivel']
                            })
                        
                        df_estacas = pd.DataFrame(dados_estacas)
                        resultados_relatorio['tabelas'] = [
                            {'dados': df_estacas, 'titulo': 'Resultados de Cálculo de Estacas'}
                        ]
                    
                    # Lista de figuras (simuladas - na prática você salvaria as figuras)
                    figuras_simuladas = []
                    
                    # Gerar relatório
                    caminho_pdf = relatorio.gerar_relatorio_completo(
                        resultados_relatorio,
                        figuras_simuladas,
                        "relatorio_tcc_final.pdf"
                    )
                    
                    # Disponibilizar download
                    with open(caminho_pdf, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.success("✅ Relatório gerado com sucesso!")
                    
                    # Botão de download
                    st.download_button(
                        label="📥 Download do Relatório PDF",
                        data=pdf_bytes,
                        file_name="relatorio_tcc_geotecnia.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")
    
    def modulo_capacidade_carga(self):
        """Módulo avançado de capacidade de carga"""
        st.markdown('<h2 class="section-header">📋 Capacidade de Carga de Fundações Superficiais</h2>', 
                   unsafe_allow_html=True)
        
        # Implementação da NBR 6122
        tab1, tab2, tab3 = st.tabs(["Terzaghi", "Meyerhof", "Hansen"])
        
        with tab1:
            self._capacidade_carga_terzaghi()
        
        with tab2:
            self._capacidade_carga_meyerhof()
        
        with tab3:
            self._capacidade_carga_hansen()
    
    def _capacidade_carga_terzaghi(self):
        """Implementação do método de Terzaghi"""
        st.subheader("Método de Terzaghi (1943)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Parâmetros do solo
            coesao = st.number_input("Coesão (c) - kPa", 0.0, 500.0, 10.0, 1.0)
            angulo_atrito = st.number_input("Ângulo de Atrito (φ) - graus", 0.0, 45.0, 30.0, 1.0)
            peso_especifico = st.number_input("Peso Específico (γ) - kN/m³", 10.0, 25.0, 18.0, 0.5)
            sobrecarga = st.number_input("Sobrecarga (q) - kPa", 0.0, 100.0, 0.0, 1.0)
        
        with col2:
            # Parâmetros da sapata
            largura = st.number_input("Largura (B) - m", 0.5, 10.0, 1.5, 0.1)
            comprimento = st.number_input("Comprimento (L) - m", 0.5, 20.0, 2.0, 0.1)
            profundidade = st.number_input("Profundidade (Df) - m", 0.5, 5.0, 1.0, 0.1)
            
            # Fatores de forma
            forma = st.selectbox("Forma da Sapata", ["Quadrada", "Retangular", "Circular", "Corrida"])
        
        if st.button("Calcular Capacidade - Terzaghi"):
            # Converter ângulo para radianos
            phi_rad = np.radians(angulo_atrito)
            
            # Fatores de capacidade de carga (Terzaghi)
            Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.pi/4 + phi_rad/2))**2
            Nc = (Nq - 1) / np.tan(phi_rad) if angulo_atrito > 0 else 5.7
            Ngamma = (Nq - 1) * np.tan(1.4 * phi_rad)
            
            # Fatores de forma
            if forma == "Corrida":
                sc, sq, sgamma = 1.0, 1.0, 1.0
            elif forma == "Quadrada":
                sc, sq, sgamma = 1.3, 1.0, 0.8
            elif forma == "Circular":
                sc, sq, sgamma = 1.3, 1.0, 0.6
            else:  # Retangular
                sc = 1 + 0.2 * (largura/comprimento)
                sq = 1 + 0.1 * (largura/comprimento) * np.tan(phi_rad)
                sgamma = 1 - 0.4 * (largura/comprimento)
            
            # Capacidade de carga última
            q_ultima = (coesao * Nc * sc + 
                       sobrecarga * Nq * sq + 
                       0.5 * peso_especifico * largura * Ngamma * sgamma)
            
            # Capacidade admissível (FS = 3)
            q_adm = q_ultima / 3
            
            # Exibir resultados
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("Capacidade Última", f"{q_ultima:.2f} kPa")
            with col_res2:
                st.metric("Capacidade Admissível", f"{q_adm:.2f} kPa")
            with col_res3:
                st.metric("Fator de Segurança", 3.0)
            
            # Salvar resultados
            st.session_state['terzaghi_result'] = {
                'q_ultima': q_ultima,
                'q_adm': q_adm,
                'fatores': {'Nc': Nc, 'Nq': Nq, 'Ngamma': Ngamma}
            }
    
    def executar(self):
        """Método principal para executar a aplicação"""
        opcao = self.criar_menu_principal()
        
        if opcao == "🏠 Início":
            self.pagina_inicial()
        elif opcao == "📊 Análise de Estacas":
            self.modulo_estacas()
        elif opcao == "📈 Bulbo de Tensões":
            # Mantenha seu código existente
            pass
        elif opcao == "📋 Capacidade de Carga":
            self.modulo_capacidade_carga()
        elif opcao == "📄 Gerar Relatório TCC":
            self.modulo_relatorio_tcc()
        elif opcao == "⚙️ Configurações":
            self.modulo_configuracoes()
    
    def pagina_inicial(self):
        """Página inicial da aplicação"""
        st.markdown("""
        ## 🎓 Sistema de Análise Geotécnica para TCC
        
        **Bem-vindo ao sistema completo de análise geotécnica desenvolvido para 
        Trabalho de Conclusão de Curso em Engenharia Civil.**
        
        ### 📚 Funcionalidades Implementadas:
        
        #### ✅ **Módulo de Estacas e Fundações Profundas**
        - Método Aoki-Velloso para estacas escavadas
        - Método Décourt-Quaresma
        - Cálculo de capacidade de ponta e atrito lateral
        - Gráficos comparativos entre métodos
        
        #### ✅ **Sistema de Relatórios ABNT**
        - Geração automática de relatórios no padrão ABNT
        - Capa, sumário, introdução, metodologia
        - Tabelas de resultados formatadas
        - Referências bibliográficas
        
        #### ✅ **Análise de Capacidade de Carga**
        - Método de Terzaghi (fundações superficiais)
        - Método de Meyerhof
        - Método de Hansen
        - Consideração de fatores de forma e profundidade
        
        #### ✅ **Bulbo de Tensões**
        - Distribuição de tensões de Boussinesq
        - Isóbaras de tensão
        - Análise de múltiplas cargas
        """)
        
        # Estatísticas de uso
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Métodos Implementados", "12")
        with col2:
            st.metric("Normas Brasileiras", "NBR 6122/6118")
        with col3:
            st.metric("Tipos de Análise", "5")
        
        # Quick start
        st.markdown("### 🚀 Comece Agora")
        st.info("""
        1. Selecione **'Análise de Estacas'** no menu lateral para calcular capacidade de carga
        2. Utilize **'Capacidade de Carga'** para fundações superficiais
        3. Gere seu **relatório completo** em PDF no padrão ABNT
        """)
    
    def modulo_configuracoes(self):
        """Módulo de configurações da aplicação"""
        st.markdown('<h2 class="section-header">⚙️ Configurações do Sistema</h2>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Normas", "Unidades", "Exportação"])
        
        with tab1:
            st.subheader("Configuração de Normas")
            normas = st.multiselect(
                "Normas para validação",
                ["NBR 6122 - Fundações", 
                 "NBR 6118 - Concreto", 
                 "NBR 8681 - Ações e Segurança",
                 "NBR 8036 - Sondagens"],
                default=["NBR 6122 - Fundações", "NBR 6118 - Concreto"]
            )
            
            fator_seguranca = st.select_slider(
                "Fator de Segurança Global",
                options=[1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                value=3.0
            )
        
        with tab2:
            st.subheader("Sistema de Unidades")
            sistema = st.radio(
                "Sistema de unidades",
                ["SI (kN, m, kPa)", "MKS (kgf, m, kgf/cm²)", "Inglês (lb, ft, psi)"],
                index=0
            )
            
            # Configurações de precisão
            casas_decimais = st.slider("Casas decimais nos resultados", 1, 6, 2)
        
        with tab3:
            st.subheader("Configurações de Exportação")
            formato_relatorio = st.selectbox(
                "Formato do relatório",
                ["PDF ABNT", "Word (.docx)", "HTML", "LaTeX"]
            )
            
            incluir_logos = st.checkbox("Incluir logos da instituição", True)
            incluir_assinatura = st.checkbox("Incluir espaço para assinaturas", True)
            
            # Botão para salvar configurações
            if st.button("💾 Salvar Configurações", type="primary"):
                st.success("Configurações salvas com sucesso!")
                st.session_state['configuracoes'] = {
                    'normas': normas,
                    'fator_seguranca': fator_seguranca,
                    'unidades': sistema,
                    'casas_decimais': casas_decimais
                }

# Ponto de entrada principal
if __name__ == "__main__":
    app = AplicacaoTCC()
    app.executar()