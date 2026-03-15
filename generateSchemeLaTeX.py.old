import os
from sys import argv, executable, exit
from codecs import lookup
from re import findall
from subprocess import Popen, PIPE
from time import sleep, time
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
PLATFORM = __import__("platform").system().upper()
STARTUP_COMMAND_FORMAT = "START \"\" \"{0}\" \"{1}\" \"{2}\"" if "WINDOWS" == PLATFORM else "\"{0}\" \"{1}\" \"{2}\" &"


def getTxt(filePath:str) -> str|None: # get ``*.txt`` content
	for coding in ("utf-8", "ANSI", "utf-16", "gbk"): # codings (add more codings here if necessary)
		try:
			with open(filePath, "r", encoding = coding) as f:
				content = f.read()
			return content[1:] if content.startswith("\ufeff") else content # if utf-8 with BOM, remove BOM
		except (UnicodeError, UnicodeDecodeError):
			continue
		except:
			return None
	return None

def callSleep(sleepingTime:int = 3) -> bool:
	try:
		sleep(sleepingTime)
		return True
	except KeyboardInterrupt:
		print()
	except BaseException:
		pass
	return False

def convertEscaped(string:str) -> str:
	if isinstance(string, str):
		vec = list(string)
		d = {"\\":"\\\\", "\"":"\\\"", "\'":"\\\'", "\a":"\\a", "\b":"\\b", "\f":"\\f", "\n":"\\n", "\r":"\\r", "\t":"\\t", "\v":"\\v"}
		for i, ch in enumerate(vec):
			if ch in d:
				vec[i] = d[ch]
			elif not ch.isprintable():
				vec[i] = "\\x" + hex(ord(ch))[2:]
		return "\"" + "".join(vec) + "\""
	else:
		return str(string)

if PLATFORM == "WINDOWS":
	def checkFile(filePath:str, lines:tuple|list|set, sleepingTime:int = 3) -> bool:
		patterns = (																															\
			" = Scheme\\(curveType[A-Za-z, ]+\\)", " = sum\\(.*^(start = ).*\\)", "\\$\\\\textbf{return", "\\\\vec{.+} = .+ \\\\gets .+ ", "^ +\\S.*$", "^def conductScheme\\(.+round\\)", 	\
			"^def conductScheme\\(curveType:tuple\\|list\\|str, [A-Za-z:\\|, _]+round:int\\|None = None\\)", "cipher:.+\\\\textit{ct}.+\\\\rightarrow", 								\
			"cipherText:.+ (?:c|C)(?:\\, |\\)).+\\\\rightarrow", "def Setup\\(self:object, [A-Za-z:\\|, _]+\\)", "for idx in range\\([0-9]+, [A-Za-z]+\\)", "len.+# type check"		\
		)
		if isinstance(filePath, str) and isinstance(lines, (tuple, list, set)):
			cnt = 0
			for pattern in patterns:
				invalidLines = []
				for idx, line in enumerate(lines):
					if isinstance(line, str):
						if findall(pattern, line):
							invalidLines.append((idx, line))
					else:
						print("** Warning: An unofficial statement detected or an unofficial generator used, please check whether official Python scripts are used. **")
						print("Detail: \"{0}\"".format(filePath))
						callSleep(sleepingTime)
						return len(patterns)
				if invalidLines:
					cnt += 1
					print("** Warning: An unofficial statement detected, please check whether official Python scripts are used. **")
					for idx, line in invalidLines:
						print("Detail: \"{0}\" ({1}): {2}".format(filePath, idx, convertEscaped(line)))
					callSleep(sleepingTime)
			return cnt
		else:
			print("** Warning: An unofficial statement detected or an unofficial generator used, please check whether official Python scripts are used. **")
			callSleep(sleepingTime)
			return len(patterns)
