"""
Sistema completo de exportação de resultados
para CSV, Excel, PDF e relatórios técnicos
"""
import pandas as pd
import numpy as np
import plotly.io as pio
import json
import base64
from datetime import datetime
from pathlib import Path
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

class ExportSystem:
    """Sistema avançado de exportação de resultados"""
    
    def __init__(self, output_dir="exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def _generate_filename(self, prefix, extension):
        """Gera nome de arquivo único com timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.{extension}"
    
    def export_to_csv(self, data_dict, filename=None):
        """
        Exporta dados para CSV
        
        Args:
            data_dict: Dicionário ou lista de dicionários
            filename: Nome personalizado (opcional)
            
        Returns:
            Path do arquivo criado
        """
        if filename is None:
            filename = self._generate_filename("dados", "csv")
        
        # Converter para DataFrame
        if isinstance(data_dict, dict):
            # Um único registro
            df = pd.DataFrame([data_dict])
        elif isinstance(data_dict, list):
            # Múltiplos registros
            df = pd.DataFrame(data_dict)
        else:
            raise ValueError("data_dict deve ser dict ou list")
        
        # Salvar CSV
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return filename
    
    def export_to_excel(self, data_dicts, sheet_names=None, filename=None):
        """
        Exporta para Excel com múltiplas planilhas
        
        Args:
            data_dicts: Lista de DataFrames ou dicionários
            sheet_names: Nomes das planilhas
            filename: Nome do arquivo
            
        Returns:
            Path do arquivo criado
        """
        if filename is None:
            filename = self._generate_filename("relatorio", "xlsx")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for i, data in enumerate(data_dicts):
                # Determinar nome da planilha
                sheet_name = sheet_names[i] if sheet_names else f"Dados_{i+1}"
                
                # Converter para DataFrame se necessário
                if isinstance(data, dict):
                    df = pd.DataFrame([data])
                elif isinstance(data, pd.DataFrame):
                    df = data
                else:
                    df = pd.DataFrame(data)
                
                # Salvar na planilha
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Ajustar largura das colunas
                worksheet = writer.sheets[sheet_name]
                for column in df.columns:
                    max_length = max(
                        df[column].astype(str).apply(len).max(),
                        len(str(column))
                    )
                    worksheet.column_dimensions[
                        self._get_column_letter(df.columns.get_loc(column) + 1)
                    ].width = min(max_length + 2, 50)
        
        return filename
    
    def export_plotly_to_html(self, fig, filename=None, include_plotlyjs=True):
        """
        Exporta gráfico Plotly para HTML interativo
        
        Args:
            fig: Figura Plotly
            filename: Nome do arquivo
            include_plotlyjs: Incluir biblioteca Plotly no arquivo
            
        Returns:
            Path do arquivo criado
        """
        if filename is None:
            filename = self._generate_filename("grafico", "html")
        
        # Configurar template
        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
        }
        
        # Salvar HTML
        pio.write_html(
            fig, 
            file=filename,
            config=config,
            include_plotlyjs=include_plotlyjs,
            auto_open=False,
            full_html=True
        )
        
        return filename
    
    def export_to_pdf_report(self, title, sections, filename=None):
        """
        Gera relatório PDF profissional
        
        Args:
            title: Título do relatório
            sections: Lista de seções com conteúdo
            filename: Nome do arquivo
            
        Returns:
            Path do arquivo criado
        """
        if filename is None:
            filename = self._generate_filename("relatorio_tecnico", "pdf")
        
        with PdfPages(filename) as pdf:
            # Página 1: Capa
            fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4
            ax.axis('off')
            
            # Título
            ax.text(0.5, 0.7, title, 
                   ha='center', va='center', 
                   fontsize=24, fontweight='bold')
            
            # Subtítulo
            ax.text(0.5, 0.6, "Relatório Técnico - Análise Geotécnica",
                   ha='center', va='center', 
                   fontsize=16)
            
            # Data
            ax.text(0.5, 0.4, datetime.now().strftime("%d/%m/%Y %H:%M"),
                   ha='center', va='center',
                   fontsize=12)
            
            # Rodapé
            ax.text(0.5, 0.1, "Gerado por Simulador Solo-Fundações",
                   ha='center', va='center',
                   fontsize=10, style='italic')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Páginas de conteúdo
            for section in sections:
                fig, ax = plt.subplots(figsize=(8.27, 11.69))
                ax.axis('off')
                
                # Título da seção
                ax.text(0.1, 0.95, section.get('title', 'Seção'),
                       fontsize=16, fontweight='bold')
                
                # Conteúdo
                y_position = 0.85
                for content in section.get('content', []):
                    if isinstance(content, str):
                        # Texto
                        ax.text(0.1, y_position, content,
                               fontsize=10, wrap=True,
                               transform=ax.transAxes)
                        y_position -= 0.05
                    elif isinstance(content, dict) and 'table' in content:
                        # Tabela
                        df = pd.DataFrame(content['table'])
                        table_text = df.to_string(index=False)
                        ax.text(0.1, y_position, table_text,
                               fontsize=8, fontfamily='monospace')
                        y_position -= len(df) * 0.02
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
        
        return filename
    
    def export_project_data(self, project_name, soil_data, foundation_data, 
                          results, figures=None):
        """
        Exporta projeto completo (dados + resultados)
        
        Returns:
            dict: Caminhos de todos arquivos exportados
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.output_dir / f"projeto_{project_name}_{timestamp}"
        project_dir.mkdir(exist_ok=True)
        
        exported_files = {}
        
        # 1. Dados do solo (JSON)
        soil_file = project_dir / "dados_solo.json"
        with open(soil_file, 'w', encoding='utf-8') as f:
            json.dump(soil_data, f, indent=2, ensure_ascii=False)
        exported_files['soil_data'] = soil_file
        
        # 2. Dados da fundação (JSON)
        foundation_file = project_dir / "dados_fundacao.json"
        with open(foundation_file, 'w', encoding='utf-8') as f:
            json.dump(foundation_data, f, indent=2, ensure_ascii=False)
        exported_files['foundation_data'] = foundation_file
        
        # 3. Resultados (CSV)
        results_file = project_dir / "resultados.csv"
        pd.DataFrame([results]).to_csv(results_file, index=False)
        exported_files['results'] = results_file
        
        # 4. Gráficos (HTML)
        if figures:
            for i, fig in enumerate(figures):
                graph_file = project_dir / f"grafico_{i+1}.html"
                pio.write_html(fig, file=graph_file)
                exported_files[f'graph_{i+1}'] = graph_file
        
        # 5. Relatório consolidado (Excel)
        report_data = {
            'Parametros_Solo': pd.DataFrame([soil_data]),
            'Parametros_Fundacao': pd.DataFrame([foundation_data]),
            'Resultados': pd.DataFrame([results])
        }
        
        report_file = project_dir / "relatorio_consolidado.xlsx"
        with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
            for sheet_name, df in report_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        exported_files['consolidated_report'] = report_file
        
        # 6. README do projeto
        readme_content = f"""# Projeto: {project_name}
        
Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

## Arquivos incluídos:
- dados_solo.json: Parâmetros geotécnicos
- dados_fundacao.json: Geometria da fundação
- resultados.csv: Resultados da análise
- relatorio_consolidado.xlsx: Relatório em Excel
- graficos_*.html: Visualizações interativas

## Resumo:
Solo: c={soil_data.get('c', 'N/A')} kPa, φ={soil_data.get('phi', 'N/A')}°
Fundação: {foundation_data.get('type', 'N/A')}
Fator de segurança: {results.get('FS', 'N/A')}
"""
        
        readme_file = project_dir / "README.txt"
        readme_file.write_text(readme_content)
        exported_files['readme'] = readme_file
        
        return exported_files
    
    def create_download_link(self, filepath, link_text="Download"):
        """
        Cria link de download para Streamlit
        
        Args:
            filepath: Caminho do arquivo
            link_text: Texto do link
            
        Returns:
            HTML do link
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return "Arquivo não encontrado"
        
        with open(filepath, "rb") as f:
            data = f.read()
        
        b64 = base64.b64encode(data).decode()
        
        if filepath.suffix == '.html':
            mime_type = "text/html"
        elif filepath.suffix == '.csv':
            mime_type = "text/csv"
        elif filepath.suffix == '.json':
            mime_type = "application/json"
        elif filepath.suffix in ['.xlsx', '.xls']:
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filepath.suffix == '.pdf':
            mime_type = "application/pdf"
        else:
            mime_type = "application/octet-stream"
        
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filepath.name}">{link_text}</a>'
        return href
    
    def _get_column_letter(self, idx):
        """Converte índice de coluna para letra Excel (A, B, C...)"""
        letters = ''
        while idx >= 0:
            letters = chr(idx % 26 + 65) + letters
            idx = idx // 26 - 1
        return letters

# Exemplo de uso no Streamlit
def streamlit_export_ui():
    """
    Interface de exportação para Streamlit
    """
    import streamlit as st
    
    st.subheader("📤 Exportação de Resultados")
    
    # Coletar dados da sessão
    if 'analysis_results' in st.session_state:
        results = st.session_state.analysis_results
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Exportar CSV"):
                exporter = ExportSystem()
                csv_file = exporter.export_to_csv(results)
                st.markdown(exporter.create_download_link(csv_file, "📥 Baixar CSV"), 
                          unsafe_allow_html=True)
        
        with col2:
            if st.button("📊 Exportar Excel"):
                exporter = ExportSystem()
                
                # Criar múltiplas planilhas
                sheets = [
                    {"Parâmetros": results.get('parameters', {})},
                    {"Resultados": results.get('results', {})},
                    {"Segurança": results.get('safety', {})}
                ]
                
                excel_file = exporter.export_to_excel(sheets)
                st.markdown(exporter.create_download_link(excel_file, "📥 Baixar Excel"), 
                          unsafe_allow_html=True)
        
        with col3:
            if st.button("📄 Relatório PDF"):
                exporter = ExportSystem()
                
                sections = [
                    {
                        'title': 'Resumo da Análise',
                        'content': [
                            f"Data: {datetime.now().strftime('%d/%m/%Y')}",
                            f"Tipo de fundação: {results.get('foundation_type', 'N/A')}",
                            f"Fator de segurança: {results.get('FS', 'N/A'):.2f}"
                        ]
                    },
                    {
                        'title': 'Parâmetros do Solo',
                        'content': [
                            f"Coesão: {results.get('c', 'N/A')} kPa",
                            f"Ângulo de atrito: {results.get('phi', 'N/A')}°",
                            f"Peso específico: {results.get('gamma', 'N/A')} kN/m³"
                        ]
                    }
                ]
                
                pdf_file = exporter.export_to_pdf_report(
                    title="Relatório de Análise Geotécnica",
                    sections=sections
                )
                st.markdown(exporter.create_download_link(pdf_file, "📥 Baixar PDF"), 
                          unsafe_allow_html=True)
        
        # Exportação completa do projeto
        st.divider()
        project_name = st.text_input("Nome do projeto:", "Analise_Fundacao")
        
        if st.button("🚀 Exportar Projeto Completo", type="primary"):
            exporter = ExportSystem()
            
            # Dados de exemplo
            soil_data = {
                'c': results.get('c', 0),
                'phi': results.get('phi', 0),
                'gamma': results.get('gamma', 18),
                'description': 'Solo da análise'
            }
            
            foundation_data = {
                'type': results.get('foundation_type', 'sapata'),
                'width': results.get('B', 1.5),
                'length': results.get('L', 1.5),
                'depth': results.get('D_f', 1.0)
            }
            
            exported = exporter.export_project_data(
                project_name=project_name,
                soil_data=soil_data,
                foundation_data=foundation_data,
                results=results,
                figures=st.session_state.get('figures', [])
            )
            
            st.success(f"✅ Projeto exportado com {len(exported)} arquivos")
            
            # Links para download
            for name, filepath in exported.items():
                st.markdown(f"**{name}:** {exporter.create_download_link(filepath)}", 
                          unsafe_allow_html=True)
    else:
        st.warning("⚠️ Execute uma análise primeiro para exportar resultados")

if __name__ == "__main__":
    # Teste do sistema de exportação
    exporter = ExportSystem()
    
    # Dados de teste
    test_data = {
        'c': 10,
        'phi': 30,
        'gamma': 18,
        'B': 1.5,
        'q_ult': 785.4,
        'FS': 3.14,
        'settlement': 0.0123
    }
    
    # Exportar CSV
    csv_file = exporter.export_to_csv(test_data)
    print(f"CSV exportado: {csv_file}")
    
    # Exportar Excel
    excel_file = exporter.export_to_excel([test_data, test_data])
    print(f"Excel exportado: {excel_file}")