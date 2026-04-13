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

# Sessao de Categorias do Wiki
CATEGORIAS_PERMITIDAS = [
    # --- TECNOLOGIA E DADOS ---
    "01_Tech/Engenharia_de_Dados",
    "01_Tech/IA_&_Machine_Learning",
    "01_Tech/Desenvolvimento_Python",
    "01_Tech/Linux_&_Open_Source",
    "01_Tech/Infraestrutura_&_Cloud",
    "01_Tech/Carreira_&_Educação",

    # --- GEOPOLÍTICA E MUNDO ---
    "02_Mundo/Conflitos_&_Guerras",
    "02_Mundo/Analise_Geopolitica",
    "02_Mundo/Relacoes_Internacionais",
    "02_Mundo/Teoria_Politica",

    # --- ESPIRITUALIDADE E FÉ ---
    "03_Espiritualidade/Teologia_Catolica",
    "03_Espiritualidade/Estudos_Biblicos",
    "03_Espiritualidade/Sermoes_&_Pregacoes",
    "03_Espiritualidade/Historia_da_Igreja",

    # --- HUMANIDADES E PENSAMENTO ---
    "04_Humanidades/Filosofia_&_Etica",
    "04_Humanidades/Psicologia_&_Mente",
    "04_Humanidades/Historia_Geral",
    "04_Humanidades/Sociologia_&_Cultura",

    # --- SOBREVIVENCIALISMO E VIDA ---
    "05_Vida/Preparacionismo_&_Bushcraft",
    "05_Vida/Ferramentas_&_Equipamentos",
    "05_Vida/Auto_Suficiencia",

    # --- MÍDIA E ENTREVISTAS ---
    "06_Midia/Entrevistas_Longas",
    "06_Midia/Insights_de_Podcasts",
    "06_Midia/Cinema_&_Critica",
    "06_Midia/Musica_&_Teoria",

    # --- LITERATURA E GÊNEROS ---
    "07_Ficcao/Terror_&_Gotico",
    "07_Ficcao/Ficcao_Cientifica_&_Distopia",
    "07_Ficcao/Suspense_&_Policial",
    "07_Ficcao/Literatura_Classica",
    "08_Nao_Ficcao/Biografias_&_Perfis",
    "08_Nao_Ficcao/Livros_Tecnicos",

    # --- SISTEMA ZETTELKASTEN ---
    "Zettelkasten/Notas_Tecnicas",
    "Zettelkasten/Principios_Pessoais",
    "Zettelkasten/Notas_Permanentes",
    "Inbox" # Fallback essencial
]