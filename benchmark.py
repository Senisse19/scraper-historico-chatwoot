#!/usr/bin/env python3
"""
Script de Benchmark - Chatwoot ETL Extractor
Testa e compara performance com e sem otimizações
"""

import time
import json
from datetime import datetime, timedelta
from chatwoot_etl import ChatwootETL

def format_time(seconds):
    """Formata tempo em formato legível"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"

def run_benchmark():
    """Executa benchmark das otimizações"""
    print("=" * 70)
    print("🏁 BENCHMARK - CHATWOOT ETL PERFORMANCE")
    print("=" * 70)
    print()
    
    # Configuração do teste
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Última semana
    
    results = {}
    
    # Teste 1: Modo Paralelo (Otimizado)
    print("📊 Teste 1: Modo PARALELO (10 workers) + Rate Limiting Adaptativo")
    print("-" * 70)
    
    try:
        etl_parallel = ChatwootETL(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        etl_parallel.max_workers = 10
        etl_parallel.adaptive_rate_limit = True
        
        start_time = time.time()
        
        # Executa ETL
        if etl_parallel.load_inbox_map():
            conversations = etl_parallel.get_all_conversations()
            if conversations:
                conversations = etl_parallel.filter_conversations_by_date(conversations)
                messages = etl_parallel.transform_messages(conversations)
                
                elapsed = time.time() - start_time
                results['parallel'] = {
                    'time': elapsed,
                    'conversations': len(conversations),
                    'messages': len(messages),
                    'avg_time_per_conv': elapsed / len(conversations) if conversations else 0
                }
                
                print(f"✅ Concluído em: {format_time(elapsed)}")
                print(f"   Conversas: {len(conversations)}")
                print(f"   Mensagens: {len(messages)}")
                print(f"   Tempo médio/conversa: {results['parallel']['avg_time_per_conv']:.2f}s")
        else:
            print("❌ Falha ao carregar inbox map")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print()
    
    # Teste 2: Modo Sequencial (Sem paralelização)
    print("📊 Teste 2: Modo SEQUENCIAL (1 worker) + Rate Limiting Fixo")
    print("-" * 70)
    
    try:
        etl_sequential = ChatwootETL(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        etl_sequential.max_workers = 1  # Desabilita paralelização
        etl_sequential.adaptive_rate_limit = False
        etl_sequential.rate_limit_delay = 0.5
        
        start_time = time.time()
        
        # Executa ETL
        if etl_sequential.load_inbox_map():
            conversations = etl_sequential.get_all_conversations()
            if conversations:
                conversations = etl_sequential.filter_conversations_by_date(conversations)
                messages = etl_sequential.transform_messages(conversations)
                
                elapsed = time.time() - start_time
                results['sequential'] = {
                    'time': elapsed,
                    'conversations': len(conversations),
                    'messages': len(messages),
                    'avg_time_per_conv': elapsed / len(conversations) if conversations else 0
                }
                
                print(f"✅ Concluído em: {format_time(elapsed)}")
                print(f"   Conversas: {len(conversations)}")
                print(f"   Mensagens: {len(messages)}")
                print(f"   Tempo médio/conversa: {results['sequential']['avg_time_per_conv']:.2f}s")
        else:
            print("❌ Falha ao carregar inbox map")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print()
    
    # Comparação de resultados
    if 'parallel' in results and 'sequential' in results:
        print("=" * 70)
        print("📈 ANÁLISE COMPARATIVA")
        print("=" * 70)
        print()
        
        time_saved = results['sequential']['time'] - results['parallel']['time']
        improvement = (time_saved / results['sequential']['time']) * 100
        speedup = results['sequential']['time'] / results['parallel']['time']
        
        print(f"⏱️  Tempo Sequencial: {format_time(results['sequential']['time'])}")
        print(f"⏱️  Tempo Paralelo:   {format_time(results['parallel']['time'])}")
        print(f"💾 Tempo Economizado: {format_time(time_saved)} ({improvement:.1f}% mais rápido)")
        print(f"🚀 Speedup:          {speedup:.2f}x")
        print()
        
        # Salva resultados
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'results': results,
            'analysis': {
                'time_saved_seconds': time_saved,
                'improvement_percentage': improvement,
                'speedup_factor': speedup
            }
        }
        
        with open('exports/benchmark_results.json', 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, ensure_ascii=False, indent=2)
        
        print("📁 Resultados salvos em: exports/benchmark_results.json")
        print()
        
        # Recomendações
        print("=" * 70)
        print("💡 RECOMENDAÇÕES")
        print("=" * 70)
        print()
        
        if improvement >= 70:
            print("🎉 EXCELENTE! As otimizações estão funcionando perfeitamente!")
        elif improvement >= 50:
            print("✅ BOM! As otimizações estão trazendo ganhos significativos.")
        elif improvement >= 30:
            print("⚠️  MODERADO. Considere aumentar max_workers se a API permitir.")
        else:
            print("⚠️  BAIXO. Verifique se há gargalos de rede ou API lenta.")
        
        print()
        print(f"⚙️  Configuração atual:")
        print(f"   - max_workers: {etl_parallel.max_workers}")
        print(f"   - adaptive_rate_limit: {etl_parallel.adaptive_rate_limit}")
        print(f"   - rate_limit_delay: {etl_parallel.rate_limit_delay}s")
        print()
    
    print("=" * 70)
    print("✅ Benchmark concluído!")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmark()
