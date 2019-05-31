from pyquil import Program
from pyquil.gates import MEASURE, I, CNOT, CCNOT, X, H, Z, CZ, PHASE, SWAP
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.api import QVMConnection,WavefunctionSimulator
from main import *
import random
import matplotlib.pyplot as plt

wf_sim = WavefunctionSimulator()

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

def get_encoded_pq(pq_tuples):
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
    pq=measure(pq,code_register)
    return pq,code_register

def get_unencoded_pq(pq_tuples,measure_pq=True):
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

def test(t,trials=10000,noisy=False):
    pq_tuples=rand_pq(t)
    gt_pq,gt_code_register=get_unencoded_pq(pq_tuples,measure_pq=False)
    encoded_pq,encoded_code_register=get_encoded_pq(pq_tuples)
    unencoded_pq,unencoded_code_register=get_unencoded_pq(pq_tuples)

    if noisy:
        noise_file='noise_model.quil'
        model_info=get_model(noise_file)
        encoded_pq=Program(model_info)+encoded_pq
        unencoded_pq=Program(model_info)+unencoded_pq

    gt_pq+=[I(gt_code_register[0]),I(gt_code_register[1])] # stupid simulator
    gt_pq=address_qubits(gt_pq,qubit_mapping={gt_code_register[i]:i for i in range(len(gt_code_register))})
    wf=wf_sim.wavefunction(gt_pq)
    p=np.absolute(wf.amplitudes)**2

    unencoded_pq=address_qubits(unencoded_pq,qubit_mapping={unencoded_code_register[i]:i for i in range(len(unencoded_code_register))})
    measures=qvm.run(unencoded_pq,trials=trials)
    q=get_distr(np.array(measures))

    encoded_pq=address_qubits(encoded_pq,qubit_mapping={encoded_code_register[i]:i for i in range(len(encoded_code_register))})
    measures=qvm.run(encoded_pq,trials=trials)
    r=get_distr(np.array(retreive_logit_qubits(measures)))

    print('p',p)
    print('q',q)
    print('r',r)
    dpq=distr_dis(p,q)
    dpr=distr_dis(p,r)
    print('dpq',dpq,'dpr',dpr)
    return dpq,dpr

def plot(Ts,dpr,dpq):
    fig=plt.gcf()
    ax=plt.gca()
    T=len(dpr)
    ax.plot(Ts,dpr,label='r')
    ax.plot(Ts,dpq,label='q')
    ax.legend()
    ax.set_title('average error rate')
    fig.savefig('error_rate.png')

if __name__=='__main__':
    T=10
    r=10
    Ts=range(1,T)
    dpr_arr=np.zeros(len(Ts))
    dpq_arr=np.zeros(len(Ts))
    for t in Ts:
        sum_dpr,sum_dpq=0,0
        for ir in range(r):
            dpq,dpr=test(t=5,noisy=True)
            sum_dpq+=dpq
            sum_dpr+=dpr
            if dpr>dpq:
                print('dpr>dpq,not fault tolerant,t={}'.format(t))
        dpr_arr[t]=sum_dpr/r
        dpq_arr[t]=sum_dpq/r
    np.savetxt('Ts.txt',np.array(Ts))
    np.savetxt('dpq.txt',dpq_arr)
    np.savetxt('dpr.txt',dpr_arr)

    # dpq_arr=np.loadtxt('dpq.txt')
    # dpr_arr=np.loadtxt('dpr.txt')
    # Ts=range(1,T)
    # plot(Ts,dpr_arr,dpq_arr)