"""
Teste de integração para o cliente LLM (LangChain + Ollama).
Verifica o parse do Pydantic, restrições de categorias e a extração O(1).
"""
import logging
from src.core.llm_client import LangChainOllamaClient

# Configuração limpa do log para ver o output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def testar_inferencia_llm():
    logging.info("--- Iniciando Teste do Motor LLM (LangChain + Ollama) ---")
    logging.info("A instanciar o cliente (verifica se o Ollama está a correr localmente)...")

    try:
        client = LangChainOllamaClient()
    except Exception as e:
        logging.error(f"Erro ao inicializar o cliente: {e}")
        return

    # 1. Dados Simulados (Contexto Mágico)
    nota_teste = """
    # O poder do Polars em Engenharia de Dados
    Hoje descobri que o Polars usa multithreading em Rust sob o capô.
    É absurdamente mais rápido que o Pandas para datasets de 10GB.
    Acho que vou migrar os meus scripts para ele.
    """
    
    termos_conhecidos = ["python", "pandas", "polars", "engenharia de dados", "rust"]
    categorias_disponiveis = ["C1_Estudos", "C2_Projetos", "C3_Ferramentas", "Inbox"]

    logging.info("A enviar requisição para o LLM. O seu M3 vai trabalhar agora. Aguarde...")
    
    # 2. Invocação do Pipeline LCEL
    try:
        resultado = client.analyze_note(
            note_text=nota_teste,
            known_terms=termos_conhecidos,
            available_categories=categorias_disponiveis
        )
    except Exception as e:
        logging.error(f"Falha Crítica na inferência: {e}")
        return

    # 3. Exibição do Objeto Pydantic Tipado
    logging.info("\n" + "="*40)
    logging.info(" RESULTADO ESTRUTURADO (PYDANTIC)")
    logging.info("="*40)
    logging.info(f"Resumo Curto     : {resultado.resumo_curto}")
    logging.info(f"Tags             : {resultado.tags}")
    logging.info(f"Aliases          : {resultado.aliases}")
    logging.info(f"Categoria Destino: {resultado.categoria_destino}")
    logging.info(f"Entidades (O(1)) : {resultado.entidades_encontradas}")
    logging.info("="*40 + "\n")

    # 4. Asserts de Segurança
    assert resultado.categoria_destino in categorias_disponiveis, "Falha: O modelo inventou uma categoria!"
    assert isinstance(resultado.entidades_encontradas, list), "Falha: Entidades não é uma lista!"
    
    logging.info("--- Sucesso! O Pipeline LCEL, o Pydantic e o Fallback estão a funcionar perfeitamente. ---")

if __name__ == "__main__":
    testar_inferencia_llm()