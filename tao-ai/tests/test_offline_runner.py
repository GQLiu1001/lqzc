import unittest

from app.eval.offline_runner import _compute_retrieval_metrics


class OfflineRunnerMetricsTest(unittest.TestCase):
    def test_duplicate_doc_ids_do_not_inflate_recall_or_ndcg(self) -> None:
        metrics = _compute_retrieval_metrics(["doc-a", "doc-b"], ["doc-a", "doc-a", "doc-b", "doc-b"])

        self.assertTrue(metrics.hit)
        self.assertEqual(metrics.hit_at_k, 1)
        self.assertEqual(metrics.recall, 1.0)
        self.assertEqual(metrics.mrr, 1.0)
        self.assertEqual(metrics.ndcg, 1.0)
        self.assertEqual(metrics.retrieved_doc_ids, ["doc-a", "doc-b"])

    def test_first_unique_occurrence_defines_rank(self) -> None:
        metrics = _compute_retrieval_metrics(["doc-b"], ["doc-x", "doc-b", "doc-b", "doc-y"])

        self.assertTrue(metrics.hit)
        self.assertEqual(metrics.hit_at_k, 2)
        self.assertEqual(metrics.recall, 1.0)
        self.assertEqual(metrics.mrr, 0.5)
        self.assertEqual(metrics.retrieved_doc_ids, ["doc-x", "doc-b", "doc-y"])


if __name__ == "__main__":
    unittest.main()
