import os
from sys import argv, exit
from getpass import getpass
try:
	from libcst import CSTNode, Call, ClassDef, ConcatenatedString, EmptyLine, FunctionDef, Name, SimpleString, TrailingWhitespace, parse_module
except:
	print("The Python `libcst` library is not installed. ")
	print("Please try to install the Python `libcst` library via `pip install libcst`. ")
	print("Please press the enter key to exit (-2). ")
	try:
		getpass("")
	except:
		print()
	exit(-2)
from subprocess import TimeoutExpired, run
from time import perf_counter, sleep
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Environments:
	__DefaultWaitingTime = float("inf")
	def __init__(self:object) -> object:
		self.__originalConsoleAttributes = None
		self.__echolessConsoleAttributes = None
		self.__tcsetattr = None
	def __parseRealNumber(self:object, string:str) -> int|float|None:
		try:
			realNumberString = "".join(ch for ch in string if ch.isalnum() or ch in "+-.").lower()
			if "e" in realNumberString and not realNumberString.endswith("e"):
				return float(realNumberString)
			else:
				minusSign = False
				while realNumberString:
					if '+' == realNumberString[0]:
						realNumberString = realNumberString[1:]
					elif '-' == realNumberString[0]:
						minusSign, realNumberString = not minusSign, realNumberString[1:]
					else:
						break
				while realNumberString.startswith("00"):
					realNumberString = realNumberString[1:]
				if realNumberString.startswith("0b"):
					base, digits, realNumberString = 2, "01", realNumberString[2:]
				elif realNumberString.startswith("0q"):
					base, digits, realNumberString = 4, "0123", realNumberString[2:]
				elif realNumberString.startswith("0o"):
					base, digits, realNumberString = 8, "01234567", realNumberString[2:]
				elif realNumberString.startswith(("0d", "0l")):
					base, digits, realNumberString = 10, "0123456789", realNumberString[2:]
				elif realNumberString.startswith(("0h", "0x")):
					base, digits, realNumberString = 16, "0123456789abcdef", realNumberString[2:]
				elif realNumberString.endswith("b"):
					base, digits, realNumberString = 2, "01", realNumberString[:-1]
				elif realNumberString.endswith("q"):
					base, digits, realNumberString = 4, "0123", realNumberString[:-1]
				elif realNumberString.endswith("o"):
					base, digits, realNumberString = 8, "01234567", realNumberString[:-1]
				elif realNumberString.endswith(("d", "l")):
					base, digits, realNumberString = 10, "0123456789", realNumberString[:-1]
				elif realNumberString.endswith(("h", "x")):
					base, digits, realNumberString = 16, "0123456789abcdef", realNumberString[:-1]
				else:
					base, digits = 10, "0123456789"
				if "inf" == realNumberString:
					realNumber = float("inf")
				elif "nan" == realNumberString:
					realNumber = float("nan")
				else:
					integerPartString, decimalPartString = realNumberString.split(".") if "." in realNumberString else (realNumberString, "")
					realNumber = 0
					for ch in reversed(decimalPartString.rstrip("0")):
						realNumber += digits.index(ch)
						realNumber /= base
					integerPartString = integerPartString.lstrip("0")
					if integerPartString:
						realNumber += int(integerPartString, base = base)
					if realNumber.is_integer():
						realNumber = int(realNumber)
				if minusSign:
					realNumber = -realNumber
				return realNumber
		except:
			return None
	def resolve(self:object) -> tuple:
		waitingTime = self.__parseRealNumber(os.getenv("WAITING_TIME"))
		return (os.getenv("FORMATTER"), waitingTime if isinstance(waitingTime, (int, float)) and waitingTime >= 0 else Environments.__DefaultWaitingTime)
	def disableConsoleEchoes(self:object) -> bool:
		if "posix" == os.name:
			try:
				if self.__originalConsoleAttributes is None:
					self.__originalConsoleAttributes = __import__("termios").tcgetattr(0)
				if self.__echolessConsoleAttributes is None:
					self.__echolessConsoleAttributes = __import__("termios").tcgetattr(0)
					self.__echolessConsoleAttributes[3] &= ~__import__("termios").ECHO
				if self.__tcsetattr is None:
					self.__tcsetattr = __import__("termios").tcsetattr
				self.__tcsetattr(0, 0, self.__echolessConsoleAttributes)
			except:
				return False
		return True
	def restoreConsoleEchoes(self:object) -> bool:
		if "posix" == os.name:
			try:
				self.__tcsetattr(0, 0, self.__originalConsoleAttributes)
			except:
				return False
		return True

