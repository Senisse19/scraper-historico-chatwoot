# 🚀 Chatwoot Full ETL - Extract

Script Python profissional para extração completa do histórico de conversas do Chatwoot, otimizado para alimentar modelos de IA com dados limpos e estruturados.

## 📋 Características

✅ **Autenticação Segura**: Variáveis de ambiente com `.env`  
✅ **Paginação Robusta**: Itera automaticamente por todas as páginas da API  
✅ **Mapeamento de Canais**: Converte IDs de inbox para nomes legíveis (WhatsApp, Email, etc.)  
✅ **Rate Limiting Inteligente**: Tratamento de erro 429 e delays preventivos  
✅ **Retry Logic**: Até 3 tentativas com exponential backoff  
✅ **Barra de Progresso**: Acompanhamento visual com `tqdm`  
✅ **Formato IA-Ready**: JSON estruturado com ISO 8601 timestamps  

## 🛠️ Instalação

### 1. Clone ou baixe este projeto

```bash
cd chatwoot-etl
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e edite com suas credenciais:

```bash
copy .env.example .env
```

Edite o arquivo `.env`:

```env
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCESS_TOKEN=seu_token_aqui
CHATWOOT_ACCOUNT_ID=1
```

#### 🔑 Como obter as credenciais:

1. **API URL**: Se você usa o Chatwoot Cloud, é `https://app.chatwoot.com`. Se for self-hosted, use seu domínio.
2. **Access Token**: 
   - Faça login no Chatwoot
   - Vá em **Configurações** → **Integrações** → **Access Tokens**
   - Crie um novo token com permissões de leitura
3. **Account ID**: 
   - Vá em qualquer conversa
   - Na URL verá: `https://app.chatwoot.com/app/accounts/123/...`
   - O número `123` é seu Account ID

## 🎯 Uso

Execute o script:

```bash
python chatwoot_etl.py
```

### Saída Esperada

```
============================================================
🚀 CHATWOOT FULL ETL - EXTRACT
============================================================

✅ Configuração carregada com sucesso!
   API URL: https://app.chatwoot.com
   Account ID: 1

📥 Carregando mapeamento de canais (Inboxes)...
✅ 3 canais mapeados:
   - ID 1: WhatsApp Comercial
   - ID 2: Web Widget
   - ID 3: Email Suporte

💬 Buscando conversas...
📊 Total de conversas: 1250
Páginas processadas: 100%|███████████| 50/50 [00:45<00:00]
✅ 1250 conversas carregadas

🔄 Transformando dados...
Processando conversas: 100%|████████| 1250/1250 [08:32<00:00]
✅ 8742 mensagens processadas

💾 Salvando dados em chatwoot_history_dump.json...
✅ Arquivo salvo com sucesso!
   Tamanho: 5.23 MB
   Total de mensagens: 8742

============================================================
📊 ESTATÍSTICAS DA EXTRAÇÃO
============================================================
⏱️  Tempo total: 542.18 segundos
💬 Conversas processadas: 1250
📨 Mensagens extraídas: 8742
📁 Arquivo gerado: chatwoot_history_dump.json

✅ ETL concluído com sucesso!
============================================================
```

## 📦 Formato de Saída

O arquivo `chatwoot_history_dump.json` contém um array de objetos no seguinte formato:

```json
[
  {
    "conversation_id": 12345,
    "customer_name": "João Silva",
    "customer_email": "joao@exemplo.com",
    "channel_name": "WhatsApp Comercial",
    "message_type": "incoming",
    "sender_name": "João Silva",
    "content": "Olá, preciso de ajuda com meu pedido",
    "created_at_iso": "2023-10-27T14:30:00Z",
    "agent_email": null
  },
  {
    "conversation_id": 12345,
    "customer_name": "João Silva",
    "customer_email": "joao@exemplo.com",
    "channel_name": "WhatsApp Comercial",
    "message_type": "outgoing",
    "sender_name": "Ana Suporte",
    "content": "Olá João! Claro, vou verificar seu pedido agora.",
    "created_at_iso": "2023-10-27T14:32:15Z",
    "agent_email": "ana@suaempresa.com"
  }
]
```

### 📊 Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `conversation_id` | int | ID único da conversa no Chatwoot |
| `customer_name` | string | Nome do cliente/contato |
| `customer_email` | string | Email do cliente (pode ser vazio) |
| `channel_name` | string | Nome do canal (WhatsApp, Email, etc.) |
| `message_type` | string | `incoming` (cliente) ou `outgoing` (agente) |
| `sender_name` | string | Nome de quem enviou a mensagem |
| `content` | string | Conteúdo da mensagem de texto |
| `created_at_iso` | string | Data/hora em formato ISO 8601 |
| `agent_email` | string/null | Email do agente (se aplicável) |

## 🔧 Configurações Avançadas

### Rate Limiting

Por padrão, há um delay de **500ms** entre requisições. Você pode ajustar em `ChatwootETL.__init__`:

```python
self.rate_limit_delay = 0.5  # Altere para 1.0 se necessário
```

### Número de Retentativas

O padrão é **3 tentativas** com exponential backoff. Ajuste em:

```python
self.max_retries = 3  # Aumente se sua rede for instável
```

## 🐛 Solução de Problemas

### Erro: "Variáveis de ambiente não configuradas"
- Verifique se o arquivo `.env` está na mesma pasta do script
- Certifique-se de que as variáveis estão preenchidas corretamente

### Erro 401 (Autenticação)
- Verifique se o `CHATWOOT_ACCESS_TOKEN` está correto
- Confirme que o token tem as permissões necessárias

### Erro 429 (Rate Limit)
- O script já trata isso automaticamente
- Se persistir, aumente o `rate_limit_delay`

### Timeout nas requisições
- Aumente o `timeout` na função `_make_request`
- Verifique sua conexão de internet

## 📈 Próximos Passos (Transform & Load)

Este script faz apenas o **Extract**. Para análise completa:

1. **Transform**: Use pandas para limpar e normalizar os dados
2. **Load**: Carregue em um data warehouse (BigQuery, Snowflake, etc.)
3. **Análise de Sentimentos**: Use modelos como BERT, GPT ou bibliotecas como TextBlob

### Exemplo de Análise

```python
import pandas as pd

# Carregar dados
df = pd.read_json('chatwoot_history_dump.json')

# Análises rápidas
print(f"Total de mensagens: {len(df)}")
print(f"Total de conversas únicas: {df['conversation_id'].nunique()}")
print(f"Mensagens por canal:\n{df['channel_name'].value_counts()}")
print(f"Taxa de resposta: {(df['message_type'] == 'outgoing').mean() * 100:.1f}%")
```

## 📝 Licença

Este script é fornecido como está, sem garantias. Use por sua conta e risco.

## 🤝 Contribuições

Sinta-se à vontade para melhorar este script. Sugestões:
- Adicionar suporte a attachments (imagens, arquivos)
- Implementar filtros por data
- Adicionar export para CSV/Parquet
- Integrar com cloud storage (S3, GCS)

---

**Desenvolvido por**: Engenheiro de Dados Sênior  
**Data**: 2025-12-05  
**Versão**: 1.0.0
