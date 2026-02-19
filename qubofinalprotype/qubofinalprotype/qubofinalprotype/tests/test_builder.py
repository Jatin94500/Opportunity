from qubo.builder import BuiltGate, generate_circuit_code


def test_generate_circuit_code():
    gates = [BuiltGate('H', [0]), BuiltGate('CNOT', [0,1]), BuiltGate('RZ', [1], params=[1.234])]
    code = generate_circuit_code(2, gates)
    assert 'QuantumCircuit(2)' in code
    assert "qc.add_gate('H', targets=[0])" in code
    assert "qc.add_gate('CNOT', targets=[0, 1])" in code
    assert "params=[1.234]" in code
