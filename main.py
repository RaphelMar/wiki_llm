import logging
from pathlib import Path
from rich.console import Console

from src.config import OBSIDIAN_VAULT_PATH, CATEGORIAS_POSSIVEIS
from src.utils.git_manager import GitManager
from src.core.indexer import VaultIndexer
from src.core.llm_client import LangChainOllamaClient
from src.core.processor import MarkdownProcessor
from src.ui.cli import DiffViewer

INBOX_PATH = OBSIDIAN_VAULT_PATH / "Inbox"
WIKI_CORE_PATH = OBSIDIAN_VAULT_PATH / "Wiki Core"

# Configuração de Logs e UI
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
console = Console()

def main():
    console.print("[bold #d97757]Wiki LLM: Iniciando Pipeline de Processamento[/bold #d97757]\n")

    # 1. ESCUDO: Seguranca Git Inicial
    git = GitManager()
    git.setup_cold_start()
    git.commit_all("Backup Preventivo antes do processamento")

    # 2. CEREBRO: Indexacao do Cofre
    indexer = VaultIndexer(OBSIDIAN_VAULT_PATH)
    known_entities = indexer.get_all_terms_for_llm()
    categories = CATEGORIAS_POSSIVEIS

    # 3. MOTOR E MAOS: Instanciando Especialistas
    llm = LangChainOllamaClient()
    processor = MarkdownProcessor()

    # 4. FILA DE TRABALHO: Notas na Inbox
    inbox_files = list(INBOX_PATH.glob("*.md"))

    if not inbox_files:
        console.print("[#d97757]Nenhuma nota pendente na Inbox.[/#d97757]")
        return
    
    processed_count = 0

    for file_path in inbox_files:
        console.print(f"\n[bold cyan]Analisando:[/bold cyan] {file_path.name}...")

        # A. Inteligencia: Analise do LLM
        with open(file_path, "r", encoding= "utf-8") as f:
            content = f.read()

        analysis = llm.analyze_note(
            note_text= content,
            known_terms= known_entities,
            available_categories= categories
        )

        # B. Cirurgia: Preparacao em Memoria (RAM)
        updated_content = processor.prepare_updated_note(file_path, analysis)

        # C. Olhos: Revisao Humana
        if DiffViewer.review_changes(file_path.name, content, updated_content):
            # D. Açao: Salvar e Mover
            # 1. Salva o novo conteudo no ficheiro original primeiro
            file_path.write_text(updated_content, encoding= "utf-8")

            # 2. Determina o destino (Garante que a pasta existe)
            dest_folder = WIKI_CORE_PATH / analysis.categoria_destino
            dest_folder.mkdir(parents= True, exist_ok= True)

            dest_path = dest_folder / file_path.name

            # 3. Move o ficheiro (pathlib.Path.rename)
            file_path.rename(dest_path)

            console.print(f"[green]Ficheiro movido para:[/green] {analysis.categoria_destino}")
        
        else:
            console.print("[yellow]Alterações rejeitadas. Ficheiro mantido na Inbox.[/yellow]")

        # 5. FINALIZACAO: Commit de Fecho
        if processed_count > 0:
            git.commit_all(f"Agente processou {processed_count} notas com sucesso")
            console.print(f"\n[bold green]Sucesso! {processed_count} notas organizadas.[/bold green]")
        else:
             console.print("\n[dim]Nenhuma alteração foi persistida no cofre.[/dim]")

if __name__ == "__main__":
    main()   

            

