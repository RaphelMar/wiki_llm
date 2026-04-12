"""
Módulo central de configuração.
Carrega as variáveis do .env de forma simples, direta e resiliente.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# VARIÁVEIS DE AMBIENTE 
# ==========================================
OBSIDIAN_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", ""))

# Modelos para estratégia de Fallback
MODEL_NAME_CLOUD = os.getenv("MODEL_NAME_CLOUD", "gemma4:31b-cloud")
MODEL_NAME_LOCAL = os.getenv("MODEL_NAME_LOCAL", "gemma3:4b")

# System Prompt
# 1. Encontra a raiz absoluta do seu projeto (a pasta wiki_llm/)
BASE_DIR = Path(__file__).parent.parent

# 2. Puxa a string do .env, e cria um Path real juntando com a raiz
_caminho_prompt_env = os.getenv("SYSTEM_PROMPT_PATH", "prompts/system_prompt.md")
SYSTEM_PROMPT_PATH = BASE_DIR / _caminho_prompt_env


# Parâmetros de Resiliência (Tipados como inteiros)
MAX_LLM_RETRIES = int(os.getenv("MAX_LLM_RETRIES", 3))
RETRY_BASE_DELAY = int(os.getenv("RETRY_BASE_DELAY", 2))

# ==========================================
# VALIDAÇÃO RÁPIDA (Cold Start)
# ==========================================
if not str(OBSIDIAN_VAULT_PATH) or not OBSIDIAN_VAULT_PATH.exists():
    logger.error(
        f"ALERTA: O caminho do cofre fornecido no .env não existe ou está vazio: '{OBSIDIAN_VAULT_PATH}'"
    )