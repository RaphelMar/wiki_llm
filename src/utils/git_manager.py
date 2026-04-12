from pathlib import Path
import subprocess
from datetime import datetime
import logging
import os

from src.config import OBSIDIAN_VAULT_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitManager:
    """
    Wrapper de segurança O(1) em RAM para operações de Git, garantindo que o cofre
    esteja versionado antes e depois de edições automatizadas.
    """

    def __init__(self):
        self.vault_path = OBSIDIAN_VAULT_PATH
        self._env = os.environ.copy()
        self._env["LC_ALL"] = "C" # Forca o Git sempre responder em ingles

    def _run_command(self, command: list[str]) -> str:
        """Executa um comando shell de forma síncrona com timeout implícito e retorna a saída."""
        try:
            result = subprocess.run(
                command,
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                check=True,
                env=self._env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or e.stdout.strip()
            logger.error(f"Erro ao executar comando Git: {command[1]}: {error_msg}")
            raise RuntimeError(f"Falha no comando Git: {error_msg}") from e

    def is_git_repo(self) -> bool:
        """Verifica de forma determinística se é um repositório."""
        if not (self.vault_path / ".git").exists():
            return False
        
        try:
            # Executa git rev-parse para confirmar que é um repo válido
            self._run_command(["git", "rev-parse", "--is-inside-work-tree"])
            return True
        except RuntimeError:
            return False

    def setup_cold_start(self) -> None:
        """
        Garante que o cofre é um repositório Git. Se não for, inicializa (Cold Start),
        cria um .gitignore protetor e faz o commit raiz.
        """
        if self.is_git_repo():
            return  # Já está tudo certo, sai da função rápido O(1)

        logger.info(f"Cold Start detectado. Inicializando repositório Git em: {self.vault_path}")
        self._run_command(["git", "init"])
        
        # Proteção contra lixo do macOS e cache do Obsidian
        gitignore_path = self.vault_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(
                ".DS_Store\n"
                ".obsidian/workspace\n"
                ".obsidian/workspace-mobile.json\n"
                "__pycache__/\n"
                "*.log\n",
                encoding="utf-8"
            )
            logger.info("Arquivo .gitignore injetado para proteger o histórico.")

        # Realiza o "Initial Commit" para criar a árvore raiz do Git
        self._run_command(["git", "add", "."])
        self._run_command(["git", "commit", "-m", "feat(vault): commit inicial (Cold Start)"])
        logger.info("Repositório inicializado e base de conhecimento assegurada.")

    def commit_all(self, message_prefix: str = "Auto-backup agente") -> str:
        """
        Executa backup condicional do cofre com base em diffs reais.
        """
        if not self.is_git_repo():
            raise RuntimeError(f"O diretório {self.vault_path} não é um repositório Git válido.")

        # LBYL: Look Before You Leap -> Padrão seguro para sub-processos
        status = self._run_command(["git", "status", "--porcelain"])
        if not status:
            logger.info("Nenhuma modificação detectada. Pulando commit.")
            return "no_changes"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{message_prefix} - {timestamp}"

        self._run_command(["git", "add", "."])
        self._run_command(["git", "commit", "-m", full_message])

        logger.info(f"Backup de segurança concluído: {full_message}")
        return self._run_command(["git", "rev-parse", "HEAD"])

