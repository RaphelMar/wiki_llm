"""
Teste de integração para o cliente LLM (LangChain + Ollama).
Verifica o parse do Pydantic, restrições de categorias e o NOVO mapeamento de entidades.
"""
import logging
from src.core.llm_client import LangChainOllamaClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def testar_inferencia_llm_mapeada():
    logging.info("--- Iniciando Teste do Motor LLM (LangChain + Ollama) ---")
    
    try:
        client = LangChainOllamaClient()
    except Exception as e:
        logging.error(f"Erro ao inicializar o cliente: {e}")
        return

    # 1. Dados Simulados COM ARMADILHAS (Abreviações e Capslock)
    nota_teste = """
    # O poder da Eng. de Dados
    Hoje descobri que o POLARS usa multithreading em Rust sob o capô.
    É absurdo o que a eng. de dados tem feito ultimamente.
    Vou abandonar o Pandas clássico.
    """
    
    termos_conhecidos = ["python", "pandas", "polars", "engenharia de dados", "rust"]
    categorias_disponiveis = ["C1_Estudos", "C2_Projetos", "C3_Ferramentas", "Inbox"]

    logging.info("A enviar requisição. O M3 está a pensar no mapeamento...")
    
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
    logging.info("\n" + "="*50)
    logging.info(" RESULTADO ESTRUTURADO (PYDANTIC AVANÇADO)")
    logging.info("="*50)
    logging.info(f"Resumo Curto     : {resultado.resumo_curto}")
    logging.info(f"Tags             : {resultado.tags}")
    logging.info(f"Categoria Destino: {resultado.categoria_destino}")
    logging.info("\nMAPEAMENTO DE ENTIDADES:")
    
    if not resultado.entidades_encontradas:
        logging.info("  -> Nenhuma entidade mapeada.")
    else:
        for entidade in resultado.entidades_encontradas:
            logging.info(f"  -> Texto Original: '{entidade.termo_no_texto}' | Aponta para Nota: '{entidade.termo_canonico}'")
    logging.info("="*50 + "\n")

    assert isinstance(resultado.entidades_encontradas, list), "Falha: Entidades não é uma lista!"
    logging.info("--- Sucesso! O LLM compreendeu o mapeamento canônico. ---")

if __name__ == "__main__":
    testar_inferencia_llm_mapeada()