class Builder:
	__DefaultCompilationTimeout = 10
	def __init__(self:object, schemeFilePath:str, pathWithoutExtensions:str) -> object:
		self.__schemeFilePath = schemeFilePath
		if isinstance(self.__schemeFilePath, str) and isinstance(pathWithoutExtensions, str):
			self.__schemeLaTeXFilePath = pathWithoutExtensions + ".tex"
			self.__targetFolderPath, self.__schemeLaTeXFileName = os.path.split(self.__schemeLaTeXFilePath)
			self.__schemePDFFilePath = pathWithoutExtensions + ".pdf"
			self.__flag = 1
		else:
			self.__schemeLaTeXFilePath = None
			self.__targetFolderPath = None
			self.__schemeLaTeXFileName = None
			self.__schemePDFFilePath = None
			self.__flag = 0
		self.__generationResult = None
		self.__compilationResult = None
	def generate(self:object) -> None:
		if self.__flag >= 1:
			try:
				startTime = perf_counter()
				with open(self.__schemeFilePath, "rb") as f:
					tree = parse_module(f.read())
				os.makedirs(self.__targetFolderPath, exist_ok = True)
				with open(self.__schemeLaTeXFilePath, "w", encoding = tree.encoding) as f:
					f.write("\\documentclass[a4paper]{article}" + os.linesep + "\\setlength{\\parindent}{0pt}" + os.linesep + "\\usepackage{amsmath,amssymb}" + os.linesep)
					f.write("\\usepackage{bm}" + os.linesep * 2 + "\\begin{document}" + os.linesep * 2)
					stack, strings, issues = [tree], [], []
					while stack:
						element = stack.pop()
						if isinstance(element, Call) and isinstance(element.func, Name) and "print" == element.func.value:
							for argument in element.args:
								if isinstance(argument.value, (ConcatenatedString, SimpleString)):
									strings.append(argument.value.evaluated_value)
						elif isinstance(element, ClassDef) and element.name.value.startswith("Scheme"): # search("^class\\s+Scheme[0-9A-Z_a-z]*", line)
							f.write("\\section{" + element.name.value.replace("_", "\\_") + "}" + os.linesep * 2)
							for item in element.body.body:
								if isinstance(item, FunctionDef):
									if "__init__" == item.name.value: # search("^\tdef\\s+__init__", line)
										if item.body.header.comment:
											f.write(item.body.header.comment.value.lstrip("# ") + os.linesep * 2)
									elif not item.name.value.startswith("_") and "getLengthOf" != item.name.value: # search("^\tdef\\s+[A-Za-z][0-9A-Z_a-z]*", line)
										f.write("\\subsection{" + item.name.value.replace("_", "\\_") + "}" + os.linesep * 2)
										s, mode = [item], False
										while s:
											ele = s.pop()
											if isinstance(ele, (EmptyLine, TrailingWhitespace)):
												if ele.comment:
													if ele.comment.value in ("# Flag #", "# Return #", "# Scheme #"):
														if False == mode:
															mode = True
													elif mode:
														comment = ele.comment.value.lstrip("# ")
														characterIndex, commentLength = 0, len(comment)
														while characterIndex < commentLength:
															if '\\' == comment[characterIndex]:
																characterIndex += 1
																if characterIndex < commentLength:
																	if comment[characterIndex] in ('(', '['):
																		if isinstance(mode, bool):
																			mode = "\\" + comment[characterIndex]
																		else:
																			raise ValueError((mode, comment, characterIndex))
																	elif ')' == comment[characterIndex]:
																		if "\\(" == mode:
																			mode = True
																		else:
																			raise ValueError((mode, comment, characterIndex))
																	elif ']' == comment[characterIndex]:
																		if "\\[" == mode:
																			mode = True
																		else:
																			raise ValueError((mode, comment, characterIndex))
																	characterIndex += 1
																else:
																	break
															elif '$' == comment[characterIndex]:
																characterIndex += 1
																dollarCount = 1
																while characterIndex < commentLength and '$' == comment[characterIndex]:
																	characterIndex += 1
																	dollarCount += 1
																if isinstance(mode, str):
																	if "$" * dollarCount == mode:
																		mode = True
																	else:
																		raise ValueError((mode, comment, characterIndex))
																else:
																	mode = "$" * dollarCount
															else:
																characterIndex += 1
														f.write(comment + os.linesep * (1 if isinstance(mode, str) else 2))
											elif isinstance(ele, CSTNode):
												s.extend(reversed(list(ele.children)))
						elif isinstance(element, CSTNode):
							stack.extend(reversed(list(element.children)))
					f.write("\\end{document}")
				endTime = perf_counter()
				self.__generationResult = endTime - startTime
				self.__flag = 2
			except BaseException as e:
				self.__generationResult = e
	def compile(self:object) -> None:
		if self.__flag >= 2:
			try:
				startTime = perf_counter()
				result = run(("pdflatex", self.__schemeLaTeXFileName), capture_output = True, text = True, timeout = Builder.__DefaultCompilationTimeout, cwd = self.__targetFolderPath)
				endTime = perf_counter()
				if EXIT_SUCCESS == result.returncode:
					self.__compilationResult = endTime - startTime
					self.__flag = 3
				else:
					self.__compilationResult = result
			except TimeoutExpired as e:
				self.__compilationResult = {"cmd":e.cmd, "stderr":e.stderr, "stdout":e.stdout, "timeout":e.timeout}
			except BaseException as e:
				self.__compilationResult = e
	def getFlag(self:object) -> int:
		return self.__flag
	def getGenerationStatement(self:object) -> str:
		if self.__flag >= 2:
			return "Successfully generated the LaTeX source code {0} for {1}. The time consumption is {2:.9f} second(s). ".format(
				repr(self.__schemeLaTeXFilePath), repr(self.__schemeFilePath), self.__generationResult
			)
		elif self.__flag >= 1:
			if self.__generationResult is None:
				return "Please call the ``generate`` method function to generate the LaTeX source code {0} for {1}. ".format(repr(self.__schemeLaTeXFilePath), repr(self.__schemeFilePath))
			else:
				return "Failed to generate the LaTeX source code {0} for {1} due to {2}. ".format(repr(self.__schemeLaTeXFilePath), repr(self.__schemeFilePath), repr(self.__generationResult))
		else:
			return "The file paths passed should be strings. "
	def getCompilationStatement(self:object) -> str:
		if self.__flag >= 3:
			return "Successfully compiled the LaTeX source code {0} to {1} for {2}. The time consumption is {3:.9f} second(s). ".format(
				repr(self.__schemeLaTeXFilePath), repr(self.__schemePDFFilePath), repr(self.__schemeFilePath), self.__compilationResult
			)
		elif self.__flag >= 2:
			if self.__compilationResult is None:
				return "Please call the ``compile`` method function to compile the LaTeX source code {0} to {1} for {2}. ".format(
					repr(self.__schemeLaTeXFilePath), repr(self.__schemePDFFilePath), repr(self.__schemeFilePath)
				)
			else:
				return "Failed to compile the LaTeX source code {0} to {1} for {2} due to {3}. ".format(
					repr(self.__schemeLaTeXFilePath), repr(self.__schemePDFFilePath), repr(self.__schemeFilePath), repr(self.__compilationResult)
				)
		elif self.__flag >= 1:
			return "Please call the ``generate`` method function before the ``compile`` method function for {0}. ".format(repr(self.__schemeFilePath))
		else:
			return "The file paths passed should be strings. "

