"""Tests for Task 2.15: the locked E01-E16 experiment configuration system."""

import tempfile
import unittest
from pathlib import Path

from rag_service.config import (
    available_configs,
    expected_experiment_matrix,
    load_config,
    validate_configs,
)


class TestExperimentMatrix(unittest.TestCase):
    def test_matrix_contains_sixteen_unique_runs(self):
        matrix = expected_experiment_matrix()

        self.assertEqual(len(matrix), 16)
        self.assertEqual(list(matrix), [f"E{number:02d}" for number in range(1, 17)])
        self.assertEqual(matrix["E01"], ("fixed", "dense"))
        self.assertEqual(matrix["E04"], ("fixed", "hybrid_rerank"))
        self.assertEqual(matrix["E05"], ("recursive", "dense"))
        self.assertEqual(matrix["E08"], ("recursive", "hybrid_rerank"))
        self.assertEqual(matrix["E09"], ("semantic", "dense"))
        self.assertEqual(matrix["E12"], ("semantic", "hybrid_rerank"))
        self.assertEqual(matrix["E13"], ("structure_aware", "dense"))
        self.assertEqual(matrix["E16"], ("structure_aware", "hybrid_rerank"))


class TestConfigFiles(unittest.TestCase):
    def test_all_sixteen_files_exist_and_are_valid(self):
        self.assertEqual(available_configs(), [f"E{number:02d}" for number in range(1, 17)])
        self.assertEqual(validate_configs(), [])

    def test_every_file_matches_the_matrix(self):
        for code, (chunking, retrieval) in expected_experiment_matrix().items():
            with self.subTest(code=code):
                config = load_config(code)
                self.assertEqual(config.code, code)
                self.assertEqual(config.chunking_strategy, chunking)
                self.assertEqual(config.retrieval_method, retrieval)
                self.assertEqual(config.token_limit, 512)
                self.assertEqual(config.token_overlap, 50)
                self.assertEqual(config.rrf_k, 60)
                self.assertEqual(config.final_top_n, 5)
                self.assertEqual(config.dense_collection, f"chroma_{chunking}")
                self.assertEqual(config.bm25_index, f"bm25_{chunking}")
                self.assertEqual(
                    config.reranker_enabled,
                    retrieval == "hybrid_rerank",
                )

    def test_e16_matches_the_prd_appendix_b(self):
        config = load_config("E16")
        raw = config.raw

        self.assertEqual(raw["chunking"]["strategy"], "structure_aware")
        self.assertTrue(raw["chunking"]["semantic_fallback_recursive"])
        self.assertTrue(raw["chunking"]["rules"]["pdf_table_isolation"])
        self.assertTrue(raw["chunking"]["rules"]["docx_heading_hierarchy"])
        self.assertTrue(raw["chunking"]["rules"]["web_qa_preservation"])

        self.assertEqual(raw["embedding"]["dimension"], 768)
        self.assertEqual(raw["embedding"]["prefix_document"], "passage: ")
        self.assertEqual(raw["embedding"]["prefix_query"], "query: ")

        self.assertEqual(raw["retrieval"]["method"], "hybrid_rerank")
        self.assertEqual(raw["retrieval"]["initial_candidates"], 20)
        self.assertEqual(raw["retrieval"]["rrf_k"], 60)
        self.assertEqual(raw["retrieval"]["final_top_n"], 5)
        self.assertTrue(raw["retrieval"]["bm25_stemming"])
        self.assertEqual(raw["retrieval"]["bm25_language"], "indonesian")

        self.assertTrue(raw["reranker"]["enabled"])
        self.assertEqual(raw["reranker"]["model_name"], "BAAI/bge-reranker-v2-m3")
        self.assertEqual(raw["reranker"]["top_n"], 5)

        self.assertEqual(raw["generation"]["temperature"], 0.0)
        self.assertEqual(raw["generation"]["max_output_tokens"], 600)
        self.assertTrue(raw["generation"]["disable_thinking"])
        self.assertEqual(raw["evaluation"]["framework"], "ragas==0.1.21")
        self.assertEqual(
            raw["evaluation"]["kappa_annotation_unit"], "atomic_claim"
        )
        self.assertEqual(raw["evaluation"]["statistical_package"], "R-ARTool")
        self.assertEqual(
            raw["evaluation"]["output_results_path"],
            "data/results/E16_results.json",
        )


class TestConfigValidationErrors(unittest.TestCase):
    def test_missing_and_mismatched_configs_are_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "E01.yaml"
            path.write_text(
                "experiment:\n"
                "  code: E16\n"
                "chunking:\n"
                "  strategy: fixed\n"
                "retrieval:\n"
                "  method: dense\n",
                encoding="utf-8",
            )

            errors = validate_configs(temp_dir)

        joined = "\n".join(errors)
        self.assertIn("missing configuration files", joined)
        self.assertIn("E01", joined)
        self.assertIn("experiment.code", joined)

    def test_malformed_yaml_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for number in range(1, 17):
                code = f"E{number:02d}"
                (Path(temp_dir) / f"{code}.yaml").write_text(
                    "experiment:\n"
                    f"  code: {code}\n"
                    "chunking:\n"
                    "  strategy: fixed\n"
                    "retrieval:\n"
                    "  method: telepathy\n",
                    encoding="utf-8",
                )

            errors = validate_configs(temp_dir)

        self.assertTrue(errors)
        self.assertTrue(any("unknown retrieval method" in error for error in errors))

    def test_missing_directory_is_reported(self):
        errors = validate_configs("/tmp/definitely-not-a-config-directory-xyz")

        self.assertEqual(len(errors), 1)
        self.assertIn("configuration directory not found", errors[0])


if __name__ == "__main__":
    unittest.main()
