"""
Teste isolado para a Interface Gráfica do Terminal (Rich).
"""
from src.ui.cli import DiffViewer

def testar_interface():
    nome_arquivo = "estudo_de_dados.md"
    
    # Simulando o estado ANTES do Processador
    texto_velho = "Hoje estudei sobre eng. de dados.\nFoi muito bom."
    
    # Simulando o estado DEPOIS do Processador
    texto_novo = "---\nagente_revisao: 2026-04-12\ntags: [estudos, dados]\n---\nHoje estudei sobre [[Engenharia de Dados|eng. de dados]].\nFoi muito bom."

    # Chama a UI
    aprovado = DiffViewer.review_changes(nome_arquivo, texto_velho, texto_novo)
    
    if aprovado:
        print("\n✅ Usuário aprovou as mudanças. O Processador salvaria no disco agora.")
    else:
        print("\n❌ Usuário rejeitou. Arquivo original mantido intacto.")

if __name__ == "__main__":
    testar_interface()