class Builders:
	__DefaultFormatter, __DefaultSchemeFilePathPrompt, __DefaultGenerationPrompt, __DefaultCompilationPrompt = "%p%s%mLaTeX%s%m", "[F] ", "[G] ", "[C] "
	def __init__(self:object, formatter:str = __DefaultFormatter, *paths:tuple) -> object:
		self.__formatter = formatter if isinstance(formatter, str) else Builders.__DefaultFormatter
		self.__filePaths = []
		self.__builders = []
		if paths:
			self.updateFilePaths(*paths)
		else:
			self.updateFilePaths(".")
	def __format(self:object, _m:str = "", _n:str = "", _p:str = "", _s:str = os.sep, _x:str = ".py") -> str:
		m, n, p = _m if isinstance(_m, str) else "", _n if isinstance(_n, str) else "", _p if isinstance(_p, str) else ""
		s, x = _s if isinstance(_s, str) else os.sep, _x if isinstance(_x, str) else ".py"
		buffer, index, length = [], 0, len(self.__formatter)
		while index < length:
			if '%' == self.__formatter[index]:
				index += 1
				if index < length:
					if '%' == self.__formatter[index]:
						buffer.append("%")
					elif 'm' == self.__formatter[index]:
						buffer.append(m)
					elif 'n' == self.__formatter[index]:
						buffer.append(n)
					elif 'p' == self.__formatter[index]:
						buffer.append(p)
					elif 's' == self.__formatter[index]:
						buffer.append(s)
					elif 'x' == self.__formatter[index]:
						buffer.append(x)
					else:
						buffer.append("%" + self.__formatter[index])
					index += 1
				else:
					buffer.append("%")
					break
			else:
				buffer.append(self.__formatter[index])
				index += 1
		return "".join(buffer)
	def updateFilePaths(self:object, *paths:tuple) -> int:
		originalLength, stack = len(self.__builders), list(reversed(paths))
		while stack:
			element = stack.pop()
			if isinstance(element, (tuple, list)):
				stack.extend(reversed(element))
			elif isinstance(element, set):
				stack.extend(sorted(element, reverse = True))
			elif isinstance(element, str):
				if os.path.isdir(element) and not os.path.islink(element):
					filePaths = []
					for root, folderNames, fileNames in os.walk(element):
						for fileName in fileNames:
							filePath = os.path.join(root, fileName)
							if os.path.isfile(filePath) and not os.path.islink(filePath) and os.path.splitext(fileName)[1] == ".py" and fileName.startswith("Scheme"):
								filePaths.append(filePath)
					filePaths.sort(reverse = True)
					stack.extend(filePaths)
					del filePaths
				elif os.path.isfile(element) and not os.path.islink(element):
					fileName = os.path.split(element)[1]
					if os.path.splitext(fileName)[1] == ".py" and fileName.startswith("Scheme"):
						relativePath = os.path.relpath(element)
						if relativePath not in self.__filePaths:
							self.__filePaths.append(relativePath)
		for filePath in self.__filePaths[originalLength:]:
			p, n = os.path.split(filePath)
			m, x = os.path.splitext(n)
			self.__builders.append(Builder(filePath, self.__format(m, n, p, os.sep, x)))
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
			for filePath, builder in zip(self.__filePaths, self.__builders):
				print(Builders.__DefaultSchemeFilePathPrompt + filePath)
				builder.generate()
				print(Builders.__DefaultGenerationPrompt + builder.getGenerationStatement())
				builder.compile()
				print(Builders.__DefaultCompilationPrompt + builder.getCompilationStatement())
				if builder.getFlag() >= 3:
					successCount += 1
				print()
		return successCount
	def __len__(self:object) -> int:
		return len(self.__builders)


