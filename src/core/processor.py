import re
import logging
import frontmatter
from pathlib import Path
from datetime import date
from typing import List

from src.core.llm_client import AnaliseLLM, EntidadeMapeada

logger = logging.getLogger(__name__)

class MarkdownProcessor:
    """Classe utilitaria para manipulacao segura de AST de Markdown"""
    def _inject_yaml(self, post: frontmatter.Post, analysis: AnaliseLLM) -> None:
        """Mescla as conclusoes do LLM com o YAML existente sem destruir dados."""
        post.metadata["resumo"] = analysis.resumo_curto
        post.metadata["tag"] = analysis.tags

        # Mantemos aliases existentes e adicionamos os novos (evitando duplicacao)
        existing_aliases = post.metadata.get("aliases", [])
        if isinstance(existing_aliases, str):
            existing_aliases = [existing_aliases]

        merged_aliases = list(set(existing_aliases + analysis.aliases))
        if merged_aliases:
            post.metadata["aliases"] = merged_aliases

        # Carimbo de auditoria (para sabermos que a IA ja processou isso)
        post.metadata["agente_revisao"] = str(date.today())

    def _inject_links(self, content: str, entities: List[EntidadeMapeada]) -> str:
        """"
        Injeta colchetes duplos nas entidades encontradas usando Regex avancada.
        Garante que links existentes nao sejam quebrados
        """
        # Ordena pelo tamanho do "termo_no_texto" (do maior para o menor)
        # se voce tiver "eng. de dados" e "dados", ele substitui a frase maior primeiro!
        sorted_entities = sorted(entities, key= lambda e: len(e.termo_no_texto), reverse= True)

        for entity in sorted_entities:
            termo_exato = entity.termo_no_texto
            canonico = entity.termo_canonico

            # Regex:
            # (?<!\[\[) -> Ignora se ANTES já tiver "[["
            # \b        -> Limite de palavra (evita substituir "andas" dentro de "pandas")
            # (?!\]\])  -> Ignora se DEPOIS já tiver "]]"
            pattern = re.compile(
                rf"(?<!\[\[)\b({re.escape(termo_exato)})\b(?!\]\])", 
                flags=re.IGNORECASE
            )
            
            # \1 pega exatamente como estava no texto (com maiúsculas originais)
            content = pattern.sub(rf"[[{canonico}|\1]]", content)

        return content

    def process_file(self, file_path: Path, analysis: AnaliseLLM) -> bool:
        """"
        Le a nota, injeta os metadados do LLM e aplica os links cruzados
        """
        try:
            # 1. Parsing Inteligente: Separa o YAML do Texto
            post = frontmatter.load(file_path)

            # 2. Injeta/Atauliza Frontmatter
            self._inject_yaml(post, analysis)

            # 3. Cirurgia de Regex:
            if analysis.entidades_encontradas:
                post.content = self._inject_links(post.content, analysis.entidades_encontradas)

            # 4. Grava de volta no disco
            with file_path.open('w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            logger.info(f"Cirurgia concluida na nota: {file_path.name}")
            return True
        
        except Exception as e:
            logger.error(f"Falha ao processar a nota {file_path.name}: {e}")
            return False
        
