
import logging
import time
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from src.config import (
    MAX_LLM_RETRIES, 
    RETRY_BASE_DELAY, 
    MODEL_NAME_CLOUD, 
    MODEL_NAME_LOCAL,
    SYSTEM_PROMPT_PATH
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema Pydantic — Saída estruturada do LLM
# ---------------------------------------------------------------------------
class EntidadeMapeada(BaseModel):
    termo_no_texto: str = Field(..., description="A palavra ou frase EXATA como está escrita no corpo da nota (mantendo maiúsculas/minúsculas).")
    termo_canonico: str = Field(..., description="O nome oficial da entidade no Índice de Termos.")

class AnaliseLLM(BaseModel):
    resumo_curto: str = Field(..., description="Resumo de no máximo 2 linhas.")
    tags: list[str] = Field(..., description="Lista de 3 a 5 tags descritivas em minúsculas.")
    aliases: list[str] = Field(..., description="Sinônimos curtos para o tema da nota.")
    categoria_destino: str = Field(..., description="A PASTA EXATA escolhida dentre as opções válidas fornecidas.")
    entidades_encontradas: list[EntidadeMapeada] = Field(..., description="Mapeia o termo exato encontrado no texto para a entidade oficial do índice.")

# ---------------------------------------------------------------------------
# Cliente LLM com LCEL e Validação Rigorosa
# ---------------------------------------------------------------------------
class LangChainOllamaClient:
    """Cliente robusto utilizando LCEL para extração de dados determinística."""
    
    def __init__(self, max_retries: int = MAX_LLM_RETRIES):
        self.max_retries = max_retries
        self._system_prompt_content = self._load_prompt()
        
        # 1. Instanciamos o LLM com as restrições máximas de criatividade
        self.llm_cloud = ChatOllama(
            model=MODEL_NAME_CLOUD,
            temperature=0.1,
            format="json"  # Força o backend do Ollama a travar em JSON mode
        )

        self.llm_local = ChatOllama(
            model=MODEL_NAME_LOCAL,
            temperature=0.1,
            format="json"  # Força o backend do Ollama a travar em JSON mode
        )
        
        self.llm = self.llm_cloud.with_fallbacks([self.llm_local])

        # 2. Instanciamos o Parser mágico do LangChain
        self.parser = PydanticOutputParser(pydantic_object=AnaliseLLM)
        
        # 3. Montamos o Template injetando as instruções de formato geradas pelo parser
        full_system_template = (
            self._system_prompt_content + 
            "\n\nINSTRUÇÕES DE FORMATAÇÃO OBRIGATÓRIAS:\n{format_instructions}"
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", full_system_template),
            ("human", "CATEGORIAS DISPONÍVEIS:\n{categorias_validas}\n\nÍNDICE DE TERMOS:\n{indice_termos}\n\nNOTA A SER PROCESSADA:\n{nota_texto}")
        ])

        # 4. A Coroa do LCEL: Composição limpa e encadeada
        self._chain = self.prompt_template | self.llm | self.parser

    def _load_prompt(self) -> str:
        if not SYSTEM_PROMPT_PATH.exists():
            raise FileNotFoundError(f"Arquivo de prompt não encontrado: {SYSTEM_PROMPT_PATH}")
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def analyze_note(
        self, 
        note_text: str, 
        known_terms: list[str], 
        available_categories: list[str]
    ) -> AnaliseLLM:
        """
        Executa a chain com retry. Retorna o objeto AnaliseLLM perfeitamente tipado.
        """
        # Garante fallback seguro
        if not available_categories:
            available_categories = ["Inbox"]

        last_error = None
        
        # As variáveis que o prompt precisa
        inputs = {
            "nota_texto": note_text,
            "indice_termos": ", ".join(known_terms) if known_terms else "Nenhum termo prévio.",
            "categorias_validas": ", ".join(available_categories),
            "format_instructions": self.parser.get_format_instructions() # Injeção da mágica
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"LangChain (Ollama) [Tentativa {attempt}/{self.max_retries}] - Analisando nota...")
                
                # A mágica acontece aqui. O LangChain chama o Ollama, recebe a string,
                # remove as crases e converte pro Pydantic sozinho. O retorno já é a classe instanciada!
                resultado_validado: AnaliseLLM = self._chain.invoke(inputs)
                
                # Validação de Negócio Extra (Fail Fast)
                if resultado_validado.categoria_destino not in available_categories:
                    raise OutputParserException(f"Alucinação: Categoria '{resultado_validado.categoria_destino}' não existe.")
                
                logger.info("JSON validado perfeitamente pelo pipeline LCEL.")
                return resultado_validado

            except OutputParserException as e:
                last_error = e
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Erro de Schema na tentativa {attempt}: {e}. Aguardando {delay}s...")
                time.sleep(delay)
            except Exception as e:
                # Erros de conexão ou timeout do Ollama
                last_error = e
                logger.error(f"Erro crítico de I/O na tentativa {attempt}: {e}")
                time.sleep(2)

        # Fallback após esgotar tentativas
        logger.error("Todas as tentativas falharam. Usando Fallback.")
        return AnaliseLLM(
            resumo_curto="Falha ao analisar a nota. Necessário revisão manual.",
            tags=["necessita-revisao"],
            aliases=[],
            categoria_destino="Inbox",
            entidades_encontradas=[]
        )