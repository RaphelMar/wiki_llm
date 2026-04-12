"""
Teste unitário da Task 4 (MarkdownProcessor).
Avalia a injeção do YAML e a técnica de Regex Bidirecional.
"""
import tempfile
import logging
from pathlib import Path

from src.core.processor import MarkdownProcessor
from src.core.llm_client import AnaliseLLM, EntidadeMapeada

logging.basicConfig(level=logging.INFO, format="%(message)s")

def testar_cirurgia_markdown():
    processor = MarkdownProcessor()
    
    # 1. Nota Bruta (Texto com caps lock e abreviações)
    nota_crua = """Hoje eu estudei bastante.
A eng. de dados é incrível. O POLARS e o Rust são ótimos.
Já o meu conhecimento de [[pandas]] está velho.
Cuidado com a palavra crustáceo, não tem a ver com rust."""

    # 2. Resposta perfeita do LLM mockada
    analise_mock = AnaliseLLM(
        resumo_curto="Reflexão sobre performance de frameworks de dados.",
        tags=["estudos", "performance"],
        aliases=[],
        categoria_destino="C1_Estudos",
        entidades_encontradas=[
            EntidadeMapeada(termo_no_texto="eng. de dados", termo_canonico="engenharia de dados"),
            EntidadeMapeada(termo_no_texto="POLARS", termo_canonico="polars"),
            EntidadeMapeada(termo_no_texto="Rust", termo_canonico="rust"),
        ]
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        fake_file = Path(temp_dir) / "nota_teste.md"
        fake_file.write_text(nota_crua, encoding="utf-8")
        
        # 3. Executa a cirurgia!
        processor.process_file(fake_file, analise_mock)
        
        resultado = fake_file.read_text(encoding="utf-8")
        
        logging.info("\n--- NOTA PROCESSADA (PÓS-CIRURGIA) ---")
        logging.info(resultado)
        logging.info("--------------------------------------")

if __name__ == "__main__":
    testar_cirurgia_markdown()