else:
	def checkFile(filePath:str, lines:None = None, sleepingTime:int = 3) -> int:
		patterns = (																													\
			" = Scheme\\\\(curveType[A-Za-z, ]+\\\\)", " = sum\\\\(.*^(start = ).*\\\\)", "\\\\\\$\\\\\\\\textbf{return", 				\
			"\\\\vec{.+} = .+ \\\\gets .+ ", "^ +\\\\S.*\\$", "^def conductScheme\\\\(.+round\\\\)", 									\
			"^def conductScheme\\\\(curveType:tuple\\\\|list\\\\|str, [A-Za-z:\\\\|, ]+round:int\\\\|None = None\\\\)", 				\
			"cipher:.+\\\\\\\\textit{ct}.+\\\\\\\\rightarrow", "cipherText:.+ (c|C)(\\\\, |\\\\)).+\\\\\\\\rightarrow", 				\
			"def Setup\\\\(self:object, [A-Za-z:\\|, _]+\\\\)", "for idx in range\\\\([0-9]+, [A-Za-z]+\\\\)", "len.+# type check"		\
		)
		if isinstance(filePath, str):
			cnt = 0
			for pattern in patterns:
				commandline = "grep -H --color=always -E \"{0}\" \"{1}\"".format(pattern, filePath)
				with Popen(commandline, stdout = PIPE, stderr = PIPE, shell = True) as process:
					output, error = process.communicate()
					if error:
						print("** Warning: An unofficial statement detected or an unofficial generator used, please check whether official Python scripts are used. **")
						print("Detail: \"{0}\": {1}".format(filePath, error))
						callSleep(sleepingTime)
						return len(patterns)
					elif output:
						cnt += 1
						print("** Warning: An unofficial statement detected, please check whether official Python scripts are used. **")
						os.system(commandline + " | sed \'s/^/Detail: /\'")
						callSleep(sleepingTime)
			return cnt
		else:
			print("** Warning: An unofficial statement detected or an unofficial generator used, please check whether official Python scripts are used. **")
			callSleep(sleepingTime)
			return len(patterns)

