import logging
import tempfile
from pathlib import Path

# Ajuste o import se a sua estrutura estiver diferente
from src.core.indexer import Indexer

# Configuração simples de log para o terminal
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def testar_fluxo_indexer():
    """
    Cria uma Sandbox para testar a indexação O(1), simulando notas
    com e sem frontmatter YAML, garantindo que o "Peek Head" funciona.
    """
    with tempfile.TemporaryDirectory(prefix="mock_vault_") as temp_dir_name:
        mock_vault = Path(temp_dir_name)
        core_dir = mock_vault / "Wiki Core"
        core_dir.mkdir(parents=True)

        logging.info(f"--- Iniciando Sandbox em: {mock_vault} ---")

        # Cenário 1: Nota Bruta (A maioria das suas notas atuais)
        nota_crua = core_dir / "Ideia Genial.md"
        nota_crua.write_text("# Meu texto limpo\nNão tenho YAML aqui.", encoding="utf-8")

        # Cenário 2: Nota Padrão com YAML
        nota_yaml = core_dir / "Linguagem Python.md"
        nota_yaml.write_text(
            "---\n"
            "title: Python 3.13 Avançado\n"
            "aliases: [\"python\", \"python sênior\"]\n"
            "---\n"
            "Corpo da nota sobre Python.", 
            encoding="utf-8"
        )

        # Cenário 3: Nota com YAML frágil (Alias não é array)
        nota_fragil = core_dir / "Machine Learning.md"
        nota_fragil.write_text(
            "---\n"
            "aliases: ML\n"
            "---\n"
            "Corpo da nota sobre ML.", 
            encoding="utf-8"
        )

        # 1. Instanciar e varrer o cofre
        logging.info("\n--- Iniciando Varrer (Scan) ---")
        indexer = Indexer(vault_root=mock_vault)
        indexer.scan()

        # 2. Assertivas (O código vai quebrar se as checagens falharem)
        logging.info("\n--- Verificando Tabela Hash (Case Insensitive) ---")
        
        # Testando Cenário 1 (Fallback pro nome do arquivo)
        assert indexer.is_known_entity("ideia genial"), "Falhou na nota crua!"
        
        # Testando Cenário 2 (Prioridade pro YAML title e parsing de lista)
        assert indexer.is_known_entity("python 3.13 avançado"), "Falhou no title do YAML!"
        assert indexer.is_known_entity("python sênior"), "Falhou na lista de aliases!"
        
        # Testando Cenário 3 (Tratamento de string solta no YAML)
        assert indexer.is_known_entity("machine learning"), "Falhou no nome base (fallback)!"
        assert indexer.is_known_entity("ml"), "Falhou na string solta do YAML!"

        # 3. Validar a exportação para o LLM
        logging.info("\n--- Termos Otimizados para o LLM ---")
        termos = indexer.get_all_terms_for_llm()
        for t in sorted(termos):
            logging.info(f" - {t}")

        logging.info("\n--- Sucesso! Todos os Edge Cases passaram. Sandbox será destruída. ---")

if __name__ == "__main__":
    testar_fluxo_indexer()