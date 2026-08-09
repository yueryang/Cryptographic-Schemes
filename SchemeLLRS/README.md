## LLRS

This is the category of the FS-LLRS cryptographic scheme.

### SchemeLLRS

- ``SchemeLLRS.py``: This is the official simulation implementation of the FS-LLRS cryptographic scheme in Python programming language based on the NumPy library. It consolidates the Setup, KeyExtract, KeyUpdate, Sign, Verify, and Link experiment flow into the common Parser/Saver interface used by this repository.

The small default matrix dimensions are intended for continuous integration. The upstream production defaults are $q = 256$, $n = 256$, $m = 4096$, $d = 10$, and $k = 4$.

The implementation was imported from [yueryang/LLRS](https://github.com/yueryang/LLRS), revision ``1f1d46c46a17aad843fa30352546e37b8fe9906a``.

```bibtex
@article{chen2024fs,
  title={FS-LLRS: Lattice-based Linkable Ring Signature with Forward Security for Cloud-assisted Electronic Medical Records},
  author={Chen, Xue and Xu, Shiyuan and Gao, Shang and Guo, Yu and Yiu, Siu-Ming and Xiao, Bin},
  journal={IEEE Transactions on Information Forensics and Security},
  year={2024},
  publisher={IEEE}
}
```
