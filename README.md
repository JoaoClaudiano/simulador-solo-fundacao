# 🏗️ SimulaSolo: Simulador de Tensões no Solo para Fundações

https://static.streamlit.io/badges/streamlit_badge_black_white.svg
https://img.shields.io/badge/python-3.9+-blue.svg
https://img.shields.io/badge/License-MIT-yellow.svg

## Uma aplicação web interativa desenvolvida em Python/Streamlit para análise e visualização da distribuição de tensões no solo sob fundações superficiais.

---

# ✨ Funcionalidades Principais

· 📊 Cálculo de Tensões: Determina a distribuição de tensões verticais (Δσz) no solo usando a solução de Love para carga uniformemente distribuída sobre área retangular.
· 🌐 Visualização 3D Interativa: Gera um "bulbo de tensões" tridimensional utilizando Plotly, permitindo rotação, zoom e análise detalhada do fenômeno.
· 📈 Gráficos de Perfil: Plota gráficos 2D da variação da tensão vertical com a profundidade em pontos específicos.
· 🗃️ Banco de Dados de Solos: Acesso integrado a um catálogo de tipos de solo (argila, silte, areia) com parâmetros geotécnicos pré-definidos.
· 📥 Exportação de Resultados: Exporta os dados calculados para formatos CSV e Excel para análise externa.
· 🧪 Exemplos Prontos: Scripts de exemplo que demonstram o uso do núcleo de cálculo independentemente da interface web.

---

# 🚀 Começando

## Pré-requisitos

· Python 3.9 ou superior
· pip (gerenciador de pacotes do Python)

## Instalação Local

1. Clone o repositório:
   ```bash
   git clone https://github.com/JoaoClaudiano/simulador-solo-fundacao.git
   cd simulador-solo-fundacao
   ```
2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   # No Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # No Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```
   A aplicação abrirá automaticamente no seu navegador padrão (geralmente em http://localhost:8501).

## Execução via Docker (Alternativa)

```bash
# Construa a imagem
docker build -t simulasolo .

# Execute o container
docker run -p 8501:8501 simulasolo
```

---

# 🖥️ Como Usar a Aplicação

1. Parâmetros da Fundação (barra lateral):
   · Insira as dimensões (comprimento e largura).
   · Defina a carga aplicada (kN/m²).
2. Parâmetros do Solo (barra lateral):
   · Selecione um tipo de solo pré-definido do banco de dados OU
   · Insira manualmente: peso específico (γ), ângulo de atrito (φ), coesão (c) e módulo de elasticidade (E).
3. Parâmetros da Análise (barra lateral):
   · Defina a profundidade inicial e final para a análise.
   · Escolha a resolução da malha de pontos.
4. Clique em "Calcular Tensões":
   · A aplicação processará os dados e exibirá:
     · Uma tabela com os resultados numéricos.
     · Um gráfico 3D interativo do bulbo de tensões.
     · Gráficos 2D do perfil de tensões em diferentes pontos.
5. Exporte os resultados usando os botões dedicados.

---

# 🏗️ Estrutura do Projeto

```
simulador-solo-fundacao/
├── app.py                         # Aplicação principal Streamlit
├── requirements.txt               # Dependências do Python
├── packages.txt                   # Pacotes do sistema (apt)
├── check_installation.py          # Script para verificar instalação
├── install_dependencies.sh        # Script de instalação de dependências
├── LICENSE                        # Licença MIT do projeto
│
├── .devcontainer/                 # Configuração do Dev Container
│   └── devcontainer.json          # Configuração do ambiente de desenvolvimento
│
├── src/                           # Núcleo do simulador
│   ├── __init__.py                # Inicialização do pacote
│   ├── bulbo_tensoes.py           # Lógica principal de cálculo (Love)
│   ├── estacas.py                 # Cálculos para fundações profundas (estacas)
│   ├── export_system.py           # Sistema de exportação de dados
│   ├── foundation_calculations.py # Cálculos gerais de fundações
│   ├── integracao_tcc.py          # Integração com trabalhos de conclusão de curso
│   ├── models.py                  # Modelos de dados geotécnicos
│   ├── mohr_coulomb.py            # Implementação do critério de Mohr-Coulomb
│   ├── nbr_validation.py          # Validação segundo normas NBR
│   ├── relatorio_abnt.py          # Geração de relatórios no padrão ABNT
│   ├── soil_calculations.py       # Cálculos relacionados ao solo
│   ├── terzaghi.py                # Método de Terzaghi para capacidade de carga
│   └── validacao_casos_teste.py   # Testes de validação de casos
│
├── data/                          # Dados e configurações
│   └── soil_database.json         # Banco de dados de tipos de solo
│
├── examples/                      # Exemplos de uso
│   └── foundation_example.py      # Uso do núcleo sem a interface web
│
├── tests/                         # Testes automatizados
│   ├── test_foundation.py         # Testes unitários de fundações
│   ├── test_integration.py        # Testes de integração
│   └── test_models.py             # Testes de modelos de dados
│
├── utils/                         # Utilitários
│   └── export_utils.py            # Funções para exportar dados (CSV, Excel)
│
└── streamlit/                     # Configurações do Streamlit
    ├── config.toml                # Configuração do Streamlit
    ├── setup.sh                   # Script de setup para deployment
    └── theme_custom.css           # Tema customizado da aplicação
```

---

# 🧪 Executando os Testes

Para garantir a corretude dos cálculos, execute a suite de testes:

```bash
pytest tests/
```

Para um relatório mais detalhado:

```bash
pytest tests/ -v
```

---

# 🛠️ Tecnologias Utilizadas

· Streamlit: Framework para criação da interface web rápida e interativa.
· Plotly: Geração de gráficos 3D interativos e de alta qualidade.
· Matplotlib: Criação de gráficos 2D estáticos para perfis.
· Pandas & NumPy: Manipulação e cálculos numéricos eficientes.
· Pytest: Framework para testes unitários.

---

# 🤝 Como Contribuir

Contribuições são bem-vindas! Siga os passos abaixo:

1. Faça um Fork do projeto.
2. Crie uma Branch para sua feature/correção (git checkout -b feature/NovaFuncionalidade).
3. Commit suas mudanças (git commit -m 'Adiciona NovaFuncionalidade').
4. Faça Push para a Branch (git push origin feature/NovaFuncionalidade).
5. Abra um Pull Request explicando suas modificações.

---

# 📈 Melhorias em Aberto (Roadmap)

· Implementação de outros métodos teóricos (ex.: Boussinesq, Westergaard).
· Cálculo de capacidade de carga do solo (Terzaghi, Meyerhof).
· Análise de recalques.
· Interface ainda mais intuitiva com abas e validação em tempo real.

---

# 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

# 📞 Contato e Suporte

· Repositório GitHub: https://github.com/JoaoClaudiano/simulador-solo-fundacao
· Aplicação Online: https://simulasolo.streamlit.app
· Em caso de problemas, por favor, abra uma issue no GitHub.

---

# Desenvolvido com ❤️ para a comunidade de Geotecnia e Engenharia Civil.