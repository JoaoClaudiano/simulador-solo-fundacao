from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np

@dataclass
class Solo:
    """Modela os parâmetros geotécnicos de um solo."""
    nome: str
    peso_especifico: float  # kN/m³
    angulo_atrito: Optional[float] = None  # graus
    coesao: Optional[float] = None  # kPa
    modulo_elasticidade: Optional[float] = None  # MPa
    coeficiente_poisson: Optional[float] = 0.3  # adimensional

    def __post_init__(self):
        """Validação básica dos dados."""
        if self.peso_especifico <= 0:
            raise ValueError("Peso específico deve ser positivo")
        if self.coeficiente_poisson is not None and not (0 <= self.coeficiente_poisson < 0.5):
            raise ValueError("Coeficiente de Poisson deve estar entre 0 e 0.5")

@dataclass
class Fundacao:
    """Modela as características de uma fundação superficial."""
    largura: float  # m (B)
    comprimento: float  # m (L)
    carga: float  # kN/m² (q)

    def __post_init__(self):
        if self.largura <= 0 or self.comprimento <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")
        if self.carga < 0:
            raise ValueError("Carga não pode ser negativa")

@dataclass
class ResultadoAnalise:
    """Estrutura para organizar os resultados da análise."""
    coordenadas: np.ndarray  # Malha de pontos (x, y, z)
    tensoes: np.ndarray  # Valores de Δσz correspondentes
    parametros_entrada: Dict[str, Any]  # Dicionário com todos os inputs