def fetchPrompts(filePath:str, idx:int|str, s:str, className:str|None, functionName:str|None, sleepingTime:int = 3) -> bool:
	if isinstance(filePath, str) and isinstance(idx, (int, str)) and isinstance(s, str):
		if isinstance(className, str) and className.isalnum() and isinstance(functionName, str) and functionName.isalnum():
			if s in (																																			\
				functionName + ": An irregular security parameter ($\\\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ", 		\
				"{0}: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``{0}`` subsequently. ".format(functionName), 					\
				functionName + ": The passed message (bytes) is too long, which has been cast. ", functionName + ": The passed message (int) is too long, which has been cast. ", 			\
				functionName + ": The variable $M$ should be an element of $\\\\mathbb{G}_T$ but it is not, which has been generated randomly. ", 									\
				functionName + ": The variable $\\textit{ek}_{\\textit{id}^*}$ should be an element of $\\\\mathbb{G}_1$ but it is not, which has been generated randomly. ", 				\
				functionName + ": The variable $m$ should be an element of $\\\\mathbb{G}_T$ but it is not, which has been generated randomly. ", 									\
				"{0}: The variable $M$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\\\"{1}\\\". ".format(functionName, className), 					\
				"{0}: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\\\"{1}\\\". ".format(functionName, className)					\
			):
				return True
			elif (																																																\
				findall("^{0}: Each of the variables (?:\\$.+\\$\\, )+and \\$.+\\$ should be a tuple containing .+ .+(?: and .+ .+)? but at least one of them is not\\, all of which have been generated randomly\\. $".format(functionName), s)					\
				or findall("^{0}: The variable \\$.+\\$ has been generated accordingly\\. $".format(functionName), s)																												\
				or findall("^{0}: The variable \\$[a-z]\\$ should be a positive integer but it is not\\, which has been defaulted to \\$\\d+\\$\\. $".format(functionName), s)																		\
				or findall("^{0}: The variable \\$[a-z]\\$ should be a positive integer not smaller than \\$\\d+\\$ but it is not\\, which has been defaulted to \\$\\d+\\$\\. $".format(functionName), s)													\
				or findall("^{0}: The variable \\$.+\\$ should be a ``bytes`` object but it is not\\, which has been generated randomly\\. $".format(functionName), s)																			\
				or findall("^{0}: The variable \\$.+\\$ should be a tuple containing .+ .+(?: and .+ .+)? but it is not\\, which has been generated (?:randomly|accordingly)\\. $".format(functionName), s)												\
				or findall("^{0}: The variable \\$.+\\$ should be a tuple containing .+ .+(?: and .+ .+)? but it is not\\, which has been generated with \\$(?:M|m)\\$ set to b\\\\\\\"{1}\\\\\\\"\\. $".format(functionName, className), s)						\
				or findall("^{0}: The variable \\$.+\\$ should be a tuple containing .+ .+(?: and .+ .+)? but it is not\\, which has been generated with \\$M \\\\\\\\in \\\\\\\\mathbb{{G}}_T\\$ generated randomly\\. $".format(functionName), s)				\
				or findall(																																														\
					"^{0}: The variable \\$.+\\$ should be a tuple containing \\$.+ = .+\\$ ``bytes`` objects where the integer \\$.+ \\\\\\\\in .+\\$ but it is not\\, which has been generated randomly with a length of \\$.+ = .+\\$\\. $".format(functionName), s	\
				)																																															\
				or findall(																																														\
					(																																														\
						"^{0}: The variable \\$.+\\$ should be a tuple containing \\$.+ = .+\\$ elements(?: of \\$\\\\\\\\mathbb\\{{\\{{Z\\}}\\}}_r\\$)?(?: where the integer \\$.+ \\\\\\\\in .+\\$)? but it is not\\, "											\
						+ "which has been generated (?:randomly with a length of \\$.+\\$|accordingly)\\. $"																													\
					).format(functionName), s																																									\
				)																																															\
				or findall("^{0}: The variable \\$.+\\$ should be an element(?: of \\$\\\\\\\\mathbb(?:\\{{Z\\}}_r|\\{{G\\}}_2)\\$)? but it is not\\, which has been generated (?:randomly|accordingly)\\. $".format(functionName), s)							\
			):
				return True
			else:
				print("** Warning: An unofficial statement detected, please check whether official Python scripts are used. **")
				print("Detail: \"{0}\" ({1}): {2} (in Function ``{3}`` of Class ``{4}``)".format(filePath, idx, convertEscaped(s), functionName, className))
				callSleep(sleepingTime)
				return False
		elif isinstance(className, str) and className.isalnum() and functionName is None:
			if s in (																										\
				"Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ", 						\
				"Init: This scheme is only applicable to symmetric groups of prime orders. The curve type has been defaulted to \\\"SS512\\\". "	\
			):
				return True
			else:
				print("** Warning: An unofficial statement detected, please check whether official Python scripts are used. **")
				print("Detail: \"{0}\" ({1}): {2} (in Function ``{3}``)".format(filePath, idx, convertEscaped(s), functionName))
				callSleep(sleepingTime)
				return False
		elif className is None and functionName is None and (
			s in (																															\
				"", "Dec1:", "Dec2:", "Decrypted:", "Derived:", "Is ``ReEnc`` passed? {0}. YesNo", "Is ``Dec1`` passed (m == message)? {0}. YesNo", 			\
				"Is ``Dec2`` passed (m\' == message)? {0}. YesNo", "Is ``ProxyDec`` passed? {0}. YesNo", "Is ``ProxyEnc`` passed? {0}. YesNo", 				\
				"Is the deriver passed (message == M\')? {0}. YesNo", "Is the deriver passed (message == m\')? {0}. YesNo", 									\
				"Is the scheme correct (message == M)? {0}. YesNo", "Is the scheme correct (message == m)? {0}. YesNo", 									\
				"Is the scheme passed (result != False)? {0}. YesNo", "Is the system valid? No. \\n\\t{0}", 													\
				"Is the system valid? No. The parameter $n$ should be a positive integer, and the parameter $d$ should be a positive integer not smaller than $2$. ", 	\
				"Is the system valid? No. The parameters $m$, $n$, and $d$ should be three positive integers. ", "Is the system valid? Yes. ", 						\
				"Is the tracing verified? {0}. YesNo", "Original:", "Please press the enter key to exit ({0}). ", "Please press the enter key to exit. ", 				\
				"Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \\\"Ctrl + C\\\" ({1}). \\n", 					\
				"Saver: \\n{0}\\n", "Saver: \\n{0}\\n\\nFailed to save the results to \\\"{1}\\\" due to the following exception(s). \\n\\t{2}", 						\
				"Saver: \\n{0}\\n\\nFailed to save the results to \\\"{1}\\\" since the parent folder was not created successfully. ", 								\
				"Saver: \\n{0}\\n\\nThe overwriting is canceled by users. ", 																			\
				"Please refer to https://github.com/JHUISI/charm if necessary.  ", "Space:", 									\
				"Successfully saved the results to \\\"{0}\\\" in the plain text form. ", "Successfully saved the results to \\\"{0}\\\" in the three-line table form. ", 		\
				"The environment of the Python ``charm`` library is not handled correctly. ", "The results are empty. ", "Time:", 								\
				"The experiments were interrupted by the following exceptions. The program will try to save the results collected. \\n\\t{0}", "Verify:", 				\
				"\\nThe experiments were interrupted by users. The program will try to save the results collected. ", 											\
				"curveType =", "curveType = Unknown", "d =", "k =", "l =", "m =", "n =", "round =", "secparam ="											\
			) or findall("^Is the system valid\\? No\\. The parameter \\$[a-z]\\$ should be a positive integer\\. $", s)											\
			or findall("^Is the system valid\\? No\\. The parameters? \\$.+\\$ should be .+ positive integers? satisfying \\$.+\\$\\. $", s)								\
		):
			return True
		else:
			print("** Warning: An unofficial statement detected, please check whether official Python scripts are used. **")
			print("Detail: \"{0}\" ({1}): {2}".format(filePath, idx, convertEscaped(s)))
			callSleep(sleepingTime)
			return False
	else:
		print("** Warning: An unofficial statement detected or an unofficial generator used, please check whether official Python scripts are used. **")
		callSleep(sleepingTime)
		return False

