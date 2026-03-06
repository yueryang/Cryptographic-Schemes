from sys import argv, exit
from datetime import datetime
from hashlib import sha256
from math import log2
from pytz import timezone
from time import sleep, time
try:
	from numpy import arange, array, asarray, concatenate, dot, eye, fill_diagonal, kron, triu_indices, zeros
	from numpy.linalg import lstsq
	from numpy.random import randint
except Exception as e:
	print("Please install the library named \"numpy\" properly before this script can be run. ")
	print("Exception(s): ")
	print(e)
	print("Please press enter key to exit. ")
	input()
	exit(-1)
try:
	from sympy import Matrix
except Exception as e:
	print("Please install the library named \"sympy\" properly before this script can be run. ")
	print("Exception(s): ")
	print(e)
	print("Please press enter key to exit. ")
	input()
	exit(-1)
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
SCRIPT_NAME = "FS-MUAEKS.py"
DEFAULT_N = 256
DEFAULT_M = 4096
DEFAULT_Q = 256
DEFAULT_LS = 32
DEFAULT_LR = 4
parameters_dict = {} # {"n":16, "m":256, "q":16} # {"n":16, "m":256, "q":16, "l_S":32, "l_R":4} # Users should only modify the parameters here in this line to accomplish more experiments. 


# Class #
class PARS:
	def __init__(self, n = DEFAULT_N, m = DEFAULT_M, q = DEFAULT_Q, l_S = DEFAULT_LS, l_R = DEFAULT_LR, **extra_pars):
		if isinstance(n, int) and n > 0:
			self.__n = n
		else:
			print("The input n is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_N))
			self.__n = DEFAULT_N
		if isinstance(m, int) and m > 0:
			self.__m = m
		else:
			print("The input m is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_M))
			self.__m = DEFAULT_M
		if isinstance(q, int) and q > 0:
			self.__q = q
		else:
			print("The input q is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_Q))
			self.__q = DEFAULT_Q
		if isinstance(l_S, int) and l_S > 0:
			self.__l_S = l_S
		else:
			print("The input l_S is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_LS))
			self.__l_S = DEFAULT_LS
		if isinstance(l_R, int) and l_R > 0:
			self.__l_R = l_R
		else:
			print("The input l_R is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_LR))
			self.__l_R = DEFAULT_LR
		if self.__m % (self.__n << 1) != 0:
			print("The input n and m do not meet the requirement that \"2n | m\". They are defaulted to {0} and {1} respectively. ".format(DEFAULT_N, DEFAULT_M))
			self.__n = DEFAULT_N
			self.__m = DEFAULT_M
		if extra_pars:
			print("Extra parameters for setting up are detected, listed as follows. \n{0}\n\n*** Please check the global parameter dictionary. ***\n".format(list(extra_pars.keys())))
	def getN(self) -> int:
		return self.__n
	def getM(self) -> int:
		return self.__m
	def getQ(self) -> int:
		return self.__q
	def getLS(self) -> int:
		return self.__l_S
	def getLR(self) -> int:
		return self.__l_R
	def setB(self, B:array) -> None:
		self.__B = B
	def getB(self) -> array:
		return self.__B
	def setPkS(self, pk_S:tuple) -> None:
		self.__pk_S = pk_S
	def getPkS(self) -> tuple:
		return self.__pk_S
	def setSkS(self, sk_S:tuple) -> None:
		self.__sk_S = sk_S
	def getSkS(self) -> tuple:
		return self.__sk_S
	def setPkR(self, pk_R:tuple) -> None:
		self.__pk_R = pk_R
	def getPkR(self) -> tuple:
		return self.__pk_R
	def setSkR(self, sk_R:array) -> None:
		self.__sk_R = sk_R
	def getSkR(self) -> array:
		return self.__sk_R
	def setFt(self, F_t:array) -> None:
		self.__F_t = F_t
	def getFt(self) -> array:
		return self.__F_t
	def setCt(self, ct:tuple) -> None:
		self.__ct = ct
	def getCt(self) -> tuple:
		return self.__ct
	def setTrap(self, Trap:tuple) -> None:
		self.__Trap = Trap
	def getTrap(self) -> tuple:
		return self.__Trap
	def printVars(self, vars:list) -> None:
		if type(vars) not in (tuple, list):
			vars = [str(vars)]
		undefined = []
		for var in vars:
			var_name = "_PARS__{0}".format(var)
			if hasattr(self, var_name):
				print("{0} = {1}".format(var, getattr(self, var_name)))
			else:
				undefined.append(var)
		if undefined:
			print("Undefined variables: {0}".format(undefined))


# Child Functions #
def H_1(message:array, m:int) -> array:
	message_bytes = message.tobytes()
	sha256_hash = sha256()
	sha256_hash.update(message_bytes)
	hash_value = sha256_hash.digest()
	hash_string = "".join(format(byte, "08b") for byte in hash_value)
	hash_list = [int(bit) for bit in hash_string][:(m * (m - 1)) >> 1] # let hash_list has a maximum length of m(m - 1) / 2 to fill the hash value in the upper right corner of the matrix
	hash_list += [0] * (((m * (m - 1)) >> 1) - len(hash_list)) # fill into m(m - 1) / 2
	hash_array = eye(m, dtype = "int") # make the eye matrix
	hash_array[triu_indices(m, k = 1)] = hash_list # fill the hash value in the upper right corner of the matrix
	return hash_array

def TrapGen(pars:PARS) -> tuple:
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	g = (1 << arange(0, m // (n << 1))).reshape((1, m // (n << 1))) # size = (1, m / 2n)
	G = kron(eye(n, dtype = "int"), g) % q # size = (n, m / 2)
	B = randint(q, size = (n, m >> 1)) # size = (n, m / 2)
	R = randint(2, size = (m >> 1, m >> 1)) # size = (m / 2, m / 2)
	A_0i = concatenate((B, (dot(B, R) % q + G) % q), axis = 1) # size = (n, m)
	T_g = zeros((m // (n << 1), m // (n << 1)), dtype = "int") # size = (m / 2n, m / 2n)
	fill_diagonal(T_g, 2)
	fill_diagonal(T_g[1:], -1)
	T_G = kron(eye(n, dtype = "int"), T_g) % q # size = (m / 2, m / 2)
	G_ = G.T # size = (m / 2, n)
	T_Aa = concatenate(((eye(m >> 1, dtype = "int") + dot(dot(R, G_) % q, B) % q) % q, dot(-R, T_G) % q), axis = 1) # size = (m / 2, m)
	T_Ab = concatenate((dot((-G_) % q, B) % q, T_G), axis = 1) # size = (m / 2, m)
	T_A0i = concatenate((T_Aa, T_Ab), axis = 0) # size = (m, m)
	return (A_0i, T_A0i) # (size = (n, m), size = (m, m))

def ExtBasis(F_B0:array, T_B0:array, B_0:array, q:int) -> array:
	W = lstsq(B_0, F_B0, rcond = None)[0].astype("int") % q
	T = concatenate((concatenate((T_B0, W), axis = 1), concatenate((zeros((W.shape[1], T_B0.shape[1]), dtype = "int"), eye(W.shape[1], dtype = "int")), axis = 1)), axis = 0)
	return T

def SampleLeft(A:array, B:array, C_u:array, T_A:array, q:int) -> array: # converted from https://www.iacr.org/archive/asiacrypt2011/70730021/70730021.pdf
	E_S = zeros((A.shape[1], C_u.shape[1]), dtype = "int")
	for j in range(C_u.shape[1]):
		E_S[:, j] = lstsq(A, C_u[:, j], rcond = None)[0].astype("int") % q
	return E_S


# Procedure Functions #
def Setup(pars_dict:dict) -> PARS:
	print("/* Setup */")
	pars = PARS(**pars_dict)
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	B = randint(q, size = (6, n, m)) # size = (6, n, m)
	pars.setB(B)
	params = (n, m, q, H_1, B)
	print("params = {0}".format(params))
	print()
	return pars

def KeyGen_S(pars:PARS) -> PARS:
	print("/* KeyGen_S */")
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A, T_A = TrapGen(pars) # (size = (n, m), size = (m, m))
	U_S = randint(q, size = (n, n)) # size = (n, n)
	D_A = randint(q, size = (n, m)) # size = (n, m)
	A_W = randint(q, size = (n, m)) # size = (n, m)
	pk_S = (A, U_S, D_A, A_W)
	pars.setPkS(pk_S)
	sk_S = T_A # size = (m, m)
	pars.setSkS(sk_S)
	print()
	return pars

def KeyGen_R(pars:PARS) -> PARS:
	print("/* KeyGen_R */")
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	B_0, T_B0 = TrapGen(pars) # (size = (n, m), size = (m, m))
	U_R = randint(q, size = (n, n)) # size = (n, n)
	D_B = randint(q, size = (n, m)) # size = (n, m)
	B_W = randint(q, size = (n, m)) # size = (n, m)
	pk_R = (B_0, U_R, D_B, B_W)
	pars.setPkR(pk_R)
	sk_R = T_B0 # size = (m, m)
	pars.setSkR(sk_R)
	print()
	return pars

def KeyUpdate(pars:PARS) -> tuple:
	print("/* KeyUpdate */")
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	B = pars.getB()
	B_0 = pars.getPkR()[0]
	F_001 = concatenate((B_0, B[0, :, :], B[2, :, :], B[5, :, :]), axis = 1) # size = (n, 4m)
	F_01 = concatenate((B_0, B[0, :, :], B[3, :, :]), axis = 1) # size = (n, 3m)
	F_1 = concatenate((B_0, B[1, :, :]), axis = 1) # size = (n, 2m)
	F_011 = concatenate((B_0, B[0, :, :], B[3, :, :], B[5, :, :]), axis = 1) # size = (n, 4m)
	F_101 = concatenate((B_0, B[1, :, :], B[2, :, :], B[5, :, :]), axis = 1) # size = (n, 4m)
	F_11 = concatenate((B_0, B[1, :, :], B[3, :, :]), axis = 1) # size = (n, 3m)
	F_111 = concatenate((B_0, B[1, :, :], B[3, :, :], B[5, :, :]), axis = 1) # size = (n, 4m)
	F = (F_001, F_01, F_1, F_011, F_101, F_11, F_111)
	T_B0 = pars.getSkR() # size = (m, m)
	T_001 = ExtBasis(F_001, T_B0, B_0, q)
	T_01 = ExtBasis(F_01, T_B0, B_0, q)
	T_1 = ExtBasis(F_1, T_B0, B_0, q)
	T_011 = ExtBasis(F_011, T_B0, B_0, q)
	T_101 = ExtBasis(F_101, T_B0, B_0, q)
	T_11 = ExtBasis(F_11, T_B0, B_0, q)
	T_111 = ExtBasis(F_111, T_B0, B_0, q)
	start_time = time()
	sk = (				\
		(T_001, T_01, T_1), 		\
		(T_01, T_1), 		\
		(T_011, T_1), 		\
		(T_1, ), 			\
		(T_101, T_11), 		\
		(T_11, ), 			\
		(T_111, )			\
	)
	t = randint(7)
	print("sk_t = {0}".format(sk[t]))
	pars.setFt(F[t])
	end_time = time()
	print()
	return pars, end_time - start_time

def FS_MUAEKS(pars:PARS) -> PARS:
	print("/* FS_MUAEKS */")
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	l_S = pars.getLS()
	sk_S = pars.getSkS() # size = (m, m)
	pk_S = pars.getPkS()
	A = pk_S[0] # size = (n, m)
	U_S = pk_S[1] # size = (n, n)
	D_A = pk_S[2] # size = (n, m)
	A_W = pk_S[3] # size = (n, m)
	pk_R = pars.getPkR()
	D_B = pk_R[2] # size = (n, m)
	B_W = pk_R[3] # size = (n, m)
	F_t = pars.getFt() # size = (n, 2m | 3m | 4m)
	E_W = randint(q, size = (m, l_S)) # size = (m, l_S)
	S_S = randint(q, size = (n, l_S)) # size = (n, l_S)
	ck = randint(q, size = (n, 1)) # size = (n, 1) # shape[1] can be a random positive integer
	C_w = (E_W + dot((dot(A_W, asarray(Matrix(H_1(concatenate((*pk_S, *pk_R, ck), axis = 1), m)).inv()).astype("int") % q) % q).T, S_S) % q) % q # size = (m, l_S)
	R_A = (randint(2, size = (m, m)) << 1) - 1 # size = (m, m)
	R_C = (randint(2, size = (m, m)) << 1) - 1 # size = (m, m)
	C_a = (dot(A.T, S_S) % q + dot(R_A, E_W) % q) % q # size = (m, l_S)
	C_c = (dot(D_A.T, S_S) % q + dot(R_C, E_W) % q) % q # size = (m, l_S)
	R_B = (randint(2, size = (F_t.shape[1], m)) << 1) - 1 # size = (2m | 3m | 4m, m)
	E_U = randint(q, size = (n, l_S)) # size = (n, l_S)
	C_b = (dot(F_t.T, S_S) % q + dot(R_B, E_W) % q) % q # size = (2m | 3m | 4m, l_S)
	C_u = (dot(U_S, S_S) % q + E_U) % q # size = (n, l_S)
	E_S = SampleLeft(A, concatenate((F_t, D_B, dot(B_W, asarray(Matrix(H_1(concatenate((*pk_S, *pk_R, ck), axis = 1), m)).inv()).astype("int") % q) % q), axis = 1), C_u, sk_S, q) # size = (m, l_S)
	ct = (C_w, C_a, C_b, C_c, E_S)
	pars.setCt(ct)
	print("ct = {0}".format(ct))
	print()
	return pars

def Trapdoor(pars:PARS) -> PARS:
	print("/* Trapdoor */")
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	l_R = pars.getLR()
	pk_S = pars.getPkS()
	A = pk_S[0] # size = (n, m)
	U_S = pk_S[1] # size = (n, n)
	D_A = pk_S[2] # size = (n, m)
	A_W = pk_S[3] # size = (n, m)
	pk_R = pars.getPkR()
	D_B = pk_R[2] # size = (n, m)
	B_W = pk_R[3] # size = (n, m)
	sk_R = pars.getSkR() # size = (m, m)
	F_t = pars.getFt() # size = (n, 2m | 3m | 4m)
	S_R = randint(q, size = (n, l_R)) # size = (n, l_R)
	E__W = randint(q, size = (m, l_R)) # size = (m, l_R)
	tk = randint(q, size = (n, 1)) # size = (n, 1) # shape[1] can be a random positive integer
	T_w = (E__W + dot((dot(B_W, asarray(Matrix(H_1(concatenate((*pk_S, *pk_R, tk), axis = 1), m)).inv()).astype("int") % q) % q).T, S_R) % q) % q # size = (m, l_R)
	R__A = (randint(2, size = (m, m)) << 1) - 1 # size = (m, m)
	R__B = (randint(2, size = (F_t.shape[1], m)) << 1) - 1 # size = (2m | 3m | 4m, m)
	R__C = (randint(2, size = (m, m)) << 1) - 1 # size = (m, m)
	T_a = (dot(A.T, S_R) % q + dot(R__A, E__W) % q) % q # size = (m, l_R)
	T_b = (dot(F_t.T, S_R) % q + dot(R__B, E__W) % q) % q # size = (2m | 3m | 4m, l_R)
	T_c = (dot(D_B.T, S_R) % q + dot(R__C, E__W) % q) % q # size = (m, l_R)
	E__U = randint(q, size = (n, l_R)) # size = (n, l_R)
	T_u = (dot(U_S, S_R) % q + E__U) % q # size = (n, l_R)
	E_R = SampleLeft(F_t, concatenate((A, D_A, dot(A_W, asarray(Matrix(H_1(concatenate((*pk_S, *pk_R, tk), axis = 1), m)).inv()).astype("int") % q) % q), axis = 1), T_u, sk_R, q) # size = (2m | 3m | 4m, l_R)
	Trap = (T_w, T_a, T_b, T_c, E_R)
	pars.setTrap(Trap)
	print("Trap = {0}".format(Trap))
	print()
	return pars

def Test(pars:PARS) -> bool:
	print("/* Test */")
	q = pars.getQ()
	ct = pars.getCt()
	C_w = ct[0] # size = (m, l_S)
	C_a = ct[1] # size = (m, l_S)
	C_b = ct[2] # size = (2m | 3m | 4m, l_S)
	C_c = ct[3] # size = (m, l_S)
	E_S = ct[4] # size = (m, l_S)
	Trap = pars.getTrap()
	T_w = Trap[0] # size = (n, l_R)
	T_a = Trap[1] # size = (m, l_R)
	T_b = Trap[2] # size = (2m | 3m | 4m, l_R)
	T_c = Trap[3] # size = (m, l_R)
	E_R = Trap[4] # size = (2m | 3m | 4m, l_R)
	# n = (dot(E_R.T, concatenate((C_a, C_b, C_c, C_w), axis = 0)) % q - dot(concatenate((T_a.T, T_b.T, T_c.T, T_w.T), axis = 1), E_S) % q) % q # size = (l_R, l_S)
	n = (dot(E_R.T, C_b) % q - dot(T_a.T, E_S) % q) % q # size = (l_R, l_S)
	bRet = (n < q >> 2).all()
	print(int(bRet))
	print()
	return bRet


# Main Functions #
def getCurrentTime() -> str:
	tz = timezone("Asia/Shanghai")
	current_time = datetime.now(tz)
	return "{0} {1}".format(current_time.strftime("%Y/%m/%d %H:%M:%S"), current_time.tzname())

def printHelp() -> None:
	print("\"{0}\": A Python script for implementing FS-MUAEKS. ".format(SCRIPT_NAME), end = "\n\n")
	print("Option: ")
	print("\t[/n|-n|n]: Specify that the following option is the value of n (default: {0}). ".format(DEFAULT_N))
	print("\t[/m|-m|m]: Specify that the following option is the value of m (default: {0}). ".format(DEFAULT_M))
	print("\t[/q|-q|q]: Specify that the following option is the value of q (default: {0}). ".format(DEFAULT_Q))
	print("\t[/ls|--ls|ls|/l_s|--l_s|l_s]: Specify that the following option is the value of l_S (default: {0}). ".format(DEFAULT_LS))
	print("\t[/lr|--lr|lr|/l_r|--l_r|l_r]: Specify that the following option is the value of l_R (default: {0}). ".format(DEFAULT_LR))
	print("\t[/h|-h|h|/help|--help|help]: Show this help information. ", end = "\n\n")
	print("Format: ")
	print("\tpython \"{0}\" [/n|-n|n] n [/m|-m|m] m [/q|-q|q] q [/ls|--ls|ls|/l_s|--l_s|l_s] l_S [/lr|--lr|lr|/l_r|--l_r|l_r] l_R".format(SCRIPT_NAME))
	print("\tpython \"{0}\" [/h|-h|h|/help|--help|help]".format(SCRIPT_NAME), end = "\n\n")
	print("Example: ")
	print("\tpython \"{0}\"".format(SCRIPT_NAME))
	print("\tpython \"{0}\" /n {1} /m {2} /q {3}".format(SCRIPT_NAME, DEFAULT_N, DEFAULT_M, DEFAULT_Q))
	print("\tpython \"{0}\" -n {1} -m {2} -q {3} --ls {4} --lr {5}".format(SCRIPT_NAME, DEFAULT_N, DEFAULT_M, DEFAULT_Q, DEFAULT_LS, DEFAULT_LR))
	print("\tpython \"{0}\" n {1} m {2} q {3} l_s {4} l_r {5}".format(SCRIPT_NAME, DEFAULT_N, DEFAULT_M, DEFAULT_Q, DEFAULT_LS, DEFAULT_LR))
	print("\tpython \"{0}\" --help".format(SCRIPT_NAME), end = "\n\n")
	print("Exit code: ")
	print("\t{0}\tThe Python script finished successfully. ".format(EXIT_SUCCESS))
	print("\t{0}\tThe Python script finished not passing all the verifications. ".format(EXIT_FAILURE))
	print("\t{0}\tThe Python script received unrecognized commandline options. ".format(EOF), end = "\n\n")
	print("Note: ")
	print("\t1) All the commandline options are optional and not case-sensitive. ")
	print("\t2) The parameters n, m, q, l_S, and l_R should be positive integers and will obey the following priority: values obtained from the commandline > values specified by the user within the script > default values set within the script. ")
	print("\t3) The parameters n and m should meet the requirement that \"2n | m\". Otherwise, they will be set to their default values respectively. ", end = "\n\n")

def handleCommandline() -> dict:
	for arg in argv[1:]:
		if arg.lower() in ("/h", "-h", "h", "/help", "--help", "help", "/?", "-?", "?"):
			printHelp()
			return True
	commandline_dict = {}
	pointer = None
	for arg in argv[1:]:
		if arg.lower() in ("/n", "-n", "n"):
			pointer = "n"
		elif arg.lower() in ("/m", "-m", "m"):
			pointer = "m"
		elif arg.lower() in ("/q", "-q", "q"):
			pointer = "q"
		elif arg.replace("_", "").lower() in ("/ls", "--ls", "ls"):
			pointer = "l_S"
		elif arg.replace("_", "").lower() in ("/lr", "--lr", "lr"):
			pointer = "l_R"
		elif pointer is None:
			print("Error handling commandline, please check your commandline or use \"/help\" for help. ")
			return False
		else:
			commandline_dict[pointer] = arg
			pointer = None # reset
	for key in ("n", "m", "q", "l_S", "l_R"):
		try:
			if key in commandline_dict:
				commandline_dict[key] = int(commandline_dict[key])
		except:
			print("Error regarding {0} as an integer. Please check your commandline. ".format(key))
			return False
	return commandline_dict

def preExit(countdownTime = 5) -> None:
	try:
		cntTime = int(countdownTime)
		length = len(str(cntTime))
	except:
		return
	print()
	while cntTime > 0:
		print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime), end = "")
		try:
			sleep(1)
		except:
			print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(0))
			return
		cntTime -= 1
	print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime))

def main() -> int:
	if not argv[0].endswith(SCRIPT_NAME):
		print("Warning: This Python script should be named \"{0}\". However, it is currently specified as another name. ".format(SCRIPT_NAME))
	commandlineArgument = handleCommandline()
	if isinstance(commandlineArgument, bool):
		return EXIT_SUCCESS if commandlineArgument else EOF
	print("Program named \"{0}\" started at {1}. ".format(SCRIPT_NAME, getCurrentTime()))
	if commandlineArgument:
		print("Parameters resolved from commandline: {0}".format(commandlineArgument))
		parameters_dict.update(commandlineArgument)
	print("Parameters: {0}".format(parameters_dict), end = "\n" * 3)
	dicts = {}
	
	start_time = time()
	pars = Setup(parameters_dict)
	end_time = time()
	dicts["Setup"] = end_time - start_time
	
	start_time = time()
	pars = KeyGen_S(pars)
	end_time = time()
	dicts["KeyGen_S"] = end_time - start_time
	
	start_time = time()
	pars = KeyGen_R(pars)
	end_time = time()
	dicts["KeyGen_R"] = end_time - start_time
	
	pars, dicts["KeyUpdate"] = KeyUpdate(pars)
	
	start_time = time()
	pars = FS_MUAEKS(pars)
	end_time = time()
	dicts["FS_MUAEKS"] = end_time - start_time
	
	start_time = time()
	pars = Trapdoor(pars)
	end_time = time()
	dicts["Trapdoor"] = end_time - start_time
	
	start_time = time()
	bRet = Test(pars)
	end_time = time()
	dicts["Test"] = end_time - start_time
	
	if 0 == len(dicts):
		print("No experimental results are collected. ")
	elif 1 == len(dicts):
		print("The experimental result of the time consumption in seconds is shown as follows. ")
		print(dicts)
	else:
		print("The experimental results of the time consumption in seconds are shown as follows. ")
		print(dicts)
	preExit()
	print("\n\n\nProgram ended at {0} with exit code {1}. ".format(getCurrentTime(), EXIT_SUCCESS if bRet else EXIT_FAILURE))
	return EXIT_SUCCESS if bRet else EXIT_FAILURE



if __name__ == "__main__":
	exit(main())