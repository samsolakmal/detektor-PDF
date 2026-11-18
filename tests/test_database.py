import unittest

from sqlalchemy import create_engine

from database import (
    Base,
    get_database_overview,
    list_database_records,
    list_recent_analyses,
    save_analysis,
)


class AnalysisDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_analysis_is_saved_and_listed_without_document_content(self):
        findings = {
            "total_score": 65,
            "word_count": 420,
            "special_score": 5,
            "special_counts": {"Em dash": 1},
            "phrase_score": 10,
            "phrase_counts": {"selain itu": 2},
            "sentence_count": 12,
            "sentence_stdev": 4.1,
            "burstiness_score": 30,
            "list_score": 0,
            "list_matches": ["1. Judul Pribadi: Nama Mahasiswa Contoh"],
        }

        record_id = save_analysis("docx", None, findings, engine=self.engine)
        total, average, history = list_recent_analyses(engine=self.engine)

        self.assertEqual(total, 1)
        self.assertEqual(average, 65.0)
        self.assertEqual(history[0]["ID"], record_id[:8])
        self.assertEqual(history[0]["Format"], "DOCX")
        self.assertEqual(history[0]["Kata"], 420)
        self.assertEqual(history[0]["Temuan"]["list_match_count"], 1)
        self.assertNotIn("list_matches", history[0]["Temuan"])
        self.assertNotIn("filename", history[0])
        self.assertNotIn("document_text", history[0])
        self.assertNotIn("Nama Mahasiswa Contoh", str(history[0]["Temuan"]))

        record_count, records = list_database_records(engine=self.engine)
        self.assertEqual(record_count, 1)
        self.assertEqual(records[0]["ID lengkap"], record_id)
        self.assertEqual(records[0]["Jenis file"], "DOCX")
        self.assertEqual(records[0]["Rincian indikator"]["list_match_count"], 1)

    def test_database_overview_identifies_test_database(self):
        overview = get_database_overview(engine=self.engine)
        self.assertEqual(overview["server"], "sqlite (mode pengujian)")
        self.assertEqual(overview["pgvector"], "Tidak berlaku untuk SQLite")

    def test_empty_history(self):
        total, average, history = list_recent_analyses(engine=self.engine)
        self.assertEqual((total, average, history), (0, None, []))


if __name__ == "__main__":
    unittest.main()
