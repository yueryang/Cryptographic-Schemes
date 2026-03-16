import os
from sys import argv, exit
from re import findall
from subprocess import run
from time import perf_counter
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Builder:
	__DefaultCompilationTimeout = 10
	def __init__(self:object, schemeFilePath:str) -> object:
		self.__schemeFilePath = schemeFilePath
		if isinstance(schemeFilePath, str):
			self.__targetFolderPath = os.path.splitext(self.__schemeFilePath)[0] + "LaTeX"
			self.__mainFileName = os.path.splitext(os.path.split(self.__schemeFilePath)[1])[0]
			self.__schemeLaTeXFilePath = os.path.join(self.__targetFolderPath, self.__mainFileName + ".tex")
			self.__schemePDFFilePath = os.path.join(self.__targetFolderPath, self.__mainFileName + ".pdf")
			self.__flag = 1
		else:
			self.__targetFolderPath = None
			self.__mainFileName = None
			self.__schemeLaTeXFilePath = None
			self.__schemePDFFilePath = None
			self.__flag = 0
		self.__generationResult = None
		self.__compilationResult = None
	def generate(self:object) -> None:
		if self.__flag >= 1:
			try:
				with open(self.__schemeFilePath, "rb") as f:
					binaryStrings = f.read()
				os.makedirs(self.__targetFolderPath, exist_ok = True)
				startTime = perf_counter()
				with open(self.__schemeLaTeXFilePath, "wb") as f:
					f.write(b"\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{amsmath,amssymb}\n\\usepackage{bm}\n\n\\begin{document}\n\n")
					className, functionName, schemeFlag, doubleSeparatorFlag, bucketCount, buffer = None, None, False, True, 0, ""
					for idx, line in enumerate(binaryStrings.splitlines()):
						if line.startswith(b"class Scheme"): # class SchemeXXX
							className = findall(b"^[0-9A-Za-z]+", line[6:])
							if className:
								className = className[0]
								if len(className) >= 7:
									f.write(b"\\section{" + className + b"}" + os.linesep.encode() * 2)
									functionName, schemeFlag, doubleSeparatorFlag = None, False, True
								else:
									className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
							else:
								className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True
						elif isinstance(className, bytes) and line.startswith(b"\tdef ") and b"(self:object" in line and b") -> " in line and b": # " in line: # def XXX
							functionName, schemeFlag, doubleSeparatorFlag = line[5:line.index(b"(self:object")].strip(), False, True
							if b"__init__" == functionName:
								f.write(line[line.index(b": # ") + 4:] + os.linesep.encode() * 2)
								functionName = None
							elif b"__" in functionName:
								functionName = None
							else:
								f.write(b"\\subsection{" + line[line.index(b": # ") + 4:].strip() + b"}" + os.linesep.encode() * 2)
						elif isinstance(className, bytes) and isinstance(functionName, bytes) and b"\t\t# Scheme #" == line: # XXX # Scheme # XXX
							schemeFlag, doubleSeparatorFlag = True, True
						elif isinstance(className, bytes) and isinstance(functionName, bytes) and schemeFlag and b" # " in line:
							prompt = line[line.index(b" # ") + 3:].lstrip()
							if b"$" == prompt.strip():
								doubleSeparatorFlag = not doubleSeparatorFlag # invert the double separator switch
							elif (prompt.startswith(b"$") or prompt.startswith(b"\\quad$")) and not prompt.rstrip().endswith(b"$"):
								doubleSeparatorFlag = False # disable the double separator switch
							elif not prompt.startswith(b"$") and prompt.rstrip().endswith(b"$"):
								doubleSeparatorFlag = True # enable the double separator switch
							tabCount = 0
							for tabIdx in range(0, len(prompt), 5):
								if prompt[tabIdx:].startswith(b"\\quad"):
									tabCount += 1
								else:
									break
							f.write(b"\t" * tabCount + prompt + os.linesep.encode() * (2 if doubleSeparatorFlag else 1))
							if line.startswith(b"\t\treturn "):
								functionName, schemeFlag, doubleSeparatorFlag = None, False, True
						elif (
							isinstance(className, bytes) and isinstance(functionName, bytes) and schemeFlag
							and line.lstrip().startswith(b"# ") and line.rstrip().endswith(b"\\textbf{end if}")
						):
							f.write(line.lstrip()[2:].lstrip() + os.linesep.encode() * (2 if doubleSeparatorFlag else 1))
						elif not line.startswith(b"\t") and line.strip() and not line.lstrip().startswith(b"#"): # Reset
							className, functionName, schemeFlag, doubleSeparatorFlag = None, None, False, True # reset
					f.write(b"\\end{document}")
				endTime = perf_counter()
				self.__generationResult = endTime - startTime
				self.__flag = 2
			except BaseException as e:
				self.__generationResult = e
	def compile(self:object) -> None:
		if self.__flag >= 2:
			try:
				startTime = perf_counter()
				print(self.__schemeLaTeXFilePath)
				result = run(("pdflatex", self.__mainFileName + ".tex"), capture_output = True, text = True, timeout = Builder.__DefaultCompilationTimeout, cwd = self.__targetFolderPath)
				endTime = perf_counter()
				if EXIT_SUCCESS == result.returncode:
					self.__compilationResult = endTime - startTime
					self.__flag = 3
				else:
					self.__compilationResult = result
			except BaseException as e:
				self.__compilationResult = e
	def getFlag(self:object) -> int:
		return self.__flag
	def getSchemeFilePath(self:object) -> str:
		return self.__schemeFilePath
	def getGenerationStatement(self:object) -> str:
		if self.__flag >= 2:
			return "Successfully generated the LaTeX source code for \"{0}\". The time consumption is {1:.9f} second(s). ".format(self.__schemeFilePath, self.__generationResult)
		elif self.__flag >= 1:
			if self.__generationResult is None:
				return "Please call the ``generate`` method function to generate the LaTeX source code for \"{0}\". ".format(self.__schemeFilePath)
			else:
				return "Failed to generate the LaTeX source code for \"{0}\" due to {1}. ".format(self.__schemeFilePath, repr(self.__generationResult))
		else:
			return "The scheme file path passed is not a string. "
	def getCompilationStatement(self:object) -> str:
		if self.__flag >= 3:
			return "Successfully compiled the LaTeX source code to the PDF for \"{0}\". The time consumption is {1:.9f} second(s). ".format(self.__schemeFilePath, self.__compilationResult)
		elif self.__flag >= 2:
			if self.__compilationResult is None:
				return "Please call the ``compile`` method function to compile the LaTeX source code to the PDF for \"{0}\". ".format(self.__schemeFilePath)
			else:
				return "Failed to compile the LaTeX source code to the PDF for \"{0}\" due to {1}. ".format(self.__schemeFilePath, repr(self.__compilationResult))
		elif self.__flag >= 1:
			return "Please call the ``generate`` method function before the ``compile`` method function for \"{0}\". ".format(self.__schemeFilePath)
		else:
			return "The scheme file path passed is not a string. "

