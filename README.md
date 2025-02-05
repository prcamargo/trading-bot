# Bot de Trading Automatizado para Binance

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Um bot de trading automatizado para a Binance que utiliza análise técnica e gerenciamento de risco integrado.

## 📌 Funcionalidades Principais

- **Estratégias Combinadas**:
  - Crossover de Médias Móveis (SMA 20/50)
  - Índice de Força Relativa (RSI)
  - Convergência/Divergência de Médias Móveis (MACD)
  
- **Gerenciamento de Risco**:
  - Stop Loss automático (1%)
  - Take Profit automático (2%)
  - Tamanho de posição ajustável (10% do saldo)

- **Relatórios**:
  - Visualização de resultados no terminal
  - Histórico completo de trades
  - Estatísticas de desempenho
  - Gráfico ASCII de evolução do lucro

## 📦 Pré-requisitos

- Python 3.8+
- Conta na Binance com API habilitada
- Saldo em USDT na conta spot

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/binance-trading-bot.git
cd binance-trading-bot

```
2. Build Docker
```bash
docker build -t trading-bot -f docker/Dockerfile .
docker run -e BINANCE_API_KEY=<key> -e BINANCE_API_SECRET=<secret> trading-bot
```

## 🌐 Infraestrutura na Azure

O projeto usa Terraform para provisionar:
- Grupo de recursos dedicado
- Container Registry (ACR)
- Instância de Container (ACI)

Para aplicar a infraestrutura:
```bash
cd infra/azure
terraform init
terraform apply