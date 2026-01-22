import pytest
from src.models import Solo, Fundacao

def test_solo_creation_valid():
    """Testa criação válida de objeto Solo."""
    solo = Solo(
        nome="Areia Média",
        peso_especifico=18.0,
        angulo_atrito=32,
        coesao=0,
        modulo_elasticidade=30
    )
    assert solo.nome == "Areia Média"
    assert solo.peso_especifico == 18.0

def test_solo_invalid_peso_especifico():
    """Testa validação de peso específico inválido."""
    with pytest.raises(ValueError, match="Peso específico deve ser positivo"):
        Solo(nome="Inválido", peso_especifico=0)

def test_fundacao_invalid_dimensions():
    """Testa validação de dimensões inválidas."""
    with pytest.raises(ValueError, match="Dimensões da fundação devem ser positivas"):
        Fundacao(largura=0, comprimento=2.0, carga=100)