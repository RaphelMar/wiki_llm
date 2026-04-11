import logging
from pathlib import Path
import frontmatter
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class Indexer:
    """
    Indexador de Alta Performance em RAM.
    Varre 'Wiki Core/' de forma otimizada para evitar leitura de arquivos sem YAML.
    """
    def __init__(self, vault_root: Path):
        self.core_path = vault_root / "Wiki Core"
        # Mapeamento para saber onde o termo está (termo_em_minusculo -> Caminho)
        self.index: Dict[str, Path] = {}
        # Tabela Hash de busca instantânea O(1)
        self.known_terms: Set[str] = set()

    def _has_yaml_frontmatter(self, file_path: Path) -> bool:
        """Lê apenas a primeira linha do arquivo para economizar I/O e RAM."""
        try:
            with file_path.open('r', encoding='utf-8') as f:
                first_line = f.readline()
                return first_line.startswith("---")
        except Exception:
            return False

    def _add_to_index(self, term: str, path: Path):
        """Auxiliar que garante a normalização da string antes de injetar na RAM."""
        if term:
            normalized_term = term.strip().lower()
            self.index[normalized_term] = path
            self.known_terms.add(normalized_term)

    def scan(self) -> Dict[str, Path]:
        """Varre o diretório construindo o índice com proteção de memória."""
        if not self.core_path.exists():
            logger.warning(f"Cold Start: Diretório {self.core_path} não existe. Retornando índice vazio.")
            return {}
        
        total_files = 0
        logger.info(f"Iniciando indexação em: {self.core_path}")

        for md_file in self.core_path.rglob("*.md"):
            total_files += 1

            # O nome do arquivo (sem extensão) sempre é um titulo valido
            title = md_file.stem
            aliases: List[str] = []

            # So carrega o frontmatter inteiro SE tivermos certeza que tem YAML
            if self._has_yaml_frontmatter(md_file):
                try:
                    post = frontmatter.load(md_file)
                    title = post.get("title", title)
                    raw_aliases = post.get("aliases", [])
                    if isinstance(raw_aliases, list):
                        aliases = [str(a) for a in raw_aliases]
                    elif isinstance(raw_aliases, str):
                        aliases = [raw_aliases]

                except Exception as e:
                    logger.error(f"Frontmatter corrompido em {md_file.name}: {e}")

            # Registra no indice com normalizacao
            self._add_to_index(title, md_file)
            for alias in aliases:
                self._add_to_index(alias, md_file)

        logger.info(f"Indexação concluída. {len(self.known_terms)} termos únicos extraídos de {total_files} notas.")
        return self.index

    def is_known_entity(self, term: str) -> bool:
        """Busca O(1) para o pipeline em Python."""
        return term.strip().lower() in self.known_terms

    def get_all_terms_for_llm(self) -> List[str]:
        """Retorna uma lista para injeção no prompt do LLM."""
        return list(self.known_terms)
