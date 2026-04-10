from pathlib import Path
import subprocess
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitManager:
    """
    Wrapper de segurança para operações de Git, garantindo que o cofre
    esteja versionado antes e depois de edições automatizadas.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def _run_command(self, command: list[str]) -> str:
        """Executa um comando shell e retorna a saída."""
        try:
            result = subprocess.run(
                command,
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando Git: {e.stderr}")
            raise RuntimeError(f"Falha no comando Git: {e.stderr}")

    def is_git_repo(self) -> bool:
        """Verifica se o caminho fornecido é um repositório Git válido."""
        try:
            # Verifica a existência da pasta .git
            if not (self.vault_path / ".git").exists():
                return False
            # Executa git rev-parse para confirmar que é um repo válido
            self._run_command(["git", "rev-parse", "--is-inside-work-tree"])
            return True
        except Exception:
            return False

    def commit_all(self, message_prefix: str = "Auto-backup agente") -> str:
        """
        Executa git add . e git commit com timestamp.
        Retorna o hash do commit se bem sucedido.
        """
        if not self.is_git_repo():
            raise RuntimeError(f"O diretório {self.vault_path} não é um repositório Git válido.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{message_prefix} - {timestamp}"

        # git add .
        self._run_command(["git", "add", "."])

        # git commit -m "message"
        try:
            self._run_command(["git", "commit", "-m", full_message])
            logger.info(f"Commit realizado com sucesso: {full_message}")
            return self._run_command(["git", "rev-parse", "HEAD"])
        except RuntimeError as e:
            if "nothing to commit" in str(e).lower():
                logger.info("Nada para commitar.")
                return "no_changes"
            raise e
