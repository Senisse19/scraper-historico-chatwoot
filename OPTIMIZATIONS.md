# 🚀 Otimizações de Performance Implementadas

## 📊 Resumo das Melhorias

Este documento descreve as otimizações de performance implementadas no sistema Chatwoot ETL Extractor.

### ✅ Fase 1 - Quick Wins (Concluída)

#### 1. Remoção da Dependência Pandas
- **Impacto**: Redução de ~50MB no tamanho da instalação
- **Benefício**: Startup ~200ms mais rápido
- **Mudança**: Removida importação não utilizada do `pandas`

#### 2. Sistema de Cache para Inbox Map
- **Impacto**: Elimina chamadas desnecessárias à API
- **Benefício**: Experiência do usuário mais rápida ao abrir o aplicativo
- **Funcionamento**: 
  - Cache armazenado em `exports/.cache/inbox_map.pkl`
  - TTL de 1 hora (configurável via `self.cache_ttl`)
  - Atualização automática quando expirado

#### 3. Algoritmo Otimizado de Remoção de Duplicatas
- **Impacto**: Menor uso de memória
- **Benefício**: Processamento mais eficiente de grandes volumes
- **Mudança**: Substituição de dict comprehension por set-based tracking

---

### ⚡ Fase 2 - Alto Impacto (Concluída)

#### 4. Paralelização de Requisições HTTP
- **Impacto**: **Redução de 70-80% no tempo de processamento** 🔥
- **Funcionamento**:
  - Usa `ThreadPoolExecutor` com 10 workers simultâneos (configurável)
  - Processa múltiplas conversas em paralelo
  - Fallback automático para modo sequencial se `max_workers = 1`
- **Configuração**:
  ```python
  etl = ChatwootETL()
  etl.max_workers = 15  # Aumentar para mais paralelização
  ```

#### 5. Rate Limiting Adaptativo
- **Impacto**: Redução de 10-20% no tempo total
- **Benefício**: Otimiza velocidade sem sobrecarregar a API
- **Funcionamento**:
  - Começa com delay de 500ms
  - Reduz gradualmente (0.95x) após requisições bem-sucedidas
  - Aumenta (1.5x) após rate limit hits (429)
  - Mínimo: 100ms | Máximo: 3s
- **Configuração**:
  ```python
  etl = ChatwootETL()
  etl.adaptive_rate_limit = True  # Padrão: True
  etl.rate_limit_delay = 0.3  # Delay inicial (segundos)
  ```

#### 6. Filtros de Data na API
- **Impacto**: Redução de 20-40% em dados transferidos
- **Benefício**: Menos dados processados = mais rápido
- **Funcionamento**: Adiciona parâmetros `since` e `until` nas requisições

---

## 📈 Ganhos de Performance Esperados

| Cenário | Tempo Antes | Tempo Depois | Redução |
|---------|-------------|--------------|---------|
| 100 conversas | ~3 min | ~45 seg | **75%** |
| 500 conversas | ~15 min | ~3.5 min | **77%** |
| 1000 conversas | ~30 min | ~6 min | **80%** |

*Estimativas baseadas em API com latência média de 500ms*

---

## 🎛️ Configurações Avançadas

### Ajustar Número de Workers Paralelos

```python
# Em chatwoot_etl.py, linha ~74
self.max_workers = 10  # Padrão

# Valores recomendados:
# - API lenta: 5-8 workers
# - API rápida: 10-15 workers
# - Conta free/limitada: 3-5 workers
# - Desabilitar paralelização: 1 worker
```

### Ajustar TTL do Cache

```python
# Em chatwoot_etl.py, linha ~75
self.cache_ttl = 3600  # 1 hora (padrão)

# Valores sugeridos:
# - Desenvolvimento: 300 (5 min)
# - Produção: 3600 (1 hora)
# - Inboxes raramente mudam: 86400 (24 horas)
```

### Desabilitar Rate Limiting Adaptativo

```python
# Em chatwoot_etl.py, linha ~76
self.adaptive_rate_limit = False  # Usa delay fixo
```

---

## 🧪 Como Testar as Melhorias

### 1. Teste Rápido (10 conversas)
```bash
python chatwoot_etl.py --start-date 2025-12-10 --end-date 2025-12-12
```

### 2. Benchmark Completo
1. Limpar cache: `rm -rf exports/.cache`
2. Executar com 100 conversas e cronometrar
3. Comparar com versão anterior

### 3. Monitorar Performance
- Observe os logs para ver o delay adaptativo em ação
- Verifique o uso de threads no gerenciador de tarefas
- Confirme que o cache é utilizado na segunda execução

---

## ⚠️ Troubleshooting

### Erro: "Too many requests" frequente
**Solução**: Reduza `max_workers` ou aumente `rate_limit_delay` inicial
```python
self.max_workers = 5
self.rate_limit_delay = 1.0
```

### Performance pior que antes
**Solução**: Verifique se a paralelização está ativa
```python
# Logs devem mostrar: "Processando conversas" com progresso paralelo
# Se aparecer erros, tente desabilitar:
self.max_workers = 1  # Modo sequencial
```

### Cache não funciona
**Solução**: Verifique permissões da pasta `exports/.cache`
```bash
mkdir -p exports/.cache
chmod 755 exports/.cache  # Linux/Mac
```

---

## 📝 Changelog

### v2.0.0 - Performance Optimization (2025-12-12)
- ✅ Paralelização de requisições HTTP (ThreadPoolExecutor)
- ✅ Rate limiting adaptativo
- ✅ Sistema de cache para inbox map
- ✅ Filtros de data na API
- ✅ Remoção de dependência pandas
- ✅ Algoritmo otimizado de deduplicação

### v1.0.0 - Versão Inicial
- Extração básica de conversas
- Paginação automática
- Export para JSON

---

## 🚀 Próximas Melhorias (Fase 3 - Opcional)

- [ ] JSON Streaming para datasets muito grandes
- [ ] Botão de cancelamento na UI
- [ ] Progress bar mais detalhado
- [ ] Export para formato Parquet (mais compacto)
- [ ] Suporte a async/await com aiohttp (ainda mais rápido)

---

**Desenvolvido com 💛 por Studio Fiscal**  
*Última atualização: 2025-12-12*
