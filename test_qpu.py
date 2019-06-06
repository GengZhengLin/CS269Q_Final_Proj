from pyquil import Program, get_qc
from pyquil.gates import MEASURE, I, CNOT, CCNOT, X, H, Z, CZ, PHASE, SWAP
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.api import QVMConnection,WavefunctionSimulator
from typing import List
import numpy as np
import random
import string

# from main import *
import random
import matplotlib.pyplot as plt

wf_sim = WavefunctionSimulator()
verbose=True


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


def get_model(filename):
    with open(filename, 'r') as file:
        model_info = file.read()
        return model_info

def rand_pq(t):
    pq=[]
    for i in range(t):
        t=random.randint(0,3)
        b=random.randint(0,1)
        if t==0:
            pq.append(('X',b))
        elif t==1:
            pq.append(('Z',b))
        elif t==2:
            pq.append(('H',))
        elif t==3:
            pq.append(('CZ',))
    return pq

def get_encoded_pq(pq_tuples,noise=None):
    pq,code_register=encode()
    for t in pq_tuples:
        if t[0]=='X':
            pq=add_logic_gate(pq,code_register,t[0],t[1])
        elif t[0]=='Z':
            pq=add_logic_gate(pq,code_register,t[0],t[1])
        elif t[0]=='H':
            pq=add_logic_gate(pq,code_register,t[0],0)
        elif t[0]=='CZ':
            pq=add_logic_gate(pq,code_register,t[0],0)
        if noise is not None:
            pq+=noise(code_register)
    pq=measure(pq,code_register)
    return pq,code_register

def get_unencoded_pq(pq_tuples,measure_pq=True,noise=None):
    pq = Program()
    code_register =  QubitPlaceholder.register(2)
    for t in pq_tuples:
        if t[0]=='X':
            pq+=X(code_register[t[1]])
        elif t[0]=='Z':
            pq+=Z(code_register[t[1]])
        elif t[0]=='H':
            pq+=[H(code_register[0]),H(code_register[1]),SWAP(code_register[0],code_register[1])]
        elif t[0]=='CZ':
            pq+=[CZ(code_register[0],code_register[1]),Z(code_register[0]),Z(code_register[1])]
        if noise is not None:
            pq+=noise(code_register)
    if measure_pq:
        pq=measure(pq,code_register)
    return pq,code_register

def distr_dis(p,q):
    return np.sum(np.abs(p-q))/2

def get_distr(measures):
    m=measures[:,0]+measures[:,1]*2
    p=np.zeros(4)
    for i in m:
        p[i]+=1
    return p/len(m)

def test(t,trials=200,noisy=False, device='9q-generic-qvm'):
    pq_tuples=rand_pq(t)
    noise=None

    gt_pq,gt_code_register=get_unencoded_pq(pq_tuples,measure_pq=False,noise=None)
    gt_pq+=[I(gt_code_register[0]),I(gt_code_register[1])] # stupid simulator

    gt_pq=address_qubits(gt_pq,qubit_mapping={gt_code_register[i]:j for i, j in enumerate([0, 1])})
    wf=wf_sim.wavefunction(gt_pq)
    p=np.absolute(wf.amplitudes)**2

   
    encoded_pq,encoded_code_register=get_encoded_pq(pq_tuples,noise=noise)
    encoded_pq=address_qubits(encoded_pq,qubit_mapping={encoded_code_register[i]:j for i, j in enumerate([0, 1, 2, 7, 15])})
    unencoded_pq,unencoded_code_register=get_unencoded_pq(pq_tuples,noise=noise)
    unencoded_pq=address_qubits(unencoded_pq,qubit_mapping={unencoded_code_register[i]:j for i, j in enumerate([0, 1])})

    qc = get_qc(device)

    unencoded_pq = qc.compile(unencoded_pq)
    measures = []
    for i in range(trials):
        measures.append(qc.run(unencoded_pq)[0])
    q=get_distr(np.array(measures))

    encoded_pq = qc.compile(encoded_pq)
    measures = []
    for i in range(trials):
        measures.append(qc.run(encoded_pq)[0])
        
    measures=retreive_logit_qubits(measures)
    if verbose:
        print('measures:',len(measures) / float(trials))
    r=get_distr(np.array(measures))

    dpq=distr_dis(p,q)
    dpr=distr_dis(p,r)
    
    if verbose:
        print('t',t)
        print(wf.amplitudes)
        print('p',p)
        print('q',q)
        print('r',r)
        print('dpq',dpq,'dpr',dpr)
    if dpr>dpq:
        print('not fault-tolerant,t={}'.format(t))
    print(pq_tuples)
    return dpq,dpr, len(measures) / float(trials)
    
if __name__ == '__main__':
    T=30
    r=10
    Ts=range(1,T)
    dpr_arr=np.zeros(len(Ts))
    dpq_arr=np.zeros(len(Ts))
    ratios = []
    for i in range(len(Ts)):
        t=Ts[i]
        sum_dpr,sum_dpq=0,0
        for ir in range(r):
            dpq,dpr,ratio=test(t=t,noisy=False,device='Aspen-4-5Q-A')
            sum_dpq+=dpq
            sum_dpr+=dpr
        dpr_arr[i]=sum_dpr/r
        dpq_arr[i]=sum_dpq/r
        ratios.append(ratio)

        np.savetxt('Ts.txt',np.array(Ts))
        np.savetxt('dpq.txt',dpq_arr)
        np.savetxt('dpr.txt',dpr_arr)
        np.savetxt('ratios.txt', np.array(ratios))

    
#     t = 3
#     # dpq,dpr=test(t=t,noisy=False,device='9q-generic-qvm')
#     dpq,dpr=test(t=t,noisy=False,device='Aspen-4-5Q-A')
