# 2. Criar arquivo: relatorio_abnt.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image, PageBreak, ListFlowable, 
    ListItem, PageTemplate, Frame, NextPageTemplate
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

class RelatorioABNT:
    """Gerador de relatórios no padrão ABNT para TCC"""
    
    def __init__(self, titulo: str, autor: str, instituicao: str):
        self.titulo = titulo
        self.autor = autor
        self.instituicao = instituicao
        self.data = datetime.now().strftime("%d/%m/%Y")
        
        # Registrar fontes (se necessário)
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        except:
            pass  # Usar fontes padrão
        
        # Configurar estilos ABNT
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
        
    def _configurar_estilos(self):
        """Configura estilos de acordo com ABNT"""
        # Estilo para título do trabalho
        self.styles.add(ParagraphStyle(
            name='TituloTCC',
            parent=self.styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Estilo para equações
        self.styles.add(ParagraphStyle(
            name='Equacao',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6,
            fontName='Helvetica-Italic'
        ))
        
        # Estilo para legenda de figuras
        self.styles.add(ParagraphStyle(
            name='LegendaFigura',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=12,
            fontName='Helvetica-Oblique'
        ))
    
    def gerar_capa(self) -> list:
        """Gera a capa do relatório no padrão ABNT"""
        elementos = []
        
        # Espaçamento inicial
        elementos.append(Spacer(1, 3*cm))
        
        # Nome da instituição
        elementos.append(Paragraph(
            self.instituicao,
            ParagraphStyle(
                name='Instituicao',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=2*cm
            )
        ))
        
        # Título do trabalho
        elementos.append(Paragraph(
            self.titulo,
            self.styles['TituloTCC']
        ))
        
        # Espaçamento
        elementos.append(Spacer(1, 5*cm))
        
        # Nome do autor
        elementos.append(Paragraph(
            self.autor,
            ParagraphStyle(
                name='Autor',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=2*cm
            )
        ))
        
        # Local e data
        elementos.append(Paragraph(
            f"São Paulo, {self.data}",
            ParagraphStyle(
                name='LocalData',
                fontSize=10,
                alignment=TA_CENTER,
                spaceAfter=0
            )
        ))
        
        return elementos
    
    def gerar_sumario(self, secoes: List[Dict]) -> list:
        """Gera sumário automático"""
        elementos = []
        
        elementos.append(Paragraph(
            "SUMÁRIO",
            ParagraphStyle(
                name='TituloSumario',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=1*cm,
                fontName='Helvetica-Bold'
            )
        ))
        
        # Adicionar itens do sumário
        for secao in secoes:
            # Usar tabulação para alinhar números de página
            texto = f"{secao['titulo']} ................................................................. {secao['pagina']}"
            elementos.append(Paragraph(
                texto,
                ParagraphStyle(
                    name='ItemSumario',
                    fontSize=10,
                    alignment=TA_LEFT,
                    leftIndent=0,
                    rightIndent=0,
                    spaceAfter=3
                )
            ))
        
        elementos.append(PageBreak())
        return elementos
    
    def gerar_introducao(self) -> list:
        """Gera introdução padrão"""
        elementos = []
        
        elementos.append(Paragraph(
            "1 INTRODUÇÃO",
            self.styles['Subtitulo']
        ))
        
        elementos.append(Paragraph(
            "Este relatório apresenta os resultados das análises geotécnicas realizadas "
            "utilizando o software SimulaSolo, desenvolvido como parte do trabalho de "
            "conclusão de curso de Engenharia Civil.",
            self.styles['TextoNormal']
        ))
        
        elementos.append(Paragraph(
            "O objetivo principal deste trabalho é fornecer uma ferramenta computacional "
            "para auxiliar no dimensionamento de fundações e análise de tensões no solo, "
            "seguindo as normas técnicas brasileiras vigentes.",
            self.styles['TextoNormal']
        ))
        
        return elementos
    
    def adicionar_tabela_resultados(self, dados: pd.DataFrame, titulo: str) -> list:
        """Adiciona uma tabela de resultados formatada"""
        elementos = []
        
        # Título da tabela
        elementos.append(Paragraph(
            titulo,
            ParagraphStyle(
                name='TituloTabela',
                fontSize=10,
                alignment=TA_LEFT,
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
        ))
        
        # Converter DataFrame para lista para o ReportLab
        table_data = [dados.columns.tolist()] + dados.values.tolist()
        
        # Criar tabela
        tabela = Table(table_data, repeatRows=1)
        
        # Estilizar tabela
        estilo = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        tabela.setStyle(estilo)
        elementos.append(tabela)
        
        return elementos
    
    def adicionar_figura(self, figura_path: str, legenda: str, largura=15*cm) -> list:
        """Adiciona uma figura ao relatório"""
        elementos = []
        
        try:
            # Adicionar imagem
            img = Image(figura_path, width=largura, height=largura*0.75)
            elementos.append(img)
            
            # Adicionar legenda
            elementos.append(Paragraph(
                f"Figura: {legenda}",
                self.styles['LegendaFigura']
            ))
            
        except:
            # Em caso de erro, adicionar placeholder
            elementos.append(Paragraph(
                f"[Figura não disponível: {legenda}]",
                self.styles['LegendaFigura']
            ))
        
        return elementos
    
    def gerar_conclusao(self) -> list:
        """Gera conclusão do relatório"""
        elementos = []
        
        elementos.append(Paragraph(
            "5 CONCLUSÕES",
            self.styles['Subtitulo']
        ))
        
        elementos.append(Paragraph(
            "Com base nas análises realizadas, podem-se tirar as seguintes conclusões:",
            self.styles['TextoNormal']
        ))
        
        # Lista de conclusões
        conclusoes = [
            "Os resultados obtidos estão em conformidade com as normas técnicas brasileiras",
            "O software desenvolvido se mostrou eficaz para análises geotécnicas preliminares",
            "Os métodos implementados apresentaram coerência com resultados de referência",
            "A ferramenta pode ser utilizada para auxiliar no dimensionamento de fundações"
        ]
        
        lista_itens = []
        for conclusao in conclusoes:
            lista_itens.append(ListItem(
                Paragraph(conclusao, self.styles['TextoNormal']),
                leftIndent=20
            ))
        
        elementos.append(ListFlowable(
            lista_itens,
            bulletType='bullet',
            start='•'
        ))
        
        return elementos
    
    def gerar_referencias(self) -> list:
        """Gera referências bibliográficas no padrão ABNT"""
        elementos = []
        
        elementos.append(Paragraph(
            "REFERÊNCIAS BIBLIOGRÁFICAS",
            ParagraphStyle(
                name='TituloReferencias',
                fontSize=12,
                alignment=TA_CENTER,
                spaceBefore=2*cm,
                spaceAfter=1*cm,
                fontName='Helvetica-Bold'
            )
        ))
        
        referencias = [
            "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 6122: Projeto e execução de fundações. Rio de Janeiro, 2019.",
            "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 6118: Projeto de estruturas de concreto. Rio de Janeiro, 2014.",
            "VARGAS, M. Fundamentos de Engenharia Geotécnica. São Paulo: Edgar Blücher, 2017.",
            "CAPUTO, H. P. Mecânica dos Solos e suas Aplicações. Rio de Janeiro: LTC, 2018.",
            "PINTO, C. S. Curso Básico de Mecânica dos Solos. São Paulo: Oficina de Textos, 2020."
        ]
        
        for ref in referencias:
            elementos.append(Paragraph(
                ref,
                ParagraphStyle(
                    name='Referencia',
                    fontSize=9,
                    alignment=TA_JUSTIFY,
                    leftIndent=0,
                    firstLineIndent=0,
                    spaceAfter=3
                )
            ))
        
        return elementos
    
    def gerar_relatorio_completo(self, resultados: Dict, figuras: List[str], 
                                output_path: str = "relatorio_tcc.pdf"):
        """Gera o relatório completo em PDF"""
        
        # Criar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Construir conteúdo
        story = []
        
        # 1. Capa
        story.extend(self.gerar_capa())
        story.append(PageBreak())
        
        # 2. Sumário (simulado - na prática você calcularia as páginas)
        secoes_simuladas = [
            {'titulo': '1 INTRODUÇÃO', 'pagina': 3},
            {'titulo': '2 METODOLOGIA', 'pagina': 4},
            {'titulo': '3 RESULTADOS', 'pagina': 5},
            {'titulo': '4 ANÁLISE DOS RESULTADOS', 'pagina': 7},
            {'titulo': '5 CONCLUSÕES', 'pagina': 9},
            {'titulo': 'REFERÊNCIAS', 'pagina': 10}
        ]
        story.extend(self.gerar_sumario(secoes_simuladas))
        
        # 3. Introdução
        story.extend(self.gerar_introducao())
        
        # 4. Adicionar resultados
        story.append(Paragraph(
            "3 RESULTADOS",
            self.styles['Subtitulo']
        ))
        
        # Adicionar tabelas de resultados
        if 'tabelas' in resultados:
            for tabela in resultados['tabelas']:
                story.extend(self.adicionar_tabela_resultados(
                    tabela['dados'], tabela['titulo']
                ))
        
        # 5. Adicionar figuras
        story.append(Paragraph(
            "4 ANÁLISE DOS RESULTADOS",
            self.styles['Subtitulo']
        ))
        
        for i, figura in enumerate(figuras, 1):
            story.extend(self.adicionar_figura(
                figura, f"Resultado gráfico {i} - Análise de tensões"
            ))
        
        # 6. Conclusão
        story.extend(self.gerar_conclusao())
        
        # 7. Referências
        story.extend(self.gerar_referencias())
        
        # Gerar PDF
        doc.build(story)
        
        return output_path