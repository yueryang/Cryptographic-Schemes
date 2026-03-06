from sys import argv, exit
from collections import OrderedDict
from datetime import datetime
from hashlib import sha256
from math import log2
from pytz import timezone
from time import sleep, time
try:
	from numpy import arange, array, asarray, concatenate, dot, eye, fill_diagonal, kron, sum as np_sum, triu_indices, zeros
	from numpy.linalg import matrix_rank
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
SCRIPT_NAME = "LB-PEAKS.py"
MAX_WIDTH = 20
DEFAULT_N = 256
DEFAULT_M = 9728
DEFAULT_Q = 4093
RAND_LB = 1
RAND_UB = 16
parameters = [{"n":16, "m":608, "q":251}, {"n":20, "m":800, "q":509}, {"n":256, "m":9728, "q":4093}, {"n":320, "m":12800, "q":8191}] # Users should only modify the parameters here in this line and the next line to accomplish their experiments. 
procedures = [("Setup", lambda p, j:Setup(p, j), 1, 10), ("KeyGen", lambda p, j:KeyGen(p, j), 10, 100), ("Authorize", lambda p, j:Authorize(p, j), 1, 1), ("Encrypt", lambda p, j:Encrypt(p, j), 100, 1000), ("Trapdoor", lambda p, j:Trapdoor(p, j), 100, 1000), ("Test", lambda p, j:Test(p, j), 100, 1000)]


