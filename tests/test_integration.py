def test_fluxo_completo_app():
    """Testa o fluxo completo desde a entrada até os resultados."""
    from src.bulbo_tensoes import analisar_tensoes_fundacao
    
    fundacao = Fundacao(largura=1.5, comprimento=1.5, carga=150)
    solo = Solo(nome="Silte", peso_especifico=19.0)
    
    resultado = analisar_tensoes_fundacao(
        fundacao=fundacao,
        solo=solo,
        profundidade_inicial=0,
        profundidade_final=5,
        resolucao=10
    )
    
    assert resultado.coordenadas.shape[0] == 10**3  # 10 pontos em cada dimensão
    assert resultado.tensoes.shape[0] == resultado.coordenadas.shape[0]
    assert len(resultado.parametros_entrada) == 4