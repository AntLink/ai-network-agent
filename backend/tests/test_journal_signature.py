from app.services.journal_signature import verify_summary_signature


def test_python_verifies_cross_runtime_ed25519_vector():
    summary = {
        "attempt_id": "attempt-vector-1",
        "idempotency_key": "idem-vector-1",
        "status": "UNKNOWN",
        "result_available": False,
        "signature": "5FrW5WF3N3VIKNQuIw_0uy7kXSbLhqdpQizh5oBcxA_b3OYbaBpqy5uabf_QXh-YrcZnR_UVx2h7nmsUNSjzDw",
    }
    verify_summary_signature(
        edge_id="edge-vector",
        summary=summary,
        public_keys={"edge-vector": "A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg"},
    )
