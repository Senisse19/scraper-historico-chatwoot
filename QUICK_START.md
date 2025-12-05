# 🚀 Guia Rápido - Chatwoot ETL

## ✅ Status da Configuração

- [x] Python 3.14.0 instalado
- [x] Dependências instaladas (requests, pandas, tqdm, python-dotenv)
- [x] Arquivo .env criado
- [ ] **PRÓXIMO PASSO**: Configurar credenciais no arquivo `.env`

## 📝 Como Configurar e Executar

### Passo 1: Obter Credenciais do Chatwoot

Você precisa de 3 informações:

#### 1️⃣ **CHATWOOT_API_URL**
- Se você usa **Chatwoot Cloud**: `https://app.chatwoot.com`
- Se você tem **instalação própria**: `https://seu-dominio.com`

#### 2️⃣ **CHATWOOT_ACCESS_TOKEN**
Como obter:
1. Faça login no Chatwoot
2. Vá em **Configurações** (ícone de engrenagem)
3. Clique em **Integrações** → **Access Tokens**
4. Clique em **"Adicionar Token"**
5. Dê um nome (ex: "ETL Script")
6. Copie o token gerado

#### 3️⃣ **CHATWOOT_ACCOUNT_ID**
Como obter:
1. Abra qualquer conversa no Chatwoot
2. Olhe a URL no navegador:
   ```
   https://app.chatwoot.com/app/accounts/123/conversations/456
                                          ^^^
                                       Este é seu Account ID
   ```

### Passo 2: Editar o Arquivo `.env`

Abra o arquivo `.env` nesta pasta e substitua os valores:

```env
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCESS_TOKEN=cole_seu_token_aqui
CHATWOOT_ACCOUNT_ID=123
```

### Passo 3: Executar o Script

Após configurar o `.env`, execute:

```powershell
py chatwoot_etl.py
```

## 📊 O Que Vai Acontecer

O script irá:

1. ✅ Validar suas credenciais
2. 📥 Buscar todos os canais (Inboxes) disponíveis
3. 💬 Baixar todas as conversas (com barra de progresso)
4. 🔄 Extrair mensagens de cada conversa
5. 💾 Salvar em `chatwoot_history_dump.json`

### Exemplo de Saída:

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
📊 Total de conversas: 250
Páginas processadas: 100%|████████| 10/10 [00:15<00:00]
✅ 250 conversas carregadas

🔄 Transformando dados...
Processando conversas: 100%|████████| 250/250 [02:10<00:00]
✅ 1847 mensagens processadas

💾 Salvando dados em chatwoot_history_dump.json...
✅ Arquivo salvo com sucesso!
   Tamanho: 1.23 MB
   Total de mensagens: 1847

============================================================
📊 ESTATÍSTICAS DA EXTRAÇÃO
============================================================
⏱️  Tempo total: 145.32 segundos
💬 Conversas processadas: 250
📨 Mensagens extraídas: 1847
📁 Arquivo gerado: chatwoot_history_dump.json

✅ ETL concluído com sucesso!
============================================================
```

## 🔍 Validar o Resultado

Após a execução, você terá o arquivo `chatwoot_history_dump.json` com estrutura:

```json
[
  {
    "conversation_id": 12345,
    "customer_name": "João Silva",
    "customer_email": "joao@exemplo.com",
    "channel_name": "WhatsApp Comercial",
    "message_type": "incoming",
    "sender_name": "João Silva",
    "content": "Olá, preciso de ajuda",
    "created_at_iso": "2023-10-27T14:30:00Z",
    "agent_email": null
  }
]
```

## ❓ Problemas Comuns

### Erro: "Variáveis de ambiente não configuradas"
➡️ Verifique se o arquivo `.env` está na mesma pasta do script

### Erro 401 (Autenticação)
➡️ Seu token está incorreto ou expirado. Gere um novo no Chatwoot

### Erro 429 (Rate Limit)
➡️ O script já trata isso automaticamente com delays

### Script muito lento
➡️ Normal para muitas conversas. Acompanhe pela barra de progresso

## 🎯 Próximos Passos

Após extrair os dados, você pode:

1. **Análise com Pandas**:
```python
import pandas as pd
df = pd.read_json('chatwoot_history_dump.json')
print(df['channel_name'].value_counts())
```

2. **Análise de Sentimentos** (exemplo):
```python
from textblob import TextBlob
df['sentiment'] = df['content'].apply(lambda x: TextBlob(x).sentiment.polarity)
```

3. **Treinar modelo de IA** com os dados estruturados

---

**Precisa de ajuda?** Consulte o `README.md` para documentação completa!