def handleFolder(fd:str) -> bool:
	folder = str(fd)
	if not folder:
		return True
	elif os.path.exists(folder):
		return os.path.isdir(folder)
	else:
		try:
			os.makedirs(folder)
			return True
		except:
			return False

def generateSchemeTxt(pythonFilePath:str) -> bool:
	if isinstance(pythonFilePath, str):
		if os.path.isfile(pythonFilePath) and not os.path.islink(pythonFilePath) and os.path.splitext(pythonFilePath)[1].lower() == ".py":
			content, folderPath, fileName = getTxt(pythonFilePath), pythonFilePath[:-3] + "LaTeX", os.path.split(pythonFilePath)[1][:-3] + ".tex"
			if content is None:
				print("Failed to read \"{0}\". ".format(pythonFilePath))
				return False
			elif handleFolder(folderPath):
				# LaTeX Generation #
				try:
					startTime = time()
					with open(os.path.join(folderPath, fileName), "w", encoding = "utf-8") as f:
						f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{amsmath,amssymb}\n\\usepackage{bm}\n\n\\begin{document}\n\n")
						className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
						printFlag, bucketCount, buffer, warningCount = 0, 0, "", checkFile(pythonFilePath, content.splitlines())
						for idx, line in enumerate(content.splitlines()):
							if line.startswith("class Scheme"): # class SchemeXXX
								className = findall("^[0-9A-Za-z]+", line[6:])
								if className:
									className = className[0]
									if len(className) >= 7:
										f.write("\\section{{{0}}}\n\n".format(className))
										functionName, schemeFlag, doubleSeparatorFlag = None, False, True
									else:
										className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
								else:
									className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
							elif className is not None and line.startswith("\tdef ") and "(self:object" in line and ") -> " in line and ": # " in line: # def XXX
								functionName, schemeFlag, doubleSeparatorFlag = line[5:line.index("(self:object")].strip(), False, True
								if "__init__" == functionName:
									f.write(line[line.index(": # ") + 4:] + "\n\n")
									functionName = None
								elif "__" in functionName:
									functionName = None
								else:
									f.write("\\subsection{" + line[line.index(": # ") + 4:].strip() + "}\n\n")
							elif className is not None and functionName is not None and "\t\t# Scheme #" == line: # XXX # Scheme # XXX
								schemeFlag, doubleSeparatorFlag = True, True
							elif className is not None and functionName is not None and schemeFlag and " # " in line:
								prompt = line[line.index(" # ") + 3:].lstrip()
								if "$" == prompt.strip():
									doubleSeparatorFlag = not doubleSeparatorFlag # invert the double separator switch
								elif (prompt.startswith("$") or prompt.startswith("\\quad$")) and not prompt.rstrip().endswith("$"):
									doubleSeparatorFlag = False # disable the double separator switch
								elif not prompt.startswith("$") and prompt.rstrip().endswith("$"):
									doubleSeparatorFlag = True # enable the double separator switch
								tabCount = 0
								for tabIdx in range(0, len(prompt), 5):
									if prompt[tabIdx:].startswith("\\quad"):
										tabCount += 1
									else:
										break
								f.write("\t" * tabCount + prompt + ("\n\n" if doubleSeparatorFlag else "\n"))
								if line.startswith("\t\treturn "):
									functionName, schemeFlag, doubleSeparatorFlag = None, False, True
							elif className is not None and functionName is not None and schemeFlag and line.lstrip().startswith("# ") and line.rstrip().endswith("\\textbf{end if}"):
								f.write(line.lstrip()[2:].lstrip() + ("\n\n" if doubleSeparatorFlag else "\n"))
							elif not line.startswith("\t") and line.strip() and not line.lstrip().startswith("#"): # Reset
								className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True # reset
							
							# Official Line Check #
							if line.lstrip().startswith("print(") or printFlag:
								printFlag, escapeFlag, stringFlag = idx + 1, False, 0
								for ch in line if printFlag else line[line.index("print(") + 5:]: # include the '('
									if '\\' == ch:
										if escapeFlag and stringFlag:
											buffer += "\\\\"
										escapeFlag = not escapeFlag
									elif '\"' == ch:
										if 2== stringFlag:
											if escapeFlag: # "XXX\"XXX"
												buffer += "\\\""
												escapeFlag = False
											else: # "XXX"
												stringFlag = 0
										elif 1 == stringFlag: # "'"
											buffer += "\""
											escapeFlag = False
										elif escapeFlag:
											escapeFlag = False
										else:
											stringFlag = 2
									elif '\'' == ch:
										if 2 == stringFlag: # '"'
											buffer += "\'"
											escapeFlag = False
										elif 1 == stringFlag:
											if escapeFlag: # 'XXX\'XXX'
												buffer += "\\\'"
												escapeFlag = False
											else: # 'XXX'
												stringFlag = 0
										elif escapeFlag:
											escapeFlag = False
										else:
											stringFlag = 1
									elif '#' == ch:
										if stringFlag:
											if escapeFlag:
												buffer += "\\#"
												escapeFlag = False
											else:
												buffer += "#"
										else:
											escapeFlag = False
											break
									elif '(' == ch:
										if stringFlag:
											if escapeFlag:
												buffer += "\\("
												escapeFlag = False
											else:
												buffer += "("
										else:
											escapeFlag = False
											bucketCount += 1
									elif ')' == ch:
										if stringFlag:
											if escapeFlag:
												buffer += "\\)"
												escapeFlag = False
											else:
												buffer += ")"
										else:
											bucketCount -= 1
											if bucketCount <= 0:
												if not fetchPrompts(pythonFilePath, printFlag if idx + 1 == printFlag else "from {0} to {1}".format(printFlag, idx + 1), buffer, className, functionName):
													warningCount += 1
												printFlag, buffer, escapeFlag = 0, "", False
												break
									elif stringFlag:
										if escapeFlag:
											buffer += "\\" + ch
											escapeFlag = False
										else:
											buffer += ch
						f.write("\\end{document}")
					endTime = time()
					generationTimeDelta = endTime - startTime
					print("The LaTeX generation for \"{0}\" finished in {1:.9f} second(s) with {2} warning(s). ".format(pythonFilePath, generationTimeDelta, warningCount))
					
					# LaTeX Compilation #
					try:
						startTime = time()
						process = Popen(["pdflatex", fileName], cwd = folderPath)
						endTime = time()
						compilationTimeDelta = endTime - startTime
						if process.wait() == EXIT_SUCCESS:
							print("The LaTeX compilation for \"{0}\" succeeded in {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return True
						else:
							print("The LaTeX compilation for \"{0}\" failed. The time consumption is {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return False
					except BaseException as compilationBE:
						print("The LaTeX compilation for \"{0}\" failed since {1}. ".format(pythonFilePath, compilationBE))
						return False
				except BaseException as generationBE:
					print("The LaTeX generation for \"{0}\" failed since {1}. ".format(pythonFilePath, generationBE))
					return False
			else:
				print("The TEX generation for \"{0}\" failed since the parent folder was not created successfully. ".format(pythonFilePath))
				return False
		else:
			print("The passed file \"{0}\" is not a normal Python file. ".format(pythonFilePath))
			return False
	else:
		print("The passed parameter should be a string. ")
		return False

def main() -> int:
	successCount, totalCount = 0, 0
	if len(argv) >= 3:
		print("As multiple options are provided, these options will be handled in the child processes. ")
		for mainTexPath in argv[1:]:
			totalCount += 1
			commandline = STARTUP_COMMAND_FORMAT.format(executable, __file__, mainTexPath)
			exitCode = os.system(commandline)
			print("$ {0} -> {1}".format(commandline, exitCode))
			if exitCode == EXIT_SUCCESS:
				successCount += 1
			print("The exit code provided here is inaccurate. Please refer to the exit codes of the child processes. ")
	elif len(argv) == 2:
		if os.path.isdir(argv[1]):
			if "WINDOWS" != PLATFORM:
				for root, dirs, files in os.walk(argv[1]):
					for folderName in dirs:
						try:
							os.chmod(os.path.join(root, folderName), 0o755)
						except:
							pass
				for fileName in files:
					for fileName in files:
						try:
							os.chmod(os.path.join(root, fileName), 0o644)
						except:
							pass
			for root, dirs, files in os.walk(argv[1]):
				for fileName in files:
					if os.path.splitext(fileName)[1].lower() == ".py" and "." != root:
						filePath = os.path.join(root, fileName)
						if not os.path.islink(filePath):
							totalCount += 1
							print(filePath)
							successCount += int(generateSchemeTxt(os.path.join(root, fileName)))
		elif os.path.isfile(argv[1]) and os.path.splitext(argv[1])[1].lower() == ".py" and os.path.abspath(os.path.dirname(argv[1])) != os.path.abspath(os.path.dirname(__file__)):
			if "WINDOWS" != PLATFORM:
				try:
					os.chmod(argv[1], 0o644)
				except:
					pass
			if not os.path.islink(argv[1]):
				totalCount += 1
				if generateSchemeTxt(argv[1]):
					successCount += 1
		else:
			print("Cannot recognize the following option as a folder or a Python file. \n\t{0}".format(argv[1]))
	else:
		for root, dirs, files in os.walk("."):
			for fileName in files:
				if os.path.splitext(fileName)[1].lower() == ".py" and "." != root:
					filePath = os.path.join(root, fileName)
					if not os.path.islink(filePath):
						totalCount += 1
						print(filePath)
						successCount += int(generateSchemeTxt(filePath))
	errorLevel = EXIT_SUCCESS if totalCount and successCount == totalCount else EXIT_FAILURE
	print("\n")
	print("Successfully handled {0} / {1} {2} with a success rate of {3:.2f}%. ".format(successCount, totalCount, "items" if successCount > 1 else "item", successCount * 100 / totalCount) if totalCount else "Nothing was handled. ")
	print("Please press the enter key to exit ({0}). ".format(errorLevel))
	try:
		input()
	except:
		print()
	return errorLevel



if "__main__" == __name__:
	exit(main())