class Builders:
	DefaultSchemeFilePathPrompt, DefaultGenerationPrompt, DefaultCompilationPrompt = "[F] ", "[G] ", "[C] "
	def __init__(self:object, *paths:tuple) -> object:
		self.__builders = []
		if paths:
			self.updateFilePaths(paths)
		else:
			self.updateFilePaths(".")
	def updateFilePaths(self:object, *paths:tuple) -> int:
		originalLength = len(self.__builders)
		queue, filePaths = list(paths), []
		while queue:
			if isinstance(queue[0], (tuple, list, set)):
				for path in queue[0]:
					queue.append(path)
			elif isinstance(queue[0], str):
				if os.path.isdir(queue[0]) and not os.path.islink(queue[0]):
					for root, folderNames, fileNames in os.walk(queue[0]):
						for fileName in fileNames:
							filePath = os.path.join(root, fileName)
							if os.path.isfile(filePath) and not os.path.islink(filePath) and os.path.splitext(fileName)[1] == ".py" and fileName.startswith("Scheme"):
								queue.append(filePath)
				elif os.path.isfile(queue[0]) and not os.path.islink(queue[0]):
					fileName = os.path.split(queue[0])[1]
					if os.path.splitext(fileName)[1] == ".py" and fileName.startswith("Scheme"):
						filePaths.append(os.path.relpath(queue[0]))
			del queue[0]
		for filePath in sorted(set(filePaths)):
			self.__builders.append(Builder(filePath))
		currentLength = len(self.__builders)
		return currentLength - originalLength
	def build(self:object, isSilent:bool = False) -> None:
		successCount = 0
		if isinstance(isSilent, bool) and isSilent:
			for builder in self.__builders:
				builder.generate()
				builder.compile()
				if builder.getFlag() >= 3:
					successCount += 1
		else:
			for builder in self.__builders:
				print(Builders.DefaultSchemeFilePathPrompt + builder.getSchemeFilePath())
				builder.generate()
				print(Builders.DefaultGenerationPrompt + builder.getGenerationStatement())
				builder.compile()
				print(Builders.DefaultCompilationPrompt + builder.getCompilationStatement())
				if builder.getFlag() >= 3:
					successCount += 1
				print()
		return successCount
	def __len__(self:object) -> int:
		return len(self.__builders)


def main() -> int:
	builders = Builders(*argv[1:])
	totalCount = len(builders)
	print("Gathered {0} to build. ".format(("{0} items" if totalCount > 1 else "{0} item").format(totalCount)))
	if totalCount >= 1:
		print()
		successCount = builders.build()
		errorLevel = EXIT_SUCCESS if successCount == totalCount else EXIT_FAILURE
		print()
		print("Successfully handled {0} / {1} {2} with a success rate of {3:.2f}%. ".format(successCount, totalCount, "items" if successCount > 1 else "item", successCount * 100 / totalCount))
	else:
		errorLevel = EOF
		print("Nothing was built. ")
	print("Please press the enter key to exit ({0}). ".format(errorLevel))
	try:
		input()
	except:
		print()
	print()
	return errorLevel



if "__main__" == __name__:
	exit(main())