# Gerenciador de Lista de Bloqueados - League of Legends

![Banner](https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Teemo_0.jpg)

## Sobre o Projeto

Esta ferramenta permite gerenciar sua lista de jogadores bloqueados no League of Legends de forma eficiente. O programa analisa o elo dos jogadores bloqueados e permite remover automaticamente aqueles com uma diferença significativa de elo em relação ao seu, ajudando a manter sua lista de bloqueados mais relevante para seu nível de jogo atual.

## Funcionalidades

- **Conexão automática** com o cliente do League of Legends
- **Análise completa** da sua lista de bloqueados
- **Verificação de elo** para cada jogador bloqueado
- **Limpeza automática** baseada na diferença de elo configurável
- **Exportação de dados** em formato Excel para análise detalhada

## Como Usar

1. Abra o cliente do League of Legends (o jogo deve estar aberto)
2. Execute o aplicativo Gerenciador de Lista de Bloqueados
3. Selecione sua região e clique em "Conectar ao Cliente"
4. Configure a diferença de elo desejada para remoção
5. Use "Analisar Bloqueados" para ver um relatório detalhado
6. Use "Limpar Lista Automaticamente" para remover jogadores que estão fora da sua faixa de elo

## Requisitos

- Windows 7 ou superior
- Python 3.7+
- Cliente do League of Legends instalado
- Pacotes Python:
  - pandas
  - psutil
  - requests
  - urllib3

## Instalação

1. Clone o repositório:
