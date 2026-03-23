## SchemeHIBME

This is the category of the proposed HIB-ME cryptographic scheme, whose baseline is the AnonymousME cryptographic scheme. 

### ``SchemeHIBME.py``

This is the official implementation of the HIB-ME cryptographic scheme in Python programming language based on the Python charm library. 

#### Discussion

It is very interesting to tell the trend of the length of the encryption key in the encryption procedure as the variable $n$ grows with the variables $l$ and $m$ fixed. 

Let $K$ donates the encryption key in the encryption procedure, $x_1$ donates the length of the element in $G_1$, and $x_0$ donates the length of the element in $Z_r$, we have $\|K\| = \|K_1\| + \|K_2\| + \|K_3\| = n\|x_1\| + (l - n)\|x_0\| + (l - n)\|x_0\| = n\|x_1\| + 2(l - n)\|x_0\|$. 

Therefore, if the length of the element in $G_1$ is greater than twice the length of the element in $Z_r$, the total length $K$ increases as $n$ grows; if the length of the element in $G_1$ is smaller than twice the length of the element in $Z_r$, the total length of $K$ decreases as $n$ grows; and if the length of the element in $G_1$ is twice the length of the element in $Z_r$, the total length of $K$ is fixed. 

Consequently, when $n$ grows with the variables $l$ and $m$ fixed, the curve in the SS512 system is in an upward trend while that in the remaining systems is in a downward one. 

### ``SchemeAnonymousME.py``

This is the official implementation of the AnonymousME cryptographic scheme (``Anonymous Hierarchical Identity-based Encryption``) in Python programming language based on the Python charm library. 

#### Discussion

It is interesting to note that the AnonymousME cryptographic scheme can remain correct while the HIB-ME cryptographic scheme cannot when $g$ is set to a random element of $\mathbb{G}_1$ instead of a generator of it. 
