
import click
import importlib.util
import sys
import json


@click.command()
@click.argument('circuit_file')
@click.option('--shots', '-s', default=1024, help='Number of measurement shots (if measuring).', type=int)
@click.option('--seed', default=None, help='RNG seed for deterministic sampling.', type=int)
@click.option('--json', 'as_json', is_flag=True, default=False, help='Output results as JSON')
def main(circuit_file, shots: int, seed: int, as_json: bool):
	"""Run a quantum circuit from a Python file and print results.

	Example:
		qubo-cli my_circuit.py --shots 1000 --json
	"""
	spec = importlib.util.spec_from_file_location("user_circuit", circuit_file)
	user_mod = importlib.util.module_from_spec(spec)
	sys.modules["user_circuit"] = user_mod
	spec.loader.exec_module(user_mod)
	if hasattr(user_mod, 'qc'):
		from qubo.simulator import StatevectorSimulator
		sim = StatevectorSimulator(user_mod.qc, seed=seed)
		result = sim.run(shots=shots)

		# If simulator returned counts (dict), optionally output JSON
		if isinstance(result, dict):
			if as_json:
				print(json.dumps({"counts": result}))
			else:
				print(result)
		else:
			# statevector returned; convert to probabilities for JSON-friendly output
			import numpy as _np
			probs = (_np.abs(result) ** 2).real
			labels = [format(i, f'0{user_mod.qc.num_qubits}b') for i in range(len(probs))]
			out = {labels[i]: float(probs[i]) for i in range(len(probs))}
			if as_json:
				print(json.dumps({"probabilities": out}))
			else:
				print('Statevector probabilities:')
				for k, v in out.items():
					print(k, v)
	else:
		print("Please define a 'qc' QuantumCircuit in your file.")


if __name__ == '__main__':
	main()
