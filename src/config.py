from pathlib import Path

# ---------------------------------------------------------------------------
# Caminho raiz do cofre Obsidian.
# Altere para o caminho absoluto do seu vault antes de executar.
# ---------------------------------------------------------------------------
VAULT_ROOT: Path = Path.home() / "ObsidianVault"

# ---------------------------------------------------------------------------
# Modelo Ollama local.
# Hardware alvo: Apple M3 16 GB — mantenha modelos ≤ 8B parâmetros Q4 para
# não estrangular a RAM unificada.
# Valor padrão alinhado com SPEC_TECH.md; substitua por ex.: "llama3:8b-q4_K_M"
# ---------------------------------------------------------------------------
MODEL_NAME: str = "gemma4:31b-cloud"

# ---------------------------------------------------------------------------
# Parâmetros de resiliência para chamadas ao LLM
# ---------------------------------------------------------------------------
# Número máximo de tentativas antes de pular a nota
MAX_LLM_RETRIES: int = 3

# Delay base (segundos) usado no backoff exponencial entre tentativas
RETRY_BASE_DELAY: float = 2.0

# ---------------------------------------------------------------------------
# Configuração do servidor Ollama local
# ---------------------------------------------------------------------------
OLLAMA_HOST: str = "http://localhost:11434"
