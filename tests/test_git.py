"""
Testes unitários para o GitManager.
Usa Mock para impedir que operações afetem o cofre real do utilizador.
"""
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch

from src.utils.git_manager import GitManager

logging.basicConfig(level=logging.INFO)

def test_fluxo_git_seguro():
    """Testa o Cold Start e o LBYL (Look Before You Leap) numa Sandbox."""
    
    with tempfile.TemporaryDirectory(prefix="mock_vault_") as temp_dir:
        mock_vault_path = Path(temp_dir)
        
        # A MÁGICA: Substituímos o valor de OBSIDIAN_VAULT_PATH dentro do módulo git_manager
        # APENAS enquanto este bloco 'with' estiver a correr.
        with patch('src.utils.git_manager.OBSIDIAN_VAULT_PATH', mock_vault_path):
            
            manager = GitManager()
            
            logging.info(f"--- Sandbox Iniciada em: {mock_vault_path} ---")
            
            # 1. Testar Cold Start
            assert not manager.is_git_repo(), "A sandbox deveria começar vazia!"
            manager.setup_cold_start()
            assert manager.is_git_repo(), "O repositório não foi inicializado!"
            assert (mock_vault_path / ".gitignore").exists(), "O escudo do Obsidian não foi injetado!"
            
            # 2. Testar LBYL (Tentar comitar sem mudanças)
            resultado = manager.commit_all("Backup Fantasma")
            assert resultado == "no_changes", "O GitManager comitou o que não devia!"
            
            # 3. Testar Commit Real
            nova_nota = mock_vault_path / "ideia_brilhante.md"
            nova_nota.write_text("Esta ideia vai mudar o mundo.", encoding="utf-8")
            
            resultado = manager.commit_all("Backup Real")
            assert resultado != "no_changes", "O GitManager ignorou a nova nota!"
            assert isinstance(resultado, str) and len(resultado) > 0, "Não retornou o Hash do commit."
            
            logging.info("--- Sucesso Absoluto! A destruir a Sandbox... ---")

if __name__ == "__main__":
    test_fluxo_git_seguro()