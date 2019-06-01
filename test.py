from pyquil import Program
from pyquil.gates import MEASURE, I, CNOT, CCNOT, X, H, Z, CZ, PHASE, SWAP
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.api import QVMConnection,WavefunctionSimulator
from main import *
import random
import matplotlib.pyplot as plt

wf_sim = WavefunctionSimulator()
verbose=False

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

def test(t,trials=10000,noisy=False):
    pq_tuples=rand_pq(t)
    noise=None
    if noisy:
        def noise(code_register):
            return [I(qq) for qq in code_register]

    gt_pq,gt_code_register=get_unencoded_pq(pq_tuples,measure_pq=False,noise=None)
    gt_pq+=[I(gt_code_register[0]),I(gt_code_register[1])] # stupid simulator
    gt_pq=address_qubits(gt_pq,qubit_mapping={gt_code_register[i]:i for i in range(len(gt_code_register))})
    wf=wf_sim.wavefunction(gt_pq)
    p=np.absolute(wf.amplitudes)**2

    encoded_pq,encoded_code_register=get_encoded_pq(pq_tuples,noise=noise)
    encoded_pq=address_qubits(encoded_pq,qubit_mapping={encoded_code_register[i]:i for i in range(len(encoded_code_register))})
    unencoded_pq,unencoded_code_register=get_unencoded_pq(pq_tuples,noise=noise)
    unencoded_pq=address_qubits(unencoded_pq,qubit_mapping={unencoded_code_register[i]:i for i in range(len(unencoded_code_register))})

    if noisy:
        kraus_ops=[np.array([[0.9991083378177872,0.0],[0.0,0.9973258078042986]]),
                   np.array([[0.0422200106937267,0.0],[0.0,-0.042144685092505366]]),
                   np.array([[0.0,0.059654872261407456],[0.0,0.0]]),
                   np.array([[0.0,-0.002520877115599509],[0.0,0.0]])]
        noise_data=Program()
        for qq in range(len(encoded_code_register)):
            noise_data.define_noisy_gate("I",[qq],kraus_ops)
        encoded_pq=noise_data+encoded_pq

        noise_data=Program()
        for qq in range(len(unencoded_code_register)):
            noise_data.define_noisy_gate("I",[qq],kraus_ops)
        unencoded_pq=noise_data+unencoded_pq

    # print(gt_pq)
    # return

    measures=qvm.run(unencoded_pq,trials=trials)
    q=get_distr(np.array(measures))

    measures=qvm.run(encoded_pq,trials=trials)
    measures=retreive_logit_qubits(measures)
    if verbose:
        print('meansures:',len(measures))
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
    T=100
    r=100
    Ts=range(1,T)
    dpr_arr=np.zeros(len(Ts))
    dpq_arr=np.zeros(len(Ts))
    for i in range(len(Ts)):
        t=Ts[i]
        sum_dpr,sum_dpq=0,0
        for ir in range(r):
            dpq,dpr=test(t=t,noisy=True)
            sum_dpq+=dpq
            sum_dpr+=dpr
        dpr_arr[i]=sum_dpr/r
        dpq_arr[i]=sum_dpq/r

    np.savetxt('Ts.txt',np.array(Ts))
    np.savetxt('dpq.txt',dpq_arr)
    np.savetxt('dpr.txt',dpr_arr)

    # Ts=np.loadtxt('Ts.txt')
    # dpq_arr=np.loadtxt('dpq.txt')
    # dpr_arr=np.loadtxt('dpr.txt')
    # plot(Ts,dpr_arr,dpq_arr)