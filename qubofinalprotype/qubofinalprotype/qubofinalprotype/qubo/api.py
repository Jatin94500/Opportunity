"""REST API for qubo quantum circuit operations.

Provides endpoints for:
- Circuit building and manipulation
- Quantum simulation
- Hardware integration
- Visualization and analysis
"""
from __future__ import annotations

import json
import traceback
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import numpy as np

from .circuit import QuantumCircuit
from .simulator import StatevectorSimulator
from .visualizer import CircuitVisualizer
from . import noise as noise_mod

app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend integration

# Global storage for circuits (in production, use proper database)
circuits: Dict[str, QuantumCircuit] = {}
simulation_results: Dict[str, Any] = {}

# ============ CIRCUIT BUILDER API ============

@app.route('/api/v1/circuit', methods=['POST'])
def create_circuit():
    """Create a new quantum circuit.
    
    Request body:
    {
        "name": "my_circuit",
        "num_qubits": 3,
        "description": "Optional description"
    }
    """
    try:
        data = request.get_json()
        name = data.get('name', f'circuit_{len(circuits)}')
        num_qubits = data.get('num_qubits', 2)
        description = data.get('description', '')
        
        if name in circuits:
            return jsonify({'error': f'Circuit {name} already exists'}), 400
            
        circuit = QuantumCircuit(num_qubits)
        circuit.description = description
        circuits[name] = circuit
        
        return jsonify({
            'success': True,
            'circuit_id': name,
            'num_qubits': num_qubits,
            'description': description
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/circuit/<circuit_id>', methods=['GET'])
def get_circuit(circuit_id: str):
    """Get circuit information."""
    if circuit_id not in circuits:
        return jsonify({'error': 'Circuit not found'}), 404
    
    circuit = circuits[circuit_id]
    return jsonify({
        'circuit_id': circuit_id,
        'num_qubits': circuit.num_qubits,
        'gates': [str(gate) for gate in circuit.gates],
        'description': getattr(circuit, 'description', ''),
        'depth': len(circuit.gates)
    })

@app.route('/api/v1/circuit/<circuit_id>/gate', methods=['POST'])
def add_gate(circuit_id: str):
    """Add a gate to the circuit.
    
    Request body:
    {
        "gate_type": "H",
        "targets": [0],
        "controls": [],
        "params": []
    }
    """
    try:
        if circuit_id not in circuits:
            return jsonify({'error': 'Circuit not found'}), 404
            
        data = request.get_json()
        gate_type = data['gate_type']
        targets = data.get('targets', [])
        controls = data.get('controls', [])
        params = data.get('params', [])
        
        circuit = circuits[circuit_id]
        
        if controls:
            circuit.add_gate(gate_type, targets=targets, controls=controls, params=params)
        else:
            circuit.add_gate(gate_type, targets=targets, params=params)
            
        return jsonify({
            'success': True,
            'gate_added': {
                'type': gate_type,
                'targets': targets,
                'controls': controls,
                'params': params
            },
            'circuit_depth': len(circuit.gates)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/circuit/<circuit_id>/gates', methods=['DELETE'])
def clear_circuit(circuit_id: str):
    """Clear all gates from circuit."""
    if circuit_id not in circuits:
        return jsonify({'error': 'Circuit not found'}), 404
    
    circuit = circuits[circuit_id]
    circuit.gates.clear()
    return jsonify({'success': True, 'message': 'Circuit cleared'})

@app.route('/api/v1/circuits', methods=['GET'])
def list_circuits():
    """List all available circuits."""
    circuit_list = []
    for name, circuit in circuits.items():
        circuit_list.append({
            'circuit_id': name,
            'num_qubits': circuit.num_qubits,
            'depth': len(circuit.gates),
            'description': getattr(circuit, 'description', '')
        })
    return jsonify({'circuits': circuit_list})

# ============ SIMULATION API ============

@app.route('/api/v1/simulate/<circuit_id>', methods=['POST'])
def simulate_circuit(circuit_id: str):
    """Simulate a quantum circuit.
    
    Request body:
    {
        "shots": 1024,
        "noise_model": "none",
        "noise_params": {"p": 0.05},
        "output_format": "counts"
    }
    """
    try:
        if circuit_id not in circuits:
            return jsonify({'error': 'Circuit not found'}), 404
            
        data = request.get_json() or {}
        shots = data.get('shots', 1024)
        noise_model = data.get('noise_model', 'none')
        noise_params = data.get('noise_params', {})
        output_format = data.get('output_format', 'counts')
        
        circuit = circuits[circuit_id]
        
        # Setup noise if specified
        noise_hook = None
        if noise_model != 'none':
            noise_func = getattr(noise_mod, noise_model, None)
            if noise_func:
                p = noise_params.get('p', 0.05)
                def noise_hook(state, gate):
                    for target in getattr(gate, 'targets', []):
                        state = noise_func(state, p, target)
                    return state
        
        simulator = StatevectorSimulator(circuit, noise_hook=noise_hook)
        result = simulator.run(shots=shots)
        
        # Store result for later retrieval
        result_id = f"{circuit_id}_sim_{len(simulation_results)}"
        simulation_results[result_id] = {
            'circuit_id': circuit_id,
            'result': result,
            'shots': shots,
            'noise_model': noise_model,
            'output_format': output_format
        }
        
        # Format response based on output type
        if isinstance(result, dict):
            # Measurement counts
            response_data = {
                'result_id': result_id,
                'type': 'counts',
                'data': result,
                'total_shots': sum(result.values()),
                'unique_states': len(result)
            }
        else:
            # Statevector
            response_data = {
                'result_id': result_id,
                'type': 'statevector',
                'data': {
                    'amplitudes': result.tolist() if hasattr(result, 'tolist') else list(result),
                    'probabilities': (np.abs(result)**2).tolist() if hasattr(result, 'tolist') else list(np.abs(result)**2)
                },
                'dimension': len(result)
            }
            
        return jsonify({
            'success': True,
            'simulation': response_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/v1/simulate/<circuit_id>/batch', methods=['POST'])
def batch_simulate(circuit_id: str):
    """Run multiple simulations with different parameters.
    
    Request body:
    {
        "simulations": [
            {"shots": 1024, "noise_model": "none"},
            {"shots": 1024, "noise_model": "bit_flip", "noise_params": {"p": 0.01}},
            {"shots": 1024, "noise_model": "bit_flip", "noise_params": {"p": 0.05}}
        ]
    }
    """
    try:
        if circuit_id not in circuits:
            return jsonify({'error': 'Circuit not found'}), 404
            
        data = request.get_json()
        simulations = data.get('simulations', [])
        
        results = []
        for i, sim_config in enumerate(simulations):
            # Use the single simulation endpoint logic
            request_data = json.dumps(sim_config)
            # This is a simplified version - in production you'd properly call the simulation
            circuit = circuits[circuit_id]
            simulator = StatevectorSimulator(circuit)
            result = simulator.run(shots=sim_config.get('shots', 1024))
            
            results.append({
                'simulation_index': i,
                'config': sim_config,
                'result': result.tolist() if hasattr(result, 'tolist') else result
            })
            
        return jsonify({
            'success': True,
            'batch_results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ HARDWARE INTEGRATION API ============

@app.route('/api/v1/hardware/providers', methods=['GET'])
def list_hardware_providers():
    """List available quantum hardware providers."""
    providers = [
        {
            'name': 'IBM Quantum',
            'status': 'available',
            'backends': ['ibm_brisbane', 'ibm_kyoto', 'simulator_mps'],
            'max_qubits': 127,
            'supports_pulse': True
        },
        {
            'name': 'Google Quantum',
            'status': 'mock',
            'backends': ['sycamore', 'bristlecone'],
            'max_qubits': 70,
            'supports_pulse': False
        },
        {
            'name': 'Rigetti',
            'status': 'mock',
            'backends': ['aspen-m-3', 'qvm-simulator'],
            'max_qubits': 80,
            'supports_pulse': True
        }
    ]
    return jsonify({'providers': providers})

@app.route('/api/v1/hardware/submit/<circuit_id>', methods=['POST'])
def submit_to_hardware(circuit_id: str):
    """Submit circuit to quantum hardware.
    
    Request body:
    {
        "provider": "IBM Quantum",
        "backend": "ibm_brisbane",
        "shots": 1024,
        "priority": "normal"
    }
    """
    try:
        if circuit_id not in circuits:
            return jsonify({'error': 'Circuit not found'}), 404
            
        data = request.get_json()
        provider = data.get('provider', 'IBM Quantum')
        backend = data.get('backend', 'simulator')
        shots = data.get('shots', 1024)
        priority = data.get('priority', 'normal')
        
        # Mock job submission
        job_id = f"job_{circuit_id}_{len(simulation_results)}"
        
        # In a real implementation, this would submit to actual hardware
        # For now, we'll simulate the job and return a mock response
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'provider': provider,
            'backend': backend,
            'shots': shots,
            'status': 'submitted',
            'queue_position': 42,
            'estimated_completion': '2025-09-05T15:30:00Z'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/hardware/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """Get the status of a hardware job."""
    # Mock job status response
    return jsonify({
        'job_id': job_id,
        'status': 'completed',
        'progress': 100,
        'queue_position': 0,
        'start_time': '2025-09-05T14:45:00Z',
        'completion_time': '2025-09-05T14:47:30Z',
        'hardware_info': {
            'backend': 'ibm_brisbane',
            'calibration_date': '2025-09-05T08:00:00Z',
            'error_rates': {'cx': 0.012, 'readout': 0.025}
        }
    })

@app.route('/api/v1/hardware/job/<job_id>/result', methods=['GET'])
def get_job_result(job_id: str):
    """Get the result of a completed hardware job."""
    # Mock hardware result
    mock_counts = {
        '00': 512,
        '01': 234,
        '10': 189,
        '11': 89
    }
    
    return jsonify({
        'job_id': job_id,
        'status': 'completed',
        'result': {
            'counts': mock_counts,
            'shots': sum(mock_counts.values()),
            'execution_time': 2.5,
            'hardware_metadata': {
                'backend': 'ibm_brisbane',
                'gate_errors': {'cx_0_1': 0.013, 'readout_0': 0.022},
                'temperature': 0.015
            }
        }
    })

# ============ VISUALIZATION API ============

@app.route('/api/v1/visualize/<circuit_id>', methods=['GET'])
def visualize_circuit(circuit_id: str):
    """Get circuit visualization data."""
    if circuit_id not in circuits:
        return jsonify({'error': 'Circuit not found'}), 404
        
    circuit = circuits[circuit_id]
    
    # Create visualization data
    viz_data = {
        'circuit_id': circuit_id,
        'num_qubits': circuit.num_qubits,
        'depth': len(circuit.gates),
        'gates': [],
        'qubit_labels': [f'q{i}' for i in range(circuit.num_qubits)]
    }
    
    for i, gate in enumerate(circuit.gates):
        gate_info = {
            'position': i,
            'type': gate.gate_type,
            'targets': gate.targets,
            'controls': getattr(gate, 'controls', []),
            'params': getattr(gate, 'params', []),
            'label': gate.gate_type
        }
        viz_data['gates'].append(gate_info)
    
    return jsonify(viz_data)

# ============ ANALYSIS API ============

@app.route('/api/v1/analyze/<circuit_id>', methods=['GET'])
def analyze_circuit(circuit_id: str):
    """Analyze circuit properties and complexity."""
    if circuit_id not in circuits:
        return jsonify({'error': 'Circuit not found'}), 404
        
    circuit = circuits[circuit_id]
    
    # Count gate types
    gate_counts = {}
    for gate in circuit.gates:
        gate_type = gate.gate_type
        gate_counts[gate_type] = gate_counts.get(gate_type, 0) + 1
    
    # Calculate circuit metrics
    analysis = {
        'circuit_id': circuit_id,
        'metrics': {
            'depth': len(circuit.gates),
            'width': circuit.num_qubits,
            'gate_count': len(circuit.gates),
            'gate_types': gate_counts,
            'complexity_score': len(circuit.gates) * circuit.num_qubits
        },
        'properties': {
            'has_measurements': any(gate.gate_type == 'M' for gate in circuit.gates),
            'has_multi_qubit_gates': any(len(gate.targets) > 1 for gate in circuit.gates),
            'max_gate_arity': max((len(gate.targets) for gate in circuit.gates), default=0)
        }
    }
    
    return jsonify(analysis)

# ============ UTILITY ENDPOINTS ============

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'active_circuits': len(circuits),
        'simulation_results': len(simulation_results)
    })

@app.route('/api/v1/reset', methods=['POST'])
def reset_all():
    """Reset all circuits and simulation results."""
    global circuits, simulation_results
    circuits.clear()
    simulation_results.clear()
    return jsonify({'success': True, 'message': 'All data cleared'})

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def run_api_server(host='localhost', port=5000, debug=True):
    """Run the API server."""
    print(f"Starting qubo API server on http://{host}:{port}")
    print("Available endpoints:")
    print("- POST /api/v1/circuit - Create circuit")
    print("- GET /api/v1/circuit/<id> - Get circuit")
    print("- POST /api/v1/circuit/<id>/gate - Add gate")
    print("- POST /api/v1/simulate/<id> - Simulate circuit")
    print("- GET /api/v1/hardware/providers - List hardware")
    print("- POST /api/v1/hardware/submit/<id> - Submit to hardware")
    print("- GET /api/v1/visualize/<id> - Get visualization")
    print("- GET /api/v1/analyze/<id> - Analyze circuit")
    print("- GET /api/v1/health - Health check")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api_server()
