"""
Utilitários para exportação de resultados
"""
import pandas as pd
import plotly.io as pio
from datetime import datetime

def export_to_csv(results_dict, filename=None):
    """Exporta resultados para CSV"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados_{timestamp}.csv"
    
    df = pd.DataFrame([results_dict])
    df.to_csv(filename, index=False)
    return filename

def export_plotly_fig(fig, filename=None):
    """Exporta gráfico Plotly para HTML"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grafico_{timestamp}.html"
    
    pio.write_html(fig, filename)
    return filename