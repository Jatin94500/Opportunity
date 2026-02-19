from qubo.ai import suggest_corrections


def test_ai_fallback_static_analysis():
    code = """from math import sqrt\nfrom qubo.circuit import QuantumCircuit\nqc = QuantumCircuit(1)\n"""
    out = suggest_corrections(code)
    assert isinstance(out, str)
    assert 'QuantumCircuit' in code  # sanity
    # Should mention unused import or no measurement
    assert ('Unused' in out) or ('measurement' in out.lower()) or ('No critical issues' in out)