# Class #
class PARS:
	def __init__(self, n = DEFAULT_N, m = DEFAULT_M, q = DEFAULT_Q, **extra_pars):
		if isinstance(n, int) and n > 1:
			self.__n = n
		else:
			print("The input n is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_N))
			self.__n = DEFAULT_N
		if isinstance(m, int) and m > 1:
			self.__m = m
		else:
			print("The input m is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_M))
			self.__m = DEFAULT_M
		if isinstance(q, int) and q > 1:
			self.__q = q
		else:
			print("The input q is not a positive integer. It is defaulted to {0}. ".format(DEFAULT_Q))
			self.__q = DEFAULT_Q
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
	def setA(self, A:array) -> None:
		self.__A = A
	def getA(self) -> array:
		return self.__A
	def setTA(self, T_A:array) -> None:
		self.__T_A = T_A
	def getTA(self) -> array:
		self.__T_A
	def setB(self, B:array) -> None:
		self.__B = B
	def getB(self) -> array:
		return self.__B
	def setK(self, k:int) -> None:
		self.__k = k
	def getK(self) -> int:
		return self.__k
	def setKw(self, kw:array) -> None:
		self.__kw = kw
	def getKw(self) -> array:
		return self.__kw
	def setU(self, U:array) -> None:
		self.__U = U
	def getU(self) -> array:
		return self.__U
	def setVecM(self, vec_M:array) -> None:
		self.__vec_M = vec_M
	def getVecM(self) -> array:
		return self.__vec_M
	def setL(self, l:int) -> None:
		self.__l = l
	def getL(self) -> int:
		return self.__l
	def setID(self, ID:array) -> None:
		self.__ID = ID
	def getID(self) -> array:
		return self.__ID
	def setLowerSKID(self, sk_ID:array) -> None:
		self.__sk_ID = sk_ID
	def getLowerSKID(self) -> array:
		return self.__sk_ID
	def setUpperSKID(self, SK_ID:array) -> None:
		self.__SK_ID = SK_ID
	def getUpperSKID(self) -> array:
		return self.__SK_ID
	def setY(self, y:array) -> None:
		self.__y = y
	def getY(self) -> array:
		return self.__y
	def setSigma(self, sigma:tuple) -> None:
		self.__sigma = sigma
	def getSigma(self) -> tuple:
		return self.__sigma
	def setCT(self, CT:tuple) -> None:
		self.__CT = CT
	def getCT(self) -> tuple:
		return self.__CT
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

def H_1(message:array, q:int, n:int) -> array:
	message_bytes = message.tobytes()
	sha256_hash = sha256()
	sha256_hash.update(message_bytes)
	hash_value = sha256_hash.digest()
	hash_string = "".join(format(byte, "02x") for byte in hash_value)
	hash_list = [int("0x" + bit, base = 16) % q for bit in hash_string][:n] # let hash_list has a maximum length of n
	hash_list += [0] * (n - len(hash_list)) # fill into n
	return array(hash_list).reshape(n, 1)

def H_2(message:array, q:int) -> int:
	message_bytes = message.tobytes()
	sha256_hash = sha256()
	sha256_hash.update(message_bytes)
	hash_value = sha256_hash.digest()
	return int(hash_value.hex(), base = 16) % q

def H_3(message:array, m:int) -> array:
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

def H_4(message:array, n:int, m:int) -> array:
	message_bytes = message.tobytes()
	sha256_hash = sha256()
	sha256_hash.update(message_bytes)
	hash_value = sha256_hash.digest()
	hash_string = "".join(format(byte, "08b") for byte in hash_value)
	hash_list = [int(bit) for bit in hash_string][:((n * (n - 1)) >> 1) + n * (m - n)] # let hash_list has a maximum length of n(n - 1) / 2 + n(m - n) to fill the hash value in the upper right corner of the matrix
	hash_list += [0] * (((n * (n - 1)) >> 1) + n * (m - n) - len(hash_list)) # fill into mn - n(n + 1) / 2
	hash_array = eye(n, dtype = "int") # make the eye matrix
	hash_array[triu_indices(n, k = 1)] = hash_list[:(n * (n - 1)) >> 1] # fill the hash value in the upper right corner of the matrix
	return concatenate((hash_array, array(hash_list[(n * (n - 1)) >> 1:], dtype = "int").reshape(n, m - n)), axis = 1) # fill to form a  n * m matrix

def SamplePre(A:array, T_A:array, hash_value:array, q:int) -> array:
	return dot(dot(A.T, asarray(Matrix(dot(A, A.T)).inv_mod(q)).astype("int")) % q, hash_value) % q

def f(sk_ID:array, kw:array, message:array, k:int, q:int) -> array:
	return (sk_ID + np_sum(kw[:k] * message[:k]) % q) % q

def f_1(sk_ID:array, KS_U:array, message:array, k:int, q:int) -> array:
	total = zeros(sk_ID.shape, dtype = "int")
	for kw in KS_U:
		total += f(sk_ID, kw, message, k, q)
	return total % q

def f_2(sk_ID:array, KS_W:array, message:array, k:int, q:int) -> array:
	total = zeros(sk_ID.shape)
	for kw in KS_W:
		total += f(sk_ID, kw, message, k, q)
	return total % q

def F(sk_ID:array, KS_U:array, KS_W:array, message:array, k:int, q:int) -> array:
	return (f_1(sk_ID, KS_U, message, k, q) - f_2(sk_ID, KS_W, message, k, q)) % q

def ExtBasis(F_B0:array, T_B0:array, B_0:array, q:int) -> array:
	W = dot(dot(B_0.T, asarray(Matrix(dot(B_0, B_0.T)).inv_mod(q)).astype("int")) % q, F_B0) % q
	T = concatenate((concatenate((T_B0, W), axis = 1), concatenate((zeros((W.shape[1], T_B0.shape[1]), dtype = "int"), eye(W.shape[1], dtype = "int")), axis = 1)), axis = 0)
	return T

def SampleLeft(A:array, B:array, C_u:array, T_A:array, q:int) -> array: # converted from https://www.iacr.org/archive/asiacrypt2011/70730021/70730021.pdf
	E_S = zeros((A.shape[1], C_u.shape[1]), dtype = "int")
	for j in range(C_u.shape[1]):
		E_S[:, j] = dot(dot(A.T, asarray(Matrix(dot(A, A.T)).inv_mod(q)).astype("int")) % q, C_u[:, j]) % q
	return E_S


# Procedure Functions #
def Setup(pars_dict:dict, round:int) -> PARS:
	print("/* Setup (Round {0}) */".format(round))
	pars = PARS(**pars_dict)
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A, T_A = TrapGen(pars) # (size = (n, m), size = (m, m))
	pars.setA(A)
	pars.setTA(T_A)
	B = randint(q, size = (n, m << 1)) # size = (n, 2m)
	pars.setB(B)
	k = randint(RAND_LB, min(m, RAND_UB))
	pars.setK(k)
	kw = randint(2, size = (k, 1)) # size = (k, 1)
	pars.setKw(kw)
	U = randint(q, size = (n, k)) # size = (n, k)
	pars.setU(U)
	vec_M = randint(q, size = (k, n, m << 1)) # size = (k, n, 2m)
	pars.setVecM(vec_M)
	vec_m = randint(q, size = (k, m)) # size = (k, m)
	u = randint(q, size = (n, 1)) # size = (n, 1)
	pp = (A, B, U, vec_M, vec_m, u, H_1, H_2, H_3, H_4)
	print("pp = {0}".format(pp))
	print("Msk = {0}".format(T_A))
	print()
	return pars

def KeyGen(pars:PARS, round:int) -> PARS:
	print("/* KeyGen (Round {0}) */".format(round))
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A = pars.getA() # size = (n, m)
	T_A = pars.getTA() # size = (m, m)
	l = randint(RAND_LB, min(n, RAND_UB))
	pars.setL(l)
	ID = (randint(2, size = (l, 1)) << 1) - 1 # size = (l, 1)
	pars.setID(ID)
	sk_ID = SamplePre(A, T_A, H_1(ID, q, n), q) # size = (m, 1)
	pars.setLowerSKID(sk_ID)
	print("sk_ID = {0}".format(sk_ID))
	print()
	return pars

def Authorize(pars:PARS, round:int) -> PARS:
	print("/* Authorize (Round {0}) */".format(round))
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A = pars.getA() # size = (n, m)
	T_A = pars.getTA() # size = (m, m)
	k = pars.getK()
	l = pars.getL()
	sk_ID = pars.getLowerSKID() # size = (m, 1)
	KS_W = randint(2, size = (randint(RAND_LB, RAND_UB), k)) # size = (randint, k)
	KS_U = concatenate((KS_W, randint(2, size = (randint(RAND_LB, RAND_UB), k))), axis = 0) # size = (randint + randint, k)
	message = concatenate((randint(2, size = (k, 1)), randint(2, size = (randint(RAND_LB, RAND_UB), 1))), axis = 0) # size = (k + randint, l)
	SK_ID = H_3(F(sk_ID, KS_U, KS_W, message, k, q), m) # size = (m, m)
	pars.setUpperSKID(SK_ID)
	y = randint(q, size = (m, 1)) # size = (m, 1)
	pars.setY(y)
	h = H_2(concatenate((dot(A, y) % q, dot(SK_ID, y) % q), axis = 0), q)
	z = (sk_ID * h % q + y) % q # size = (m, 1)
	sigma = (h, z)
	pars.setSigma(sigma)
	print("sigma = {0}".format(sigma))
	token = (SK_ID, sigma, y)
	print("token = {0}".format(token))
	print()
	return pars

def Encrypt(pars:PARS, round:int) -> PARS:
	print("/* Encrypt (Round {0}) */".format(round))
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A = pars.getA() # size = (n, m)
	B = pars.getB() # size = (n, 2m)
	k = pars.getK()
	kw = pars.getKw() # size = (k, 1)
	U = pars.getU() # size = (n, k)
	vec_M = pars.getVecM() # size = (k, n, 2m)
	ID = pars.getID() # size = (l, 1)
	A_kw = (np_sum(kw[:, :, None] * vec_M, axis = 0) % q + B) % q # size = (n, 2m)
	A_ID = concatenate((A, H_4(ID, n, m)), axis = 1) # size = (n, 2m)
	A_ID_kw = concatenate((A_ID, A_kw), axis = 1) # size = (n, 4m)
	R = (randint(2, size = (k, m << 1, m << 1)) << 1) - 1 # size = (k, 2m, 2m)
	R_kw = np_sum(kw[:, :, None] * R, axis = 0) % q # size = (2m, 2m)
	noi = randint(q)
	NOI = randint(q, size = (m << 1, 1)) # size = (2m, 1)
	r = randint(q, size = (n, 1)) # size = (n, 1)
	c_0 = (dot(U.T, r) % q + noi) % q # size = (n, k)
	c_1 = (dot(A_ID_kw.T, r) % q + concatenate((NOI, dot(R_kw.T, NOI) % q), axis = 0)) % q # size = (4m, 1)
	CT = (c_0, c_1)
	pars.setCT(CT)
	print("CT = {0}".format(CT))
	print()
	return pars

def Trapdoor(pars:PARS, round:int) -> PARS:
	print("/* Trapdoor (Round {0}) */".format(round))
	n = pars.getN()
	m = pars.getM()
	q = pars.getQ()
	A = pars.getA() # size = (n, m)
	T_A = pars.getTA() # size = (m, m)
	B = pars.getB() # size = (n, 2m)
	kw = pars.getKw() # size = (k, 1)
	U = pars.getU() # size = (n, k)
	vec_M = pars.getVecM() # size = (k, n, 2m)
	ID = pars.getID() # size = (l, 1)
	SK_ID = pars.getUpperSKID() # size = (m, m)
	y = pars.getY() # size = (m, 1)
	sigma = pars.getSigma()
	A_kw = (np_sum(kw[:, :, None] * vec_M, axis = 0) % q + B) % q # size = (n, 2m)
	A_ID = concatenate((A, H_4(ID, n, m)), axis = 1) % q # size = (n, 2m)
	T_A_ID = randint(q, size = (m << 1, m << 1)) # ExtBasis(A_ID, T_A, A) # size = (2m, 2m)
	trap_1 = dot(SK_ID, y) % q # size = (m, 1)
	trap_2 = randint(q, size = (m << 2, 1)) # SampleLeft(A_ID, A_kw, T_A_ID, U, q) # size = (4m, 1)
	Trap = (trap_1, trap_2, sigma)
	pars.setTrap(Trap)
	print("Trap = {0}".format(Trap))
	print()
	return pars

def Test(pars:PARS, round:int) -> bool:
	print("/* Test (Round {0}) */".format(round))
	n = pars.getN()
	q = pars.getQ()
	A = pars.getA() # size = (n, m)
	ID = pars.getID() # size = (l, 1)
	CT = pars.getCT()
	c_0 = CT[0] # size = (n, k)
	c_1 = CT[1] # size = (4m, 1)
	Trap = pars.getTrap()
	trap_1 = Trap[0] # size = (m, 1)
	trap_2 = Trap[1] # size = (4m, 1)
	sigma = Trap[2]
	h = sigma[0]
	z = sigma[1] # size = (m, 1)
	bRet = (h == H_2(concatenate(((dot(A, z) - H_1(ID, q, n) * h % q) % q, trap_1), axis = 0), q)) and matrix_rank((c_0 - dot(trap_2.T, c_1) % q) % q) <= q >> 2
	print(int(bRet))
	print()
	return bRet


# Main Functions #
def getCurrentTime() -> str:
	tz = timezone("Asia/Shanghai")
	current_time = datetime.now(tz)
	return "{0} {1}".format(current_time.strftime("%Y/%m/%d %H:%M:%S"), current_time.tzname())

def printHelp() -> None:
	print("\"{0}\": A Python script for implementing LB-PEAKS. ".format(SCRIPT_NAME), end = "\n\n")
	print("Option: ")
	print("\t[/n|-n|n]: Specify that the following option is the value of n (default: {0}). ".format(DEFAULT_N))
	print("\t[/m|-m|m]: Specify that the following option is the value of m (default: {0}). ".format(DEFAULT_M))
	print("\t[/q|-q|q]: Specify that the following option is the value of q (default: {0}). ".format(DEFAULT_Q))
	print("\t[/h|-h|h|/help|--help|help]: Show this help information. ", end = "\n\n")
	print("Format: ")
	print("\tpython \"{0}\" [/n|-n|n] n [/m|-m|m] m [/q|-q|q] q".format(SCRIPT_NAME))
	print("\tpython \"{0}\" [/h|-h|h|/help|--help|help]".format(SCRIPT_NAME), end = "\n\n")
	print("Example: ")
	print("\tpython \"{0}\"".format(SCRIPT_NAME))
	print("\tpython \"{0}\" /n {1} /m {2} /q {3}".format(SCRIPT_NAME, DEFAULT_N, DEFAULT_M, DEFAULT_Q))
	print("\tpython \"{0}\" --help".format(SCRIPT_NAME), end = "\n\n")
	print("Exit code: ")
	print("\t{0}\tThe Python script finished successfully. ".format(EXIT_SUCCESS))
	print("\t{0}\tThe Python script finished not passing all the verifications. ".format(EXIT_FAILURE))
	print("\t{0}\tThe Python script received unrecognized commandline options. ".format(EOF), end = "\n\n")
	print("Note: ")
	print("\t1) All the commandline options are optional and not case-sensitive. ")
	print("\t2) The commandline parameters will be appended to the parameter list specified by the user within the script. ")
	print("\t3) The parameters n, m, and q should be positive integers that greater than 1. ")
	print("\t4) The parameters n and m should meet the requirement that \"2n | m\". Otherwise, they will be set to their default values respectively. ", end = "\n\n")

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
		elif pointer is None:
			print("Error handling commandline, please check your commandline or use \"/help\" for help. ")
			return False
		else:
			commandline_dict[pointer] = arg
			pointer = None # reset
	for key in ("n", "m", "q"):
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
		parameters.append(commandlineArgument)
	print("Parameters: {0}".format(parameters), end = "\n" * 3)
	
	orderedDict = OrderedDict()
	for procedure in procedures:
		orderedDict[procedure[0]] = OrderedDict()
	bRet = True
	for parameter in parameters:
		key = (parameter["n"] if "n" in parameter else DEFAULT_N, parameter["m"] if "m" in parameter else DEFAULT_M, parameter["q"] if "q" in parameter else DEFAULT_Q)
		print("/** parameter = {0} **/".format(parameter))
		for i, procedure in enumerate(procedures):
			orderedDict[procedure[0]][key] = OrderedDict()
			start_time = time()
			for j in range(1, procedure[-1] + 1):
				if 0 == i:
					pars = procedure[1](parameter, j)
				elif len(procedures) - 1 == i:
					bRet = procedure[1](pars, j) and bRet
				else:
					pars = procedure[1](pars, j)
				if j % procedure[-2] == 0:
					end_time = time()
					orderedDict[procedure[0]][key][j] = end_time - start_time
		print()
		print("The experimental results of the time consumption in seconds are shown as follows. ")
		print(orderedDict)
		print()
	print()
	
	preExit()
	print("\n\n\nProgram ended at {0} with exit code {1}. ".format(getCurrentTime(), EXIT_SUCCESS if bRet else EXIT_FAILURE))
	return EXIT_SUCCESS if bRet else EXIT_FAILURE



if __name__ == "__main__":
	exit(main())