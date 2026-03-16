import os
from sys import argv, executable, exit
from re import findall
from subprocess import run
from time import perf_counter, sleep
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
		if os.path.isfile(pythonFilePath) and not os.path.islink(pythonFilePath) and os.path.splitext(pythonFilePath)[1].lower() == ".py" and os.path.split(pythonFilePath)[1].startswith("Scheme"):
			content, folderPath, fileName = getTxt(pythonFilePath), pythonFilePath[:-3] + "LaTeX", os.path.split(pythonFilePath)[1][:-3] + ".tex"
			if content is None:
				print("Failed to read \"{0}\". ".format(pythonFilePath))
				return False
			elif handleFolder(folderPath):
				# LaTeX Generation #
				try:
					startTime = perf_counter()
					with open(os.path.join(folderPath, fileName), "w", encoding = "utf-8") as f:
						f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{amsmath,amssymb}\n\\usepackage{bm}\n\n\\begin{document}\n\n")
						className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
						printFlag, bucketCount, buffer = 0, 0, ""
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
						f.write("\\end{document}")
					endTime = perf_counter()
					generationTimeDelta = endTime - startTime
					print("The LaTeX generation for \"{0}\" finished in {1:.9f} second(s). ".format(pythonFilePath, generationTimeDelta))
					
					# LaTeX Compilation #
					try:
						startTime = perf_counter()
						result = run(("pdflatex", fileName), capture_output = True, text = True, timeout = 10, cwd = folderPath)
						endTime = perf_counter()
						compilationTimeDelta = endTime - startTime
						if EXIT_SUCCESS == result.returncode:
							print("The LaTeX compilation for \"{0}\" succeeded in {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return True
						else:
							print("The LaTeX compilation for \"{0}\" failed. The time consumption is {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return False
					except BaseException as compilationBE:
						print("The LaTeX compilation for \"{0}\" failed due to {1}. ".format(pythonFilePath, repr(compilationBE)))
						return False
				except BaseException as generationBE:
					print("The LaTeX generation for \"{0}\" failed due to {1}. ".format(pythonFilePath, repr(generationBE)))
					return False
			else:
				print("The TEX generation for \"{0}\" failed since the parent folder was not created successfully. ".format(pythonFilePath))
				return False
		else:
			print("The passed file \"{0}\" is not an expected Python file. ".format(pythonFilePath))
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
				if os.path.splitext(fileName)[1].lower() == ".py" and fileName.startswith("Scheme"):
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