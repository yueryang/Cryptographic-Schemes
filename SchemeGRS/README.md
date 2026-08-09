## GRS

This is the category of the GRS cryptographic scheme.

### SchemeGRS

- ``SchemeGRS.java``: This is the official implementation of the GRS cryptographic scheme in Java programming language based on the JPBC library. It consolidates the upstream multi-file implementation into one source file and uses the common Parser/Saver interface of this repository.

The implementation contains both signature constructions from ``From $\Sigma$-protocol Based Signatures to Ring Signatures: General Construction and Applications``. Object sizes are calculated from encoded cryptographic elements, so the former ClassMexer dependency is no longer required.

The implementation was imported from [yueryang/GRS](https://github.com/yueryang/GRS), revision ``c0ec5024cb8321884fb254a4ddeabe1657f40b79``.
