"""
Testes unitários — Task 3: LLMClient (LangChain LCEL)

Estratégia: mock de `_chain.invoke` para isolar completamente a rede/GPU.
Cenários cobertos:
  1. Resposta válida → retorna AnaliseLLM correto.
  2. JSON malformado nas primeiras tentativas → recupera na 3ª tentativa.
  3. Todas as tentativas falham → levanta RuntimeError.
  4. Categoria inválida retornada pelo LLM → levanta RuntimeError após retries.
  5. LLM retorna JSON com markdown fence → fence é removida corretamente.
  6. load_categories_from_vault com diretório existente → retorna categorias.
  7. load_categories_from_vault sem 'Wiki Core/' → retorna lista vazia (cold start).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.llm_client import AnaliseLLM, LLMClient, load_categories_from_vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_ANALYSIS = {
    "resumo_curto": "Nota sobre pipelines de dados com Apache Kafka.",
    "tags": ["kafka", "streaming", "dados", "pipeline"],
    "aliases": ["Apache Kafka", "Kafka Streams"],
    "categoria_destino": "Engenharia_de_Dados",
    "entidades_encontradas": ["Apache Kafka", "Python"],
}

CATEGORIES = ["Engenharia_de_Dados", "Estudos_LLM", "Desenvolvimento_Pessoal"]
KNOWN_TERMS = ["apache kafka", "python", "spark", "dbt"]
NOTE_TEXT = "Esta nota fala sobre Apache Kafka e Python para processar streams."


def _make_client(tmp_path: Path, **kwargs) -> LLMClient:
    """
    Cria um LLMClient apontando para um system_prompt temporário.
    O ChatOllama é inicializado normalmente (não faz chamadas de rede no __init__).
    """
    prompt_file = tmp_path / "system_prompt.md"
    prompt_file.write_text("You are a test assistant.", encoding="utf-8")
    return LLMClient(
        model="test-model",
        host="http://localhost:11434",
        system_prompt_path=prompt_file,
        base_delay=0.0,  # Zeramos o delay para os testes rodarem rápido
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestAnaliseLLMSchema:
    """Validação do schema Pydantic independente do cliente."""

    def test_valid_data_is_accepted(self):
        analysis = AnaliseLLM.model_validate(VALID_ANALYSIS)
        assert analysis.resumo_curto == VALID_ANALYSIS["resumo_curto"]
        assert analysis.tags == VALID_ANALYSIS["tags"]
        assert analysis.categoria_destino == "Engenharia_de_Dados"
        assert analysis.entidades_encontradas == ["Apache Kafka", "Python"]

    def test_missing_required_field_raises(self):
        from pydantic import ValidationError
        incomplete = {k: v for k, v in VALID_ANALYSIS.items() if k != "resumo_curto"}
        with pytest.raises(ValidationError):
            AnaliseLLM.model_validate(incomplete)


class TestLLMClientSuccess:
    """Cenários de sucesso do LLMClient."""

    def test_returns_valid_analysis_on_first_attempt(self, tmp_path):
        client = _make_client(tmp_path)
        raw_json = json.dumps(VALID_ANALYSIS)

        with patch.object(client._chain, "invoke", return_value=raw_json):
            result = client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES, note_name="test_note")

        assert isinstance(result, AnaliseLLM)
        assert result.categoria_destino == "Engenharia_de_Dados"
        assert "kafka" in result.tags

    def test_strips_markdown_fences_from_response(self, tmp_path):
        client = _make_client(tmp_path)
        raw_with_fence = f"```json\n{json.dumps(VALID_ANALYSIS)}\n```"

        with patch.object(client._chain, "invoke", return_value=raw_with_fence):
            result = client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES)

        assert result.resumo_curto == VALID_ANALYSIS["resumo_curto"]


class TestLLMClientRetry:
    """Cenários de retry e resiliência."""

    def test_recovers_on_third_attempt(self, tmp_path):
        client = _make_client(tmp_path)
        invalid_json = "{ broken json %%"
        valid_json = json.dumps(VALID_ANALYSIS)

        side_effects = [
            invalid_json,   # Tentativa 1: JSON inválido
            invalid_json,   # Tentativa 2: JSON inválido
            valid_json,     # Tentativa 3: sucesso
        ]

        with patch.object(client._chain, "invoke", side_effect=side_effects):
            result = client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES)

        assert isinstance(result, AnaliseLLM)

    def test_raises_runtime_error_after_all_retries_exhausted(self, tmp_path):
        client = _make_client(tmp_path, max_retries=3)
        invalid_json = "not json at all"

        with patch.object(client._chain, "invoke", return_value=invalid_json):
            with pytest.raises(RuntimeError, match="Todas as 3 tentativas falharam"):
                client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES)

    def test_raises_runtime_error_on_invalid_category(self, tmp_path):
        client = _make_client(tmp_path, max_retries=2)
        bad_json = json.dumps({**VALID_ANALYSIS, "categoria_destino": "Categoria_Inventada"})

        with patch.object(client._chain, "invoke", return_value=bad_json):
            with pytest.raises(RuntimeError):
                client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES)

    def test_retry_called_correct_number_of_times(self, tmp_path):
        client = _make_client(tmp_path, max_retries=3)
        invalid_json = "{ bad }"

        mock_invoke = MagicMock(return_value=invalid_json)
        with patch.object(client._chain, "invoke", mock_invoke):
            with pytest.raises(RuntimeError):
                client.analyze_note(NOTE_TEXT, KNOWN_TERMS, CATEGORIES)

        assert mock_invoke.call_count == 3


class TestLLMClientEdgeCases:
    """Casos de borda."""

    def test_empty_categories_list_skips_category_validation(self, tmp_path):
        """Se não há categorias, não valida categoria_destino — útil no cold start."""
        client = _make_client(tmp_path)
        raw_json = json.dumps({**VALID_ANALYSIS, "categoria_destino": "QualquerCoisa"})

        with patch.object(client._chain, "invoke", return_value=raw_json):
            result = client.analyze_note(NOTE_TEXT, KNOWN_TERMS, categories=[])

        assert result.categoria_destino == "QualquerCoisa"

    def test_empty_known_terms_results_in_empty_entities(self, tmp_path):
        client = _make_client(tmp_path)
        raw_json = json.dumps({**VALID_ANALYSIS, "entidades_encontradas": []})

        with patch.object(client._chain, "invoke", return_value=raw_json):
            result = client.analyze_note(NOTE_TEXT, known_terms=[], categories=CATEGORIES)

        assert result.entidades_encontradas == []

    def test_system_prompt_file_not_found_raises(self, tmp_path):
        missing_path = tmp_path / "nonexistent.md"
        with pytest.raises(FileNotFoundError, match="System prompt não encontrado"):
            LLMClient(system_prompt_path=missing_path)


class TestLoadCategoriesFromVault:
    """Testa o helper load_categories_from_vault."""

    def test_returns_sorted_subdirectory_names(self, tmp_path):
        core = tmp_path / "Wiki Core"
        for name in ["Estudos_LLM", "Engenharia_de_Dados", "Desenvolvimento_Pessoal"]:
            (core / name).mkdir(parents=True)

        result = load_categories_from_vault(tmp_path)

        assert result == sorted(["Estudos_LLM", "Engenharia_de_Dados", "Desenvolvimento_Pessoal"])

    def test_ignores_hidden_directories(self, tmp_path):
        core = tmp_path / "Wiki Core"
        (core / "Engenharia_de_Dados").mkdir(parents=True)
        (core / ".obsidian").mkdir(parents=True)

        result = load_categories_from_vault(tmp_path)

        assert ".obsidian" not in result
        assert "Engenharia_de_Dados" in result

    def test_cold_start_returns_empty_list_when_wiki_core_missing(self, tmp_path):
        result = load_categories_from_vault(tmp_path)
        assert result == []
