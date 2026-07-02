import pytest
import os
from src.pulse_ia.services.pdf import run_export_sync

def test_generate_real_pdf():
    report_data = {
        "id": 123,
        "version": "1.0",
        "content": {
            "executive_summary": "Test Summary",
            "results": {
                "maturity_avg": 0.45,
                "sentiment_avg": 0.88,
                "activation_avg": 0.32
            },
            "recommendations": [
                {"title": "Rec 1", "target": "RH", "content": "Contenu 1"}
            ]
        }
    }
    output_path = "test_report.pdf"

    if os.path.exists(output_path):
        os.remove(output_path)

    run_export_sync(report_data, output_path)

    assert os.path.exists(output_path)
    # Check PDF signature
    with open(output_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"

    # Clean up
    os.remove(output_path)
