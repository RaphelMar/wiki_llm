import difflib
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text

# Instancia global do console do Rich
console = Console()

class DiffViewer:
    """Classe responsavel por renderizar a comparacao de notas no terminal"""

    def review_changes(filename: str, original_text: str, modified_text: str) -> bool:
        """
        Gera um diff no estilo Git e pede confirmacao do usuario.
        Retorna True se aprovado, False se rejeitado.
        """
        # Se a IA/Regex nao alterou absulutamente nada
        if original_text == modified_text:
            console.print(f"[dim]Nenhuma alteração necessária em: {filename}[/dim]")
            return True
        
        # Gera o diff unificado (igual ao "git diff")
        diff = list(
            difflib.unified_diff(
                original_text.splitlines(keepends=True),
                modified_text.splitlines(keepends=True),
                fromfile="Estado Original",
                tofile="Modificado (LLM + Regex)",
                n= 3 # Quantidade de linhas de contexto ao redor da mudança
            )
        )

        # Colore o texto interando linha por linha
        diff_text = Text()
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                diff_text.append(line, style= "bold white")
            elif line.startswith("+"):
                # O verde vai se destacar perfeitamente o YAML injetado e os [[links]]
                diff_text.append(line, style= "bold green")
            elif line.startswith("-"):
                # O vermelho mostra oque foi retirado/substituido
                diff_text.append(line, style= "bold red")
            elif line.startswith("@@"):
                diff_text.append(line, style= "cyan")
            else:
                diff_text.append(line, style= "dim white")

        # Embala o Diff num painel bonito
        painel = Panel(
            diff_text,
            title= f"Revisão Pendente: [bold #d97757]{filename}[/bold #d97757]",
            border_style= "#d97757"
        )
        console.print(painel)
        console.print()
        return Confirm.ask(f"Deseja aplicar estas alterações em [#d97757]{filename}[/#d97757]")