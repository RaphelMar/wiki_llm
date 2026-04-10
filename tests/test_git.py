import logging
from pathlib import Path
import tempfile

# Ajuste o import de acordo com onde você salvou a classe
from src.utils.git_manager import GitManager 

# Configuração simples de log para vermos o que está acontecendo
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def testar_fluxo_git():
    """
    Cria um diretório temporário efêmero (Sandbox) para testar o GitManager.
    O bloco 'with' garante que a pasta será deletada pelo SO ao final.
    """
    with tempfile.TemporaryDirectory(prefix="mock_vault_") as temp_dir_name:
        mock_vault = Path(temp_dir_name)
        logging.info(f"--- Iniciando Sandbox em: {mock_vault} ---")

        # 1. Instanciar o Manager
        git = GitManager(vault_path=mock_vault)

        # 2. Testar Cold Start (Deve inicializar o repo)
        logging.info("\n--- Teste 1: Cold Start ---")
        git.setup_cold_start()
        
        # Opcional: tentar rodar de novo para garantir que é O(1) rápido
        logging.info("Rodando Cold Start de novo (deve ser ignorado):")
        git.setup_cold_start()

        # 3. Testar Commit sem mudanças (Deve retornar 'no_changes')
        logging.info("\n--- Teste 2: Commit Vazio ---")
        resultado = git.commit_all("Backup sem mudanças")
        assert resultado == "no_changes", "Deveria ter detectado que não há mudanças."

        # 4. Simular o Agente criando uma nota na Inbox
        logging.info("\n--- Teste 3: Commit com Mudanças ---")
        inbox = mock_vault / "Inbox"
        inbox.mkdir()
        nova_nota = inbox / "ideia_genial.md"
        nova_nota.write_text("# Minha nova ideia\nIsso aqui vai ser incrível.")
        logging.info("Nota simulada criada na Inbox.")

        # 5. Fazer o backup (Deve gerar um hash de commit)
        hash_commit = git.commit_all("Backup de nova nota")
        assert hash_commit != "no_changes", "Deveria ter commitado a nova nota."
        logging.info(f"Sucesso! Hash do commit: {hash_commit}")

        logging.info("\n--- Fim do Teste. O Python apagará a Sandbox agora. ---")

if __name__ == "__main__":
    testar_fluxo_git()