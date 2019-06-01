from typing import List
import numpy as np
import random
import string

from pyquil import Program
from pyquil.gates import MEASURE, I, CNOT, CCNOT, X, H, Z, CZ, PHASE
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.api import QVMConnection

qvm = QVMConnection(random_seed=1337)

def encode():
    pq = Program()
    code_register =  QubitPlaceholder.register(5)
    q0, q1, q2, q3, a = code_register
    pq += H(q1)
    pq += CNOT(q1, q2)
    pq += CNOT(q1, q0)
    pq += CNOT(q2, q3)
    pq += CNOT(q3, a)
    pq += CNOT(q2, a)
    return pq, code_register


def add_logic_gate(pq, code_register, gate, bit):
    q0, q1, q2, q3, a = code_register
    assert bit == 0 or bit == 1
    if gate == 'X':
        # X gate on one of the qubits
        if bit == 0:
            pq += X(q0)
            pq += X(q2)
        else:
            pq += X(q0)
            pq += X(q1)
    elif gate == 'Z':
        # Z gate on one of the qubits
        if bit == 0:
            pq += Z(q0)
            pq += Z(q1)
        elif bit == 1:
            pq += Z(q0)
            pq += Z(q2)
    elif gate == 'H':
        # Hadmard gate on both qubits but switch them
        pq += [H(qq) for qq in code_register[:-1]]
    elif gate == 'CZ':
        # Controlled Z on the two qubits, and then apply Z gates to each of them
        pq += [PHASE(np.pi / 2, qq) for qq in code_register[:-1]]
    else:
        raise ValueError('Gate value invalid!')
    return pq
    

def measure(pq, code_register):
    ro = pq.declare('ro', 'BIT', 5)
    pq += [MEASURE(qq, rr) for qq, rr in zip(code_register, ro)]
    return pq


def run(pq, trials=10):
    return qvm.run(address_qubits(pq), trials=trials)

def retreive_logit_qubits(results):
    logics = []
    for r in results:
        if r[-1] == 1:
            pass
            # print('Ancilla wrong, discarded!')
            # logics.append([-1, -1])
        elif sum(r) % 1 == 1:
            pass
            # print('Gate error, discarded!')
            # logics.append([-1, -1])
        elif r[0] == r[1] == r[2] == r[3]:
            logics.append([0, 0])
        elif r[0] == r[1] == 1-r[2] == 1-r[3]:
            logics.append([0, 1])
        elif r[0] == 1-r[1] == r[2] == 1-r[3]:
            logics.append([1, 0])
        elif r[0] == 1-r[1] == 1-r[2] == r[3]:
            logics.append([1, 1])
        else:
            pass
            # print(r)
    return logics
 

if __name__ == '__main__':
    # Example: test the circuit which applies H gates to two logical qubits and then invert them, and then perform this again.
    # Under a noiseless QVM, this should give [0, 0] deterministically.
    pq, code_register = encode()
    pq = add_logic_gate(pq, code_register, 'H', 0)
    pq = add_logic_gate(pq, code_register, 'H', 0)
    pq = measure(pq, code_register)
    
    # Example: test the circuit which applies X gates to the first logical qubits.
    # Under a noiseless QVM, this should give [1, 0] deterministically.
    pq, code_register = encode()
    pq = add_logic_gate(pq, code_register, 'X', 0)
    pq = measure(pq, code_register)
    results = run(pq, trials=10)
    print(retreive_logit_qubits(results))
    
    # Example: test the circuit which applies Z gates to both logical qubits.
    # Under a noiseless QVM, this should give [0, 0] deterministically.
    pq, code_register = encode()
    pq = add_logic_gate(pq, code_register, 'Z', 0)
    pq = add_logic_gate(pq, code_register, 'Z', 1)
    pq = measure(pq, code_register)
    results = run(pq, trials=10)
    print(retreive_logit_qubits(results))
    
    # Example: test the circuit which entangles both qubits, 
    # then apply Z gates qubit 0 (which is input 1 because inverted), and then revert back.
    # Under a noiseless QVM, this should give [1, 0] deterministically.
    pq, code_register = encode()
    pq = add_logic_gate(pq, code_register, 'H')
    pq = add_logic_gate(pq, code_register, 'Z', 1)
    pq = add_logic_gate(pq, code_register, 'H')
    pq = measure(pq, code_register)
    results = run(pq, trials=10)
    print(retreive_logit_qubits(results))