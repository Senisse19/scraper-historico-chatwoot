#!/usr/bin/env python3
"""
Chatwoot Full ETL - Extract
Script para extração completa do histórico de conversas do Chatwoot
Desenvolvido para análise de sentimentos e métricas com IA

Autor: Engenheiro de Dados Sênior
Data: 2025-12-05
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
import pandas as pd


class ChatwootETL:
    """Classe para gerenciar a extração de dados do Chatwoot"""
    
    def __init__(self):
        """Inicializa a classe com configurações do .env"""
        load_dotenv()
        
        self.api_url = os.getenv('CHATWOOT_API_URL', '').rstrip('/')
        self.access_token = os.getenv('CHATWOOT_ACCESS_TOKEN')
        self.account_id = os.getenv('CHATWOOT_ACCOUNT_ID')
        
        # Validação de variáveis de ambiente
        if not all([self.api_url, self.access_token, self.account_id]):
            raise ValueError(
                "❌ Variáveis de ambiente não configuradas corretamente!\n"
                "Certifique-se de que CHATWOOT_API_URL, CHATWOOT_ACCESS_TOKEN "
                "e CHATWOOT_ACCOUNT_ID estão definidos no arquivo .env"
            )
        
        self.headers = {
            'api_access_token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        self.inbox_map = {}  # Mapa de inbox_id -> nome do canal
        self.rate_limit_delay = 0.5  # Delay padrão entre requisições (500ms)
        self.max_retries = 3  # Número máximo de tentativas em caso de erro
        
        print(f"✅ Configuração carregada com sucesso!")
        print(f"   API URL: {self.api_url}")
        print(f"   Account ID: {self.account_id}\n")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, debug: bool = False) -> Optional[Dict]:
        """
        Faz requisição à API com tratamento de erros e rate limiting
        
        Args:
            endpoint: Endpoint da API (ex: /api/v1/accounts/{account_id}/inboxes)
            params: Parâmetros da query string
            debug: Se True, mostra detalhes completos da resposta
            
        Returns:
            Resposta JSON ou None em caso de erro
        """
        url = f"{self.api_url}{endpoint}"
        
        if debug:
            print(f"🔍 DEBUG: {url}")
            if params:
                print(f"🔍 Parâmetros: {params}")
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                # Rate limiting - Too Many Requests
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"⚠️  Rate limit atingido. Aguardando {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Erro de autenticação
                if response.status_code == 401:
                    print(f"❌ Erro 401: Autenticação falhou")
                    print(f"🔍 Resposta: {response.text[:500]}")
                    raise Exception("❌ Erro de autenticação. Verifique seu ACCESS_TOKEN")
                
                # Outros erros HTTP
                if response.status_code >= 400:
                    print(f"⚠️  Erro HTTP {response.status_code} em {endpoint}")
                    print(f"   Tentativa {attempt + 1}/{self.max_retries}")
                    
                    # Mostra resposta de erro para debug
                    try:
                        error_data = response.json()
                        print(f"🔍 Detalhes: {error_data}")
                    except:
                        print(f"🔍 Resposta: {response.text[:500]}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None
                
                # Sucesso
                time.sleep(self.rate_limit_delay)  # Delay preventivo
                return response.json()
                
            except requests.exceptions.Timeout:
                print(f"⚠️  Timeout na requisição. Tentativa {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Erro na requisição: {str(e)}")
                return None
        
        return None
    
    def load_inbox_map(self) -> bool:
        """
        Carrega o mapeamento de Inboxes (id -> nome do canal)
        
        Returns:
            True se bem sucedido, False caso contrário
        """
        print("📥 Carregando mapeamento de canais (Inboxes)...")
        
        endpoint = f"/api/v1/accounts/{self.account_id}/inboxes"
        response = self._make_request(endpoint)
        
        if not response or 'payload' not in response:
            print("❌ Falha ao carregar inboxes")
            return False
        
        inboxes = response['payload']
        
        for inbox in inboxes:
            inbox_id = inbox.get('id')
            inbox_name = inbox.get('name', 'Canal Desconhecido')
            self.inbox_map[inbox_id] = inbox_name
        
        print(f"✅ {len(self.inbox_map)} canais mapeados:")
        for inbox_id, name in self.inbox_map.items():
            print(f"   - ID {inbox_id}: {name}")
        print()
        
        return True
    
    def get_all_conversations(self) -> List[Dict]:
        """
        Obtém todas as conversas com paginação automática
        Tenta múltiplas estratégias se a primeira falhar
        
        Returns:
            Lista de todas as conversas
        """
        print("💬 Buscando conversas...")
        
        # Estratégia 1: Buscar todas as conversas de uma vez
        conversations = self._get_conversations_all_status()
        
        if conversations:
            return conversations
        
        print("⚠️  Estratégia padrão falhou. Tentando buscar por inbox...")
        
        # Estratégia 2: Buscar conversas por cada inbox
        conversations = self._get_conversations_by_inbox()
        
        return conversations
    
    def _get_conversations_all_status(self) -> List[Dict]:
        """
        Tenta buscar todas as conversas com diferentes filtros de status
        """
        all_conversations = []
        
        # Tenta com diferentes status (open, resolved, pending, snoozed, all)
        status_filters = ['all', 'open', 'resolved', 'pending']
        
        for status in status_filters:
            print(f"🔍 Tentando buscar conversas com status: {status}")
            
            page = 1
            endpoint = f"/api/v1/accounts/{self.account_id}/conversations"
            params = {
                'page': page,
                'status': status
            }
            
            response = self._make_request(endpoint, params, debug=True)
            
            if not response:
                continue
            
            # Verifica estrutura da resposta
            if 'data' in response and 'meta' in response:
                # Formato: {data: {payload: [...]}, meta: {...}}
                total_count = response['meta'].get('count', 0)
                payload = response['data'].get('payload', [])
                
                if total_count > 0:
                    print(f"✅ Encontradas {total_count} conversas com status '{status}'")
                    all_conversations.extend(payload)
                    
                    # Calcula número de páginas
                    per_page = response['meta'].get('per_page', 25)
                    total_pages = (total_count + per_page - 1) // per_page
                    
                    # Busca páginas restantes
                    if total_pages > 1:
                        with tqdm(total=total_pages, desc=f"Páginas [{status}]", unit="página") as pbar:
                            pbar.update(1)
                            
                            page = 2
                            while page <= total_pages:
                                params['page'] = page
                                response = self._make_request(endpoint, params)
                                
                                if response and 'data' in response:
                                    conversations = response['data'].get('payload', [])
                                    if conversations:
                                        all_conversations.extend(conversations)
                                    else:
                                        break
                                    pbar.update(1)
                                    page += 1
                                else:
                                    break
                    
                    # Encontrou conversas, retorna
                    return all_conversations
            
            elif 'payload' in response and 'meta' in response:
                # Formato alternativo: {payload: [...], meta: {...}}
                total_count = response['meta'].get('count', 0)
                payload = response.get('payload', [])
                
                if total_count > 0:
                    print(f"✅ Encontradas {total_count} conversas com status '{status}'")
                    all_conversations = payload
                    return all_conversations
        
        return all_conversations
    
    def _get_conversations_by_inbox(self) -> List[Dict]:
        """
        Busca conversas iterando por cada inbox
        Útil quando a busca global não funciona
        """
        all_conversations = []
        
        print(f"📨 Buscando conversas por canal (inbox)...")
        
        for inbox_id, inbox_name in tqdm(self.inbox_map.items(), desc="Canais processados", unit="canal"):
            endpoint = f"/api/v1/accounts/{self.account_id}/conversations"
            
            # Tenta diferentes combinações de parâmetros
            param_combinations = [
                {'inbox_id': inbox_id, 'status': 'all'},
                {'inbox_id': inbox_id, 'status': 'open'},
                {'inbox_id': inbox_id, 'status': 'resolved'},
                {'inbox_id': inbox_id},
            ]
            
            for params in param_combinations:
                response = self._make_request(endpoint, params)
                
                if response:
                    # Extrai conversas independente do formato
                    conversations = []
                    
                    if 'data' in response and 'payload' in response['data']:
                        conversations = response['data']['payload']
                    elif 'payload' in response:
                        conversations = response['payload']
                    
                    if conversations:
                        print(f"   ✅ {len(conversations)} conversas em '{inbox_name}'")
                        all_conversations.extend(conversations)
                        break  # Encontrou com essa combinação, próximo inbox
        
        if all_conversations:
            # Remove duplicatas (mesma conversa pode aparecer em múltiplos status)
            unique_conversations = {conv['id']: conv for conv in all_conversations}.values()
            all_conversations = list(unique_conversations)
            print(f"\n✅ Total: {len(all_conversations)} conversas únicas carregadas\n")
        else:
            print("\n❌ Nenhuma conversa encontrada em nenhum canal\n")
        
        return all_conversations
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """
        Obtém todas as mensagens de uma conversa específica
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Lista de mensagens
        """
        endpoint = f"/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        response = self._make_request(endpoint)
        
        if not response or 'payload' not in response:
            return []
        
        return response['payload']
    
    def transform_messages(self, conversations: List[Dict]) -> List[Dict]:
        """
        Transforma as conversas e mensagens no formato desejado
        
        Args:
            conversations: Lista de conversas do Chatwoot
            
        Returns:
            Lista de mensagens formatadas para análise
        """
        print("🔄 Transformando dados...")
        
        transformed_messages = []
        
        # Barra de progresso para conversas
        for conversation in tqdm(conversations, desc="Processando conversas", unit="conversa"):
            conversation_id = conversation.get('id')
            inbox_id = conversation.get('inbox_id')
            
            # Dados do cliente
            contact = conversation.get('meta', {}).get('sender', {})
            customer_name = contact.get('name', 'Cliente Desconhecido')
            customer_email = contact.get('email', '')
            
            # Nome do canal (do mapa criado anteriormente)
            channel_name = self.inbox_map.get(inbox_id, f'Canal ID {inbox_id}')
            
            # Busca as mensagens desta conversa
            messages = self.get_conversation_messages(conversation_id)
            
            for msg in messages:
                # Determina o tipo de mensagem (incoming/outgoing)
                message_type = msg.get('message_type', 'outgoing')
                
                # Dados do remetente
                sender = msg.get('sender')
                sender_name = customer_name  # Padrão é cliente
                agent_email = None
                
                if sender and sender.get('type') == 'User':
                    # É um agente
                    sender_name = sender.get('name', 'Agente Desconhecido')
                    agent_email = sender.get('email', '')
                
                # Conteúdo da mensagem
                content = msg.get('content', '')
                
                # Data de criação em formato ISO 8601
                created_at = msg.get('created_at')
                created_at_iso = None
                
                if created_at:
                    # Chatwoot retorna timestamp Unix
                    try:
                        dt = datetime.fromtimestamp(created_at)
                        created_at_iso = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    except:
                        created_at_iso = str(created_at)
                
                # Monta o objeto de mensagem
                message_obj = {
                    "conversation_id": conversation_id,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "channel_name": channel_name,
                    "message_type": message_type,
                    "sender_name": sender_name,
                    "content": content,
                    "created_at_iso": created_at_iso,
                    "agent_email": agent_email
                }
                
                transformed_messages.append(message_obj)
        
        print(f"✅ {len(transformed_messages)} mensagens processadas\n")
        return transformed_messages
    
    def save_to_json(self, data: List[Dict], filename: str = 'chatwoot_history_dump.json'):
        """
        Salva os dados em arquivo JSON
        
        Args:
            data: Lista de mensagens transformadas
            filename: Nome do arquivo de saída
        """
        print(f"💾 Salvando dados em {filename}...")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ Arquivo salvo com sucesso!")
            print(f"   Tamanho: {file_size_mb:.2f} MB")
            print(f"   Total de mensagens: {len(data)}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {str(e)}")
    
    def run(self):
        """Executa o processo completo de ETL"""
        print("=" * 60)
        print("🚀 CHATWOOT FULL ETL - EXTRACT")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Passo 1: Carregar mapeamento de canais
        if not self.load_inbox_map():
            print("❌ Falha ao carregar inboxes. Abortando...")
            return
        
        # Passo 2: Buscar todas as conversas (com paginação)
        conversations = self.get_all_conversations()
        
        if not conversations:
            print("⚠️  Nenhuma conversa encontrada")
            return
        
        # Passo 3: Transformar mensagens no formato desejado
        transformed_data = self.transform_messages(conversations)
        
        if not transformed_data:
            print("⚠️  Nenhuma mensagem para salvar")
            return
        
        # Passo 4: Salvar em JSON
        self.save_to_json(transformed_data)
        
        # Estatísticas finais
        elapsed_time = time.time() - start_time
        print()
        print("=" * 60)
        print("📊 ESTATÍSTICAS DA EXTRAÇÃO")
        print("=" * 60)
        print(f"⏱️  Tempo total: {elapsed_time:.2f} segundos")
        print(f"💬 Conversas processadas: {len(conversations)}")
        print(f"📨 Mensagens extraídas: {len(transformed_data)}")
        print(f"📁 Arquivo gerado: chatwoot_history_dump.json")
        print()
        print("✅ ETL concluído com sucesso!")
        print("=" * 60)


def main():
    """Função principal"""
    try:
        etl = ChatwootETL()
        etl.run()
    except ValueError as e:
        print(str(e))
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
