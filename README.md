# CS269Q Final Proj (Fault-Tolerant Operations on QPUs)

Quantum Processing Units (QPU) today are noisy and will remain noisy in the near future. 
Therefore fault-tolerant protocols are of paramount importance in running larger quantum algorithms to demonstrate quantum advantage. 
In this project, we will implement the 5-qubit fault-tolerant circuit introduced in (Gotesmann 2016) and run it on both QVM and QPU to study the effectiveness of the protocol on the respective platform.

## Code
 - `main.py`: encoding implemented for the noiseless QVM (progress report)
 - `test.py`: comparing errors on encoded and unencoded circuits on noisy QVM
 - `test_qpu.py`: comparing errors on encoded and unencoded circuits on QPU.

### References
Gotesmann 2016, Quantum  fault  tolerance  in  small  experiments. arXiv preprint arXiv:1610.03507, 2016.
