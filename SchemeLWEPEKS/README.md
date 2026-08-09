## LWE-PEKS

This is the category of the LWE-PEKS cryptographic scheme.

### SchemeLWEPEKS

- ``SchemeLWEPEKS.py``: This is the official simulation implementation of the LWE-PEKS cryptographic scheme in Python programming language based on the NumPy library. It consolidates the upstream setup, derivation, encryption, trapdoor, and search experiments into the common Parser/Saver interface used by this repository.

The upstream implementation uses MATLAB and is intended to simulate the time consumption of the LWE-PEKS procedures. The bounded parameters in this implementation make the same experiment structure suitable for automated testing; they are not production security parameters.

The implementation was imported from [yueryang/LWE-PEKS](https://github.com/yueryang/LWE-PEKS), revision ``fc6202f46fbd0e48567c514d0b18d29d40d513d5``.