def main() -> int:
	environments = Environments()
	formatter, waitingTime = environments.resolve()
	environments.disableConsoleEchoes()
	builders = Builders(formatter, *argv[1:])
	totalCount = len(builders)
	print("Gathered {0} to build. ".format(("{0} items" if totalCount > 1 else "{0} item").format(totalCount)))
	if totalCount >= 1:
		print()
		successCount = builders.build()
		errorLevel = EXIT_SUCCESS if successCount == totalCount else EXIT_FAILURE
		print("Successfully handled {0} / {1} {2} with a success rate of {3:.2f}%. ".format(successCount, totalCount, "items" if successCount > 1 else "item", successCount * 100 / totalCount))
	else:
		errorLevel = EOF
		print("Nothing was built. ")
	if 0 == waitingTime:
		print("The execution has finished ({0}). ".format(errorLevel))
		print()
	elif isinstance(waitingTime, (float, int)) and 0 < waitingTime < float("inf"):
		integerTime, timeString = int(waitingTime), str(waitingTime)
		decimalTime = waitingTime - integerTime
		if "e" in timeString:
			timeString = str(integerTime) + ("{{0:.{0}f}}".format(decimalPlace).format(decimalTime).strip("0").rstrip(".") if decimalTime >= 10 ** (-decimalPlace) else "")
		timeStringLength = len(timeString)
		print("Please wait {0} second(s) for automatic exit, or exit manually, for example by pressing `Ctrl + C` ({1}). ".format(timeString, errorLevel))
		try:
			print("\rThe countdown is {0} second(s). ".format(timeString, errorLevel), end = "")
			sleep(decimalTime)
			while integerTime >= 1:
				print("\rThe countdown is {{0:>{0}}} second(s). ".format(timeStringLength).format(integerTime, errorLevel), end = "")
				sleep(1)
				integerTime -= 1
		except:
			pass
		print("\rThe countdown is {{0:>{0}}} second(s). ".format(timeStringLength).format(0, errorLevel))
		print("The execution has finished ({0}). ".format(errorLevel))
		print()
	else:
		print("Please press the enter key to exit ({0}). ".format(errorLevel))
		try:
			getpass("")
		except:
			print()
	environments.restoreConsoleEchoes()
	del environments
	return errorLevel



if "__main__" == __name__:
	exit(main())