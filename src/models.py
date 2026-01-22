from dataclasses import dataclass
from typing import Optional

@dataclass
class Solo:
    """Modela os parâmetros geotécnicos de um solo."""
    nome: str
    peso_especifico: float  # kN/m³
    angulo_atrito: Optional[float] = None  # graus
    coesao: Optional[float] = None  # kPa
    modulo_elasticidade: Optional[float] = None  # MPa
    
    def __post_init__(self):
        """Validação básica dos dados."""
        if self.peso_especifico <= 0:
            raise ValueError("Peso específico deve ser positivo")

@dataclass
class Fundacao:
    """Modela as características de uma fundação superficial."""
    largura: float  # m
    comprimento: float  # m
    carga: float  # kN/m²
    
    def __post_init__(self):
        if self.largura <= 0 or self.comprimento <= 0:
            raise ValueError("Dimensões da fundação devem ser positivas")

@dataclass
class ResultadoAnalise:
    """Estrutura para organizar os resultados da análise."""
    coordenadas: np.ndarray  # Malha de pontos (x, y, z)
    tensoes: np.ndarray  # Valores de Δσz correspondentes
    parametros_entrada: dict  # Dicionário com todos os inputs