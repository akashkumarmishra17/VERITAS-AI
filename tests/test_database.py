"""
Unit tests for SQLite Forensic Database Manager.
"""

import os
import tempfile
from src.database.db_manager import ForensicDatabaseManager


def test_database_crud_operations():
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = tf.name
    tf.close()

    try:
        db = ForensicDatabaseManager(db_path=temp_db_path)
        
        # 1. Initial stats should be zero
        stats = db.get_statistics()
        assert stats["total_analyses"] == 0

        # 2. Insert record
        rec_id = db.record_analysis(
            analysis_uuid="TEST-UUID-001",
            filename="sample_test.jpg",
            file_format="JPEG",
            dimensions="512x512",
            file_size_kb=120.5,
            prediction="Authentic",
            confidence_score=0.88,
            manipulated_probability=0.12,
            ela_mean_error=3.2,
            noise_inconsistency_score=0.18,
            copy_move_detected=False,
            num_suspicious_zones=0,
            metadata_risk="LOW",
            model_version="RandomForest-v1.0",
            notes_summary="Normal baseline test record.",
        )
        assert rec_id == 1

        # 3. Retrieve records
        records = db.get_records()
        assert len(records) == 1
        assert records[0]["analysis_uuid"] == "TEST-UUID-001"
        assert records[0]["filename"] == "sample_test.jpg"

        # 4. Search and filter
        rec_by_id = db.get_record_by_id(rec_id)
        assert rec_by_id is not None
        assert rec_by_id["prediction"] == "Authentic"

        filtered = db.get_records(verdict_filter="Potentially Manipulated")
        assert len(filtered) == 0

        searched = db.get_records(search_query="sample_test")
        assert len(searched) == 1

        # 5. Delete record
        deleted = db.delete_record(rec_id)
        assert deleted is True
        assert len(db.get_records()) == 0

    finally:
        del db
        import gc
        gc.collect()
        try:
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)
        except OSError:
            pass
