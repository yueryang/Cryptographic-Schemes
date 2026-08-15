from os import chdir, makedirs, name, sep
from os.path import abspath, basename, dirname, exists, isfile, isdir, join, split, splitext
from sys import argv, exit
from codecs import lookup
from getpass import getpass
from hashlib import sha3_256
try:
	from numpy import arange, asarray, concatenate, dot, eye, fill_diagonal, kron, minimum, ndarray, triu_indices, zeros
	from numpy.linalg import lstsq
	from numpy.random import randint
	from sympy import Matrix
except:
	arange, asarray, concatenate, dot, eye, fill_diagonal, kron, minimum, ndarray, triu_indices, zeros, lstsq, randint, Matrix = (None, ) * 14
from time import perf_counter, sleep
try:
	chdir(abspath(dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
MAXIMUM_ATTEMPT_COUNT = 100


class Parser:
	__SchemeName = "SchemeFSMUAEKS" # splitext(basename(__file__))[0]
	__OptionEncoding = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
	__DefaultEncoding = "utf-8"
	__OptionHelp = ("h", "/h", "-h", "help", "/help", "--help")
	__OptionOutput = ("o", "/o", "-o", "output", "/output", "--output")
	__DefaultOutputExtension = ".xlsx"
	__DefaultOutputFileName = __SchemeName + __DefaultOutputExtension
	__ProtectedExtensionNames = ("ASM", "BAT", "C", "CMD", "CPP", "CS", "GO", "H", "HPP", "IPYNB", "JAR", "JAVA", "JS", "KT", "LUA", "M", "O", "PHP", "PS1", "PY", "R", "RB", "RS", "S", "SH", "SQL")
	__OptionPlace = ("p", "/p", "-p", "place", "/place", "--place")
	__DefaultPlace = 9
	__PlaceTranslations = {"s":0, "second":0, "ms":3, "millisecond":3, "microsecond":6, "ns":9, "nanosecond":9, "ps":12, "picosecond":12, "fs":15, "femtosecond":15}
	__OptionQuiet = ("q", "/q", "-q", "quiet", "/quiet", "--quiet")
	__OptionRun = ("r", "/r", "-r", "run", "/run", "--run")
	__DefaultRun = 10
	__OptionTime = ("t", "/t", "-t", "time", "/time", "--time")
	__DefaultTime = float("inf")
	__OptionYes = ("y", "/y", "-y", "yes", "/yes", "--yes")
	__tcgetattr = None
	__OriginalConsoleAttributes = None
	__ECHOLESSNESS = None
	__EcholessConsoleAttributes = None
	__tcsetattr = None
	@staticmethod
	def __formatOption(option:tuple|list, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, (tuple, list)) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	@staticmethod
	def __printHelp() -> None:
		print("This is the official implementation of the AA-IB-ME cryptographic scheme in Python programming language based on the Python Charm-Crypto framework. ")
		print()
		print("Options (case-insensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(
			Parser.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding
		))
		print("\t{0}\t\tPrint this help document. ".format(Parser.__formatOption(Parser.__OptionHelp)))
		print("\t{0} [|.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(
			Parser.__formatOption(Parser.__OptionOutput), Parser.__SchemeName, repr(Parser.__DefaultOutputFileName)
		))
		print("\t{0} [s|ms|microsecond|ns|ps|0|3|6|9|12|...]\t\tSpecify the decimal place, which should be a non-negative integer. The default value is {1}. ".format(
			Parser.__formatOption(Parser.__OptionPlace), Parser.__DefaultPlace
		))
		print("\t{0}\t\tDisable the verbose console outputs. ".format(Parser.__formatOption(Parser.__OptionQuiet)))
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the run count, which must be a positive integer. The default value is {1}. ".format(
			Parser.__formatOption(Parser.__OptionRun), Parser.__DefaultRun
		))
		print(
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(Parser.__formatOption(Parser.__OptionTime))
			+ "Passing inf requires users to manually press the Enter key before exiting. The default value is {0}. ".format(Parser.__DefaultTime)
		)
		print("\t{0}\t\tIndicate to confirm the overwriting of the existing output file. ".format(Parser.__formatOption(Parser.__OptionYes)))
		print()
	@staticmethod
	def __handlePath(filePath:str) -> str:
		if isinstance(filePath, str):
			if isdir(filePath) or filePath.endswith((sep, "/")):
				print("Parser: The output file path passed looks like a directory, which would be connected with the default file name {0}. ".format(repr(Parser.__DefaultOutputFileName)))
				return Parser.__handlePath(join(filePath, Parser.__DefaultOutputFileName))
			elif splitext(basename(filePath))[1][1:].upper() in Parser.__ProtectedExtensionNames:
				print((
					"Parser: The extension name of the output file path passed is one of the protected extension names, "
					+ "which would be reset to the default extension {0}. "
				).format(repr(Parser.__DefaultOutputExtension)))
				return Parser.__handlePath(splitext(filePath)[0] + Parser.__DefaultOutputExtension)
			else:
				return filePath
		else:
			return Parser.__DefaultOutputFileName
	@staticmethod
	def __parseRealNumber(string:str) -> int|float|None:
		try:
			realNumberString = "".join(character for character in string if character in "+-." or character.isalnum()).lower()
			if "x" not in realNumberString and "e" in realNumberString and not realNumberString.endswith("e"):
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
				realNumberString = realNumberString.lstrip("0")
				if realNumberString.startswith("b"):
					base, digits, realNumberString = 2, "01", realNumberString[1:]
				elif realNumberString.startswith("q"):
					base, digits, realNumberString = 4, "0123", realNumberString[1:]
				elif realNumberString.startswith("o"):
					base, digits, realNumberString = 8, "01234567", realNumberString[1:]
				elif realNumberString.startswith(("d", "l")):
					base, digits, realNumberString = 10, "0123456789", realNumberString[1:]
				elif realNumberString.startswith(("h", "x")):
					base, digits, realNumberString = 16, "0123456789abcdef", realNumberString[1:]
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
					integerPartString, decimalPartString = realNumberString.split(".")[:2] if "." in realNumberString else (realNumberString, "")
					realNumber = 0
					for character in reversed(decimalPartString.rstrip("0")):
						realNumber += digits.index(character)
						realNumber /= base
					integerPartString = integerPartString.lstrip("0")
					if integerPartString:
						realNumber += int(integerPartString, base = base)
					if isinstance(realNumber, float) and realNumber.is_integer():
						realNumber = int(realNumber)
				if minusSign:
					realNumber = -realNumber
				return realNumber
		except:
			return None
	@staticmethod
	def parse(args:tuple|list) -> tuple:
		arguments = tuple(argument for argument in args if isinstance(argument, str)) if isinstance(args, (tuple, list)) else ()
		flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed = (
			max(EXIT_SUCCESS, EOF) + 1, Parser.__DefaultEncoding, Parser.__DefaultOutputFileName, Parser.__DefaultPlace, True, Parser.__DefaultRun, Parser.__DefaultTime, False
		)
		index, argumentCount, buffers = 1, len(arguments), []
		while index < argumentCount:
			argument = arguments[index].lower()
			if argument in Parser.__OptionEncoding:
				index += 1
				if index < argumentCount:
					try:
						lookup(arguments[index])
						encoding = arguments[index]
					except:
						flag = EOF
						buffers.append("Parser: The value [0] = {1} for the encoding option is invalid. ".format(index, repr(arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the encoding option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionHelp:
				Parser.__printHelp()
				flag = EXIT_SUCCESS
				break
			elif argument in Parser.__OptionOutput:
				index += 1
				if index < argumentCount:
					outputFilePath = Parser.__handlePath(arguments[index])
				else:
					flag = EOF
					buffers.append("Parser: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionPlace:
				index += 1
				if index < argumentCount:
					decimalPlaceLower = arguments[index].lower()
					if decimalPlaceLower in Parser.__PlaceTranslations:
						decimalPlace = Parser.__PlaceTranslations[decimalPlaceLower]
					else:
						p = Parser.__parseRealNumber(arguments[index])
						if p is None:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option cannot be recognized. ".format(index, repr(arguments[index])))
						elif isinstance(p, int) and p >= 0:
							decimalPlace = p
						else:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option should be a non-negative integer. ".format(index, p))
						del p
				else:
					flag = EOF
					buffers.append("Parser: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionQuiet:
				isVerbose = False
			elif argument in Parser.__OptionRun:
				index += 1
				if index < argumentCount:
					r = Parser.__parseRealNumber(arguments[index])
					if r is None:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the run count option is invalid. ".format(index, repr(arguments[index])))
					elif isinstance(r, int) and r >= 1:
						runCount = r
					else:
						flag = EOF
						buffers.append("Parser: The value [{0}] = {1} for the run count option should be a positive integer. ".format(index, r))
					del r
				else:
					flag = EOF
					buffers.append("Parser: The value for the run count option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionTime:
				index += 1
				if index < argumentCount:
					t = Parser.__parseRealNumber(arguments[index])
					if t is None:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the waiting time option is invalid. ".format(index, repr(arguments[index])))
					elif t >= 0:
						waitingTime = t
					else:
						flag = EOF
						buffers.append("Parser: The value [{0}] = {1} for the waiting time option should be a non-negative value. ".format(index, t))
					del t
				else:
					flag = EOF
					buffers.append("Parser: The value for the waiting time option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionYes:
				overwritingConfirmed = True
			else:
				flag = EOF
				buffers.append("Parser: The option [{0}] = {1} is unknown. ".format(index, repr(arguments[index])))
			index += 1
		if EOF == flag:
			for buffer in buffers:
				print(buffer)
		return (flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed)
	@staticmethod
	def disableConsoleEchoes() -> bool:
		if "posix" == name:
			try:
				if Parser.__tcgetattr is None:
					Parser.__tcgetattr = __import__("termios").tcgetattr
				if Parser.__OriginalConsoleAttributes is None:
					Parser.__OriginalConsoleAttributes = Parser.__tcgetattr(0)
				if Parser.__ECHOLESSNESS is None:
					Parser.__ECHOLESSNESS = ~__import__("termios").ECHO
				if Parser.__EcholessConsoleAttributes is None:
					Parser.__EcholessConsoleAttributes = Parser.__tcgetattr(0)
					Parser.__EcholessConsoleAttributes[3] &= Parser.__ECHOLESSNESS
				if Parser.__tcsetattr is None:
					Parser.__tcsetattr = __import__("termios").tcsetattr
				Parser.__tcsetattr(0, 0, Parser.__EcholessConsoleAttributes)
			except:
				return False
		return True
	@staticmethod
	def checkOverwriting(outputFP:str, overwriting:bool) -> tuple:
		if isinstance(outputFP, str) and isinstance(overwriting, bool):
			outputFilePath, overwritingConfirmed, flag = outputFP, overwriting, False
			while outputFilePath and exists(outputFilePath):
				if isfile(outputFilePath):
					if not overwritingConfirmed:
						flag = True
						try:
							overwritingConfirmed = input(
								"The file {0} exists. Overwrite the file or not [yN]? ".format(repr(outputFilePath))
							).upper() in ("Y", "YES", "1", "T", "TRUE")
						except:
							print()
				else:
					flag = True
					print("Parser: The path {0} exists not to be a regular file. ".format(repr(outputFilePath)))
				if overwritingConfirmed:
					break
				else:
					flag = True
					try:
						outputFilePath = Parser.__handlePath(input("Please specify a new output file path or leave it empty for console output: "))
					except:
						print()
			if flag:
				print()
			return (outputFilePath, overwritingConfirmed)
		else:
			return (outputFP, overwriting)
	@staticmethod
	def getDefaultOutputFilePath() -> str:
		return Parser.__DefaultOutputFileName
	@staticmethod
	def getDefaultPlace() -> int:
		return Parser.__DefaultPlace
	@staticmethod
	def getDefaultEncoding() -> str:
		return Parser.__DefaultEncoding
	@staticmethod
	def getSchemeName() -> str:
		return Parser.__SchemeName
	@staticmethod
	def getProtectedExtensionNames() -> tuple:
		return Parser.__ProtectedExtensionNames
	@staticmethod
	def restoreConsoleEchoes() -> bool:
		if "posix" == name:
			try:
				Parser.__tcsetattr(0, 0, Parser.__OriginalConsoleAttributes)
				Parser.__OriginalConsoleAttributes = None
			except:
				return False
		return True

class Saver:
	def __init__(
		self:object, outputFilePath:str = Parser.getDefaultOutputFilePath(), columns:tuple|list = tuple(), decimalPlace:int = Parser.getDefaultPlace(), encoding:str = Parser.getDefaultEncoding()
	) -> object:
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else Parser.getDefaultOutputFilePath()
		self.__columns = tuple(column for column in columns if isinstance(column, str)) if isinstance(columns, (tuple, list)) else tuple()
		self.__decimalPlace = decimalPlace if isinstance(decimalPlace, int) and decimalPlace >= 0 else Parser.getDefaultPlace()
		self.__encoding = encoding if isinstance(encoding, str) else Parser.getDefaultEncoding()
		self.__directoryPath = dirname(self.__outputFilePath)
		self.__extensionName = splitext(basename(self.__outputFilePath))[1][1:].upper()
		self.__Writer = None # CSV/TSV
		self.__escapeHTML = None # HTM/HTML
		self.__dumpsJSON = None # JSON/YAML/YML
		self.__escapeTEX = None # TEX
		self.__columnsTEX = None # TEX
		self.__WorkbookXLS = None #XLS
		self.__styleXLSColumns = None # XLS
		self.__styleXLSValues = None # XLS
		self.__WorkbookXLSX = None # XLSX
		self.__alignmentXLSX = None # XLSX
		self.__fontXLSXColumns = None # XLSX
		self.__fontXLSXValues = None # XLSX
		self.__escapeXLSX = None # XLSX
		self.__escapeXML = None # XML
	def __handleDirectory(self:object) -> bool:
		if not self.__directoryPath:
			return True
		elif exists(self.__directoryPath):
			return isdir(self.__directoryPath)
		else:
			try:
				makedirs(self.__directoryPath)
				return True
			except:
				return False
	def save(self:object, results:tuple|list) -> bool:
		if isinstance(results, (tuple, list)) and all(isinstance(result, (tuple, list)) and all(r is None or isinstance(r, (bool, float, int, str)) for r in result) for result in results):
			if self.__outputFilePath:
				if self.__handleDirectory():
					flag = True
					while True: # try our best to avoid ``KeyboardInterrupt`` when writing the output file
						if flag and self.__extensionName != "TXT":
							try:
								if "CSV" == self.__extensionName:
									if self.__Writer is None:
										self.__Writer = __import__("csv").writer
									with open(self.__outputFilePath, "w", newline = "", encoding = self.__encoding) as f:
										writer = self.__Writer(f)
										writer.writerow(self.__columns)
										for result in results:
											writer.writerow("{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r for r in result)
								elif self.__extensionName in ("HTM", "HTML"):
									if self.__escapeHTML is None:
										self.__escapeHTML = (
											lambda x:str(x).replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#39;")
											.replace("<", "&lt;").replace(">", "&gt;").replace("\r\n", "<br />").replace("\n", "<br />").replace("\r", "<br />")
										)
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										f.write("<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta charset=\"{0}\" />\n".format(self.__encoding.upper()))
										f.write("\t\t<title>{0}</title>\n\t\t<style>\n".format(Parser.getSchemeName()))
										f.write("\t\t\ttable {\n\t\t\t\tfont-family: \'Times New Roman\', serif;\n\t\t\t\twidth: 80%;\n")
										f.write("\t\t\t\tmargin: 20px auto;\n\t\t\t\tborder-top: 2px solid black;\n")
										f.write("\t\t\t\tborder-bottom: 2px solid black;\n\t\t\t\tborder-collapse: collapse;\n\t\t\t}\n")
										f.write("\t\t\tth, td {\n\t\t\t\tpadding: 8px 12px;\n\t\t\t\tborder: none;\n\t\t\t\ttext-align: center;\n\t\t\t}\n")
										f.write("\t\t\tthead tr {\n\t\t\t\tborder-bottom: 1.5px solid #000;\n\t\t\t}\n")
										f.write("\t\t\tth {\n\t\t\t\tfont-weight: bold;\n\t\t\t}\n")
										f.write("\t\t\tcaption {\n\t\t\t\tfont-size: 1.5em;\n\t\t\t\tfont-weight: bold;\n")
										f.write("\t\t\t\tmargin: 10px;\n\t\t\t\tcaption-side: top;\n\t\t\t}\n")
										f.write("\t\t</style>\n\t</head>\n\t<body>\n\t\t<table>\n")
										f.write("\t\t\t<caption>{0}</caption>\n\t\t\t<thead>\n\t\t\t\t<tr>\n".format(Parser.getSchemeName()))
										for column in self.__columns:
											f.write("\t\t\t\t\t<th>{0}</th>\n".format(self.__escapeHTML(column)))
										f.write("\t\t\t\t</tr>\n\t\t\t</thead>\n\t\t\t<tbody>\n")
										for result in results:
											f.write("\t\t\t\t<tr>\n")
											for r in result:
												f.write("\t\t\t\t\t<td>{0}</td>\n".format(
													"{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else self.__escapeHTML(r)
												))
											f.write("\t\t\t\t</tr>\n")
										f.write("\t\t\t</tbody>\n\t\t</table>\n\t</body>\n</html>")
								elif "JSON" == self.__extensionName:
									if self.__dumpsJSON is None:
										self.__dumpsJSON = __import__("json").dumps
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										f.write(self.__dumpsJSON({"columns":self.__columns, "results":results}, indent = "\t", sort_keys = True, ensure_ascii = True))
								elif "TEX" == self.__extensionName:
									if self.__escapeTEX is None:
										self.__escapeTEX = lambda x:"\\textbackslash{}".join(
											string.replace("#", "\\#").replace("$", "\\$").replace("%", "\\%").replace("&", "\\&")
											.replace("_", "\\_").replace("{", "\\{").replace("}", "\\}")
											.replace("<", "\\textless{}").replace(">", "\\textgreater{}")
											.replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")
											for string in "".join(character for character in str(x) if ' ' <= character <= '~').split("\\")
										)
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										maxLength = max(
											len(self.__columnsTEX) if isinstance(self.__columnsTEX, (tuple, list)) else 0, 
											max(len(result) for result in results)
										)
										f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n")
										f.write("\\usepackage{graphicx}\n\\usepackage{textcomp}\n\\usepackage{booktabs}\n\\usepackage{rotating}\n\n")
										f.write("\\begin{document}\n\n\\begin{sidewaystable}\n\t\\caption{The comparison results. }\n")
										f.write("\t\\label{tab:comparison}\n\t\\centering\n\t\\resizebox{\\textwidth}{!}{%\n\t\t\\begin{tabular}{")
										f.write("c" * maxLength + "}\n\t\t\t\\toprule\n\t\t\t\t")
										if self.__columns:
											f.write(" & ".join("\\textbf{{{0}}}".format(self.__escapeTEX(column)) for column in self.__columns))
											if len(self.__columns) < maxLength:
												f.write(" & \\textbf{~}" * (maxLength - len(self.__columns)))
										else:
											f.write(" & ".join(("\\textbf{~}", ) * maxLength))
										f.write(" \\\\\n\t\t\t\\midrule\n")
										for result in results:
											if result:
												f.write("\t\t\t\t")
												f.write(" & ".join((
													"${0}$" if isinstance(r, int) else "${{0:.{0}f}}$".format(self.__decimalPlace)
												).format(r) if isinstance(r, (float, int)) and not isinstance(r, bool) else self.__escapeTEX(r) for r in result))
												if len(result) < maxLength:
													f.write(" & ~" * (maxLength - len(result)))
												f.write(" \\\\\n")
										f.write("\t\t\t\\bottomrule\n\t\t\\end{tabular}\n\t}\n")
										f.write("\\end{sidewaystable}\n\n\\end{document}")
								elif "TSV" == self.__extensionName:
									if self.__Writer is None:
										self.__Writer = __import__("csv").writer
									with open(self.__outputFilePath, "w", newline = "", encoding = self.__encoding) as f:
										writer = self.__Writer(f, delimiter = '\t')
										writer.writerow(self.__columns)
										for result in results:
											writer.writerow("{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r for r in result)
								elif "XLS" == self.__extensionName:
									if self.__WorkbookXLS is None:
										self.__WorkbookXLS = __import__("xlwt").Workbook
									if self.__styleXLSColumns is None:
										self.__styleXLSColumns = __import__("xlwt").XFStyle()
										self.__styleXLSColumns.font = __import__("xlwt").Font()
										self.__styleXLSColumns.font.name = "Times New Roman"
										self.__styleXLSColumns.font.height = 240 # 12 * 20
										self.__styleXLSColumns.font.bold = True
										self.__styleXLSColumns.alignment = __import__("xlwt").Alignment()
										self.__styleXLSColumns.alignment.horz = __import__("xlwt").Alignment.HORZ_CENTER
										self.__styleXLSColumns.alignment.vert = __import__("xlwt").Alignment.VERT_CENTER
									if self.__styleXLSValues is None:
										self.__styleXLSValues = __import__("xlwt").XFStyle()
										self.__styleXLSValues.font = __import__("xlwt").Font()
										self.__styleXLSValues.font.name = "Times New Roman"
										self.__styleXLSValues.font.height = 240 # 12 * 20
										self.__styleXLSValues.alignment = __import__("xlwt").Alignment()
										self.__styleXLSValues.alignment.horz = __import__("xlwt").Alignment.HORZ_CENTER
										self.__styleXLSValues.alignment.vert = __import__("xlwt").Alignment.VERT_CENTER
									workbook = self.__WorkbookXLS(encoding = self.__encoding)
									worksheet = workbook.add_sheet(Parser.getSchemeName())
									for columnIndex, columnName in enumerate(self.__columns):
										worksheet.write(0, columnIndex, columnName, self.__styleXLSColumns)
									for i, result in enumerate(results, start = 1):
										for j, r in enumerate(result):
											worksheet.write(
												i, j, "{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r, self.__styleXLSValues
											)
									workbook.save(self.__outputFilePath)
								elif "XLSX" == self.__extensionName:
									if self.__WorkbookXLSX is None:
										self.__WorkbookXLSX = __import__("openpyxl").Workbook
									if self.__alignmentXLSX is None:
										self.__alignmentXLSX = __import__("openpyxl").styles.Alignment(horizontal = "center", vertical = "center")
									if self.__fontXLSXColumns is None:
										self.__fontXLSXColumns = __import__("openpyxl").styles.Font(name = "Times New Roman", size = 12, bold = True)
									if self.__fontXLSXValues is None:
										self.__fontXLSXValues = __import__("openpyxl").styles.Font(name = "Times New Roman", size = 12)
									if self.__escapeXLSX is None:
										self.__escapeXLSX = lambda x:"".join(character for character in str(x) if character in ("\t", "\n", "\r") or character > ' ')
									workbook = self.__WorkbookXLSX()
									worksheet = workbook.active
									for columnIndex, columnName in enumerate(self.__columns, start = 1):
										cell = worksheet.cell(row = 1, column = columnIndex, value = self.__escapeXLSX(columnName))
										cell.alignment = self.__alignmentXLSX
										cell.font = self.__fontXLSXColumns
									for i, result in enumerate(results, start = 2):
										for j, r in enumerate(result, start = 1):
											if isinstance(r, float):
												cell = worksheet.cell(row = i, column = j, value = "{{0:.{0}f}}".format(self.__decimalPlace).format(r))
											elif isinstance(r, str):
												cell = worksheet.cell(row = i, column = j, value = self.__escapeXLSX(r))
											else:
												cell = worksheet.cell(row = i, column = j, value = r)
											cell.alignment = self.__alignmentXLSX
											cell.font = self.__fontXLSXValues
									worksheet.freeze_panes = "A2"
									workbook.save(self.__outputFilePath)
								elif "XML" == self.__extensionName:
									if self.__escapeXML is None:
										self.__escapeXML = (
											lambda x:"".join(character for character in str(x) if ' ' <= character <= '~')
											.replace("&", "&amp;").replace("\"", "&quot;").replace("\'", "&apos;").replace("<", "&lt;").replace(">", "&gt;")
										)
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										f.write("<?xml version=\"1.0\" encoding=\"{0}\"?>\n<data>\n\t<columns>\n".format(self.__encoding.upper()))
										for column in self.__columns:
											f.write("\t\t<column>" + self.__escapeXML(column) + "</column>\n")
										f.write("\t</columns>\n\t<results>\n")
										for result in results:
											f.write("\t\t<result>\n")
											for rIndex, r in enumerate(result):
												if isinstance(r, float):
													f.write("\t\t\t<r>{{0:.{0}f}}</r>\n".format(self.__decimalPlace).format(r))
												else:
													f.write("\t\t\t<r>{0}</r>\n".format(self.__escapeXML(str(r))))
											f.write("\t\t</result>\n")
										f.write("\t</results>\n</data>")
								elif self.__extensionName in ("YAML", "YML"):
									if self.__dumpsJSON is None:
										self.__dumpsJSON = __import__("json").dumps
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										if self.__columns:
											f.write("columns:\n")
											for column in self.__columns:
												f.write("  - {0}\n".format(self.__dumpsJSON(column, indent = "\t", sort_keys = True, ensure_ascii = True)))
										else:
											f.write("columns: []")
										f.write("\n")
										if results:
											f.write("results:\n")
											for result in results:
												if result:
													f.write("  - - {0}\n".format(
														self.__dumpsJSON(result[0], indent = "\t", sort_keys = True, ensure_ascii = True)
													))
													for r in result[1:]:
														f.write("    - {0}\n".format(
															self.__dumpsJSON(r, indent = "\t", sort_keys = True, ensure_ascii = True)
														))
												else:
													f.write("  - []")
										else:
											f.write("results: []")
								elif self.__extensionName in Parser.getProtectedExtensionNames():
									print("Saver: Failed to save the results to {0} since {1} is one of the protected extension names. ".format(
										repr(self.__outputFilePath), self.__extensionName
									))
									print("Saver: {0}".format({"columns":self.__columns, "results":results}))
									return False
								else:
									raise Exception("The {0} format is not supported. ".format(self.__extensionName))
								print("Saver: Successfully saved the results to {0} in the {1} format. ".format(repr(self.__outputFilePath), self.__extensionName))
								return True
							except KeyboardInterrupt:
								continue
							except BaseException as e:
								flag = False
								print("Saver: Failed to save the results to {0} in the {1} format due to the following exception(s). \n\t{2}".format(
									repr(self.__outputFilePath), self.__extensionName, repr(e)
								))
						else:
							try:
								with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
									f.write(str({"columns":self.__columns, "results":results}))
								print("Saver: Successfully saved the results to {0} in the TXT format. ".format(repr(self.__outputFilePath)))
								return True
							except KeyboardInterrupt:
								continue
							except BaseException as e:
								if flag:
									print("Saver: Failed to save the results to {0} due to the following exception(s). \n\t{1}".format(
										repr(self.__outputFilePath), repr(e)
									))
								else:
									print("\t{0}".format(e))
								print("Saver: {0}".format({"columns":self.__columns, "results":results}))
								return False
				else:
					print("Saver: Failed to initialize the directory for the output file path {0}. ".format(repr(self.__outputFilePath)))
					print("Saver: {0}".format({"columns":self.__columns, "results":results}))
					return False
			else:
				print("Saver: {0}".format({"columns":self.__columns, "results":results}))
				return True
		else:
			print("Saver: The results are invalid. ")
			return False

class SchemeFSMUAEKS:
	__DefaultN, __DefaultM, __DefaultQ, __DefaultLS, __DefaultLR = 2, 8, 16, 2, 2
	def __init__(self:object) -> object:
		self.__n, self.__m, self.__q, self.__lS, self.__lR = (None, ) * 5
		self.__B, self.__pkS, self.__skS, self.__pkR, self.__skR = (None, ) * 5
		self.__Ft, self.__cipherText, self.__trapdoor = (None, ) * 3
	def __requireSetup(self:object) -> None:
		if not all(isinstance(value, int) for value in (self.__n, self.__m, self.__q, self.__lS, self.__lR)):
			raise RuntimeError("The scheme has not been set up. ")
	def __H1(self:object, message:ndarray, m:int) -> ndarray:
		hashValue = sha3_256(message.tobytes()).digest()
		hashString = "".join(format(byte, "08b") for byte in hashValue)
		hashList = [int(bit) for bit in hashString][:(m * (m - 1)) >> 1]
		hashList += [0] * (((m * (m - 1)) >> 1) - len(hashList))
		hashArray = eye(m, dtype = "int")
		hashArray[triu_indices(m, k = 1)] = hashList
		return hashArray
	def __TrapGen(self:object) -> tuple:
		self.__requireSetup()
		n, m, q = self.__n, self.__m, self.__q
		g = (1 << arange(0, m // (n << 1))).reshape((1, m // (n << 1)))
		G = kron(eye(n, dtype = "int"), g) % q
		B = randint(q, size = (n, m >> 1))
		R = randint(2, size = (m >> 1, m >> 1))
		A0i = concatenate((B, (dot(B, R) % q + G) % q), axis = 1)
		Tg = zeros((m // (n << 1), m // (n << 1)), dtype = "int")
		fill_diagonal(Tg, 2)
		fill_diagonal(Tg[1:], -1)
		TG = kron(eye(n, dtype = "int"), Tg) % q
		GTranspose = G.T
		TAa = concatenate(((eye(m >> 1, dtype = "int") + dot(dot(R, GTranspose) % q, B) % q) % q, dot(-R, TG) % q), axis = 1)
		TAb = concatenate((dot((-GTranspose) % q, B) % q, TG), axis = 1)
		return (A0i, concatenate((TAa, TAb), axis = 0))
	def __ExtBasis(self:object, FB0:ndarray, TB0:ndarray, B0:ndarray, q:int) -> ndarray:
		W = lstsq(B0, FB0, rcond = None)[0].astype("int") % q
		return concatenate((
			concatenate((TB0, W), axis = 1),
			concatenate((zeros((W.shape[1], TB0.shape[1]), dtype = "int"), eye(W.shape[1], dtype = "int")), axis = 1)
		), axis = 0)
	def __SampleLeft(self:object, A:ndarray, C_u:ndarray, q:int) -> ndarray:
		ES = zeros((A.shape[1], C_u.shape[1]), dtype = "int")
		for column in range(C_u.shape[1]):
			ES[:, column] = lstsq(A, C_u[:, column], rcond = None)[0].astype("int") % q
		return ES
	def __hashMatrix(self:object, pkS:tuple, pkR:tuple, value:ndarray) -> ndarray:
		message = concatenate((*pkS, *pkR, value), axis = 1)
		return asarray(Matrix(self.__H1(message, self.__m)).inv()).astype("int") % self.__q
	def Setup(self:object, n:int = __DefaultN, m:int = __DefaultM, q:int = __DefaultQ, lS:int = __DefaultLS, lR:int = __DefaultLR) -> tuple: # $\textbf{Setup}(n, m, q, \ell_S, \ell_R) \to \textit{pp}$
		if not all(isinstance(value, int) and value >= 1 for value in (n, m, lS, lR)) or not isinstance(q, int) or q <= 1:
			raise ValueError("The parameters n, m, q, lS, and lR must be positive integers, and q must be greater than one. ")
		if m % (n << 1):
			raise ValueError("The parameters n and m must satisfy 2n | m. ")

		# Scheme #
		self.__n, self.__m, self.__q, self.__lS, self.__lR = n, m, q, lS, lR # $(n, m, q, \ell_S, \ell_R) \gets (n, m, q, \ell_S, \ell_R)$
		self.__B = randint(q, size = (6, n, m)) # generate $\bm{B}_0, \bm{B}_1, \ldots, \bm{B}_5 \in \mathbb{Z}_q^{n \times m}$ uniformly at random
		self.__pkS, self.__skS, self.__pkR, self.__skR = (None, ) * 4 # $(\textit{pk}_S, \textit{sk}_S, \textit{pk}_R, \textit{sk}_R) \gets (\perp, \perp, \perp, \perp)$
		self.__Ft, self.__cipherText, self.__trapdoor = (None, ) * 3 # $(\bm{F}_t, \textit{CT}, \textit{td}) \gets (\perp, \perp, \perp)$

		# Return #
		return (n, m, q, lS, lR, self.__B) # $\textbf{return}\ \textit{pp} \gets (n, m, q, \ell_S, \ell_R, (\bm{B}_i)_{i = 0}^{5})$
	def KeyGenS(self:object) -> tuple: # $\textbf{KeyGenS}(\textit{pp}) \to (\textit{pk}_S, \textit{sk}_S)$
		self.__requireSetup()

		# Scheme #
		A, TA = self.__TrapGen() # $(\bm{A}, \bm{T}_A) \gets \textbf{TrapGen}(n, m, q)$
		US = randint(self.__q, size = (self.__n, self.__n)) # generate $\bm{U}_S \in \mathbb{Z}_q^{n \times n}$ uniformly at random
		DA = randint(self.__q, size = (self.__n, self.__m)) # generate $\bm{D}_A \in \mathbb{Z}_q^{n \times m}$ uniformly at random
		AW = randint(self.__q, size = (self.__n, self.__m)) # generate $\bm{A}_W \in \mathbb{Z}_q^{n \times m}$ uniformly at random
		self.__pkS, self.__skS = (A, US, DA, AW), TA # $(\textit{pk}_S, \textit{sk}_S) \gets ((\bm{A}, \bm{U}_S, \bm{D}_A, \bm{A}_W), \bm{T}_A)$

		# Return #
		return (self.__pkS, self.__skS) # $\textbf{return}\ (\textit{pk}_S, \textit{sk}_S)$
	def KeyGenR(self:object) -> tuple: # $\textbf{KeyGenR}(\textit{pp}) \to (\textit{pk}_R, \textit{sk}_R)$
		self.__requireSetup()

		# Scheme #
		B0, TB0 = self.__TrapGen() # $(\bm{B}_0', \bm{T}_{B_0'}) \gets \textbf{TrapGen}(n, m, q)$
		UR = randint(self.__q, size = (self.__n, self.__n)) # generate $\bm{U}_R \in \mathbb{Z}_q^{n \times n}$ uniformly at random
		DB = randint(self.__q, size = (self.__n, self.__m)) # generate $\bm{D}_B \in \mathbb{Z}_q^{n \times m}$ uniformly at random
		BW = randint(self.__q, size = (self.__n, self.__m)) # generate $\bm{B}_W \in \mathbb{Z}_q^{n \times m}$ uniformly at random
		self.__pkR, self.__skR = (B0, UR, DB, BW), TB0 # $(\textit{pk}_R, \textit{sk}_R) \gets ((\bm{B}_0', \bm{U}_R, \bm{D}_B, \bm{B}_W), \bm{T}_{B_0'})$

		# Return #
		return (self.__pkR, self.__skR) # $\textbf{return}\ (\textit{pk}_R, \textit{sk}_R)$
	def KeyUpdate(self:object) -> tuple: # $\textbf{KeyUpdate}(\textit{pp}, \textit{pk}_R, \textit{sk}_R) \to (\textit{fsk}_t, \bm{F}_t)$
		self.__requireSetup()
		if self.__pkR is None or self.__skR is None:
			raise RuntimeError("The receiver keys have not been generated. ")

		# Scheme #
		B0, B, q = self.__pkR[0], self.__B, self.__q # $(\bm{B}_0', (\bm{B}_i)_{i = 0}^{5}, q) \gets (\textit{pk}_R[0], \textit{pp}.\bm{B}, \textit{pp}.q)$
		F001 = concatenate((B0, B[0], B[2], B[5]), axis = 1) # $\bm{F}_{001} \gets [\bm{B}_0' \mid \bm{B}_0 \mid \bm{B}_2 \mid \bm{B}_5]$
		F01 = concatenate((B0, B[0], B[3]), axis = 1) # $\bm{F}_{01} \gets [\bm{B}_0' \mid \bm{B}_0 \mid \bm{B}_3]$
		F1 = concatenate((B0, B[1]), axis = 1) # $\bm{F}_{1} \gets [\bm{B}_0' \mid \bm{B}_1]$
		F011 = concatenate((B0, B[0], B[3], B[5]), axis = 1) # $\bm{F}_{011} \gets [\bm{B}_0' \mid \bm{B}_0 \mid \bm{B}_3 \mid \bm{B}_5]$
		F101 = concatenate((B0, B[1], B[2], B[5]), axis = 1) # $\bm{F}_{101} \gets [\bm{B}_0' \mid \bm{B}_1 \mid \bm{B}_2 \mid \bm{B}_5]$
		F11 = concatenate((B0, B[1], B[3]), axis = 1) # $\bm{F}_{11} \gets [\bm{B}_0' \mid \bm{B}_1 \mid \bm{B}_3]$
		F111 = concatenate((B0, B[1], B[3], B[5]), axis = 1) # $\bm{F}_{111} \gets [\bm{B}_0' \mid \bm{B}_1 \mid \bm{B}_3 \mid \bm{B}_5]$
		F = (F001, F01, F1, F011, F101, F11, F111) # $\mathcal{F} \gets (\bm{F}_{001}, \bm{F}_{01}, \bm{F}_{1}, \bm{F}_{011}, \bm{F}_{101}, \bm{F}_{11}, \bm{F}_{111})$
		T001 = self.__ExtBasis(F001, self.__skR, B0, q) # $\bm{T}_{001} \gets \textbf{ExtBasis}(\bm{F}_{001}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T01 = self.__ExtBasis(F01, self.__skR, B0, q) # $\bm{T}_{01} \gets \textbf{ExtBasis}(\bm{F}_{01}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T1 = self.__ExtBasis(F1, self.__skR, B0, q) # $\bm{T}_{1} \gets \textbf{ExtBasis}(\bm{F}_{1}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T011 = self.__ExtBasis(F011, self.__skR, B0, q) # $\bm{T}_{011} \gets \textbf{ExtBasis}(\bm{F}_{011}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T101 = self.__ExtBasis(F101, self.__skR, B0, q) # $\bm{T}_{101} \gets \textbf{ExtBasis}(\bm{F}_{101}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T11 = self.__ExtBasis(F11, self.__skR, B0, q) # $\bm{T}_{11} \gets \textbf{ExtBasis}(\bm{F}_{11}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		T111 = self.__ExtBasis(F111, self.__skR, B0, q) # $\bm{T}_{111} \gets \textbf{ExtBasis}(\bm{F}_{111}, \bm{T}_{B_0'}, \bm{B}_0', q)$
		forwardSecretKeys = ((T001, T01, T1), (T01, T1), (T011, T1), (T1, ), (T101, T11), (T11, ), (T111, )) # $(\textit{fsk}_{001}, \textit{fsk}_{01}, \textit{fsk}_{1}, \textit{fsk}_{011}, \textit{fsk}_{101}, \textit{fsk}_{11}, \textit{fsk}_{111}) \gets ((\bm{T}_{001}, \bm{T}_{01}, \bm{T}_{1}), (\bm{T}_{01}, \bm{T}_{1}), (\bm{T}_{011}, \bm{T}_{1}), (\bm{T}_{1}), (\bm{T}_{101}, \bm{T}_{11}), (\bm{T}_{11}), (\bm{T}_{111}))$
		index = randint(len(F)) # generate $t \in \{001, 01, 1, 011, 101, 11, 111\}$ uniformly at random
		self.__Ft = F[index] # $\bm{F}_t \gets \mathcal{F}[t]$

		# Return #
		return (forwardSecretKeys[index], self.__Ft) # $\textbf{return}\ (\textit{fsk}_t, \bm{F}_t)$
	def Encryption(self:object) -> tuple: # $\textbf{Encryption}(\textit{pp}, \textit{pk}_S, \textit{pk}_R, \bm{F}_t) \to \textit{CT}$
		self.__requireSetup()
		if any(value is None for value in (self.__pkS, self.__skS, self.__pkR, self.__Ft)):
			raise RuntimeError("The sender keys, receiver keys, and forward key must be generated before encryption. ")

		# Scheme #
		n, m, q, lS = self.__n, self.__m, self.__q, self.__lS # $(n, m, q, \ell_S) \gets \textit{pp}.(n, m, q, \ell_S)$
		A, US, DA, AW = self.__pkS # $(\bm{A}, \bm{U}_S, \bm{D}_A, \bm{A}_W) \gets \textit{pk}_S$
		DB, BW = self.__pkR[2], self.__pkR[3] # $(\bm{D}_B, \bm{B}_W) \gets (\textit{pk}_R[2], \textit{pk}_R[3])$
		EW, SS, ck = randint(q, size = (m, lS)), randint(q, size = (n, lS)), randint(q, size = (n, 1)) # generate $\bm{E}_W \in \mathbb{Z}_q^{m \times \ell_S}$, $\bm{S}_S \in \mathbb{Z}_q^{n \times \ell_S}$, and $\textit{ck} \in \mathbb{Z}_q^{n \times 1}$ uniformly at random
		hashMatrix = self.__hashMatrix(self.__pkS, self.__pkR, ck) # $\bm{H}_{\textit{ck}} \gets H_1(\textit{pk}_S \Vert \textit{pk}_R \Vert \textit{ck})^{-1} \bmod q$
		Cw = (EW + dot((dot(AW, hashMatrix) % q).T, SS) % q) % q # $\bm{C}_w \gets \bm{E}_W + (\bm{A}_W \bm{H}_{\textit{ck}})^{\mathsf{T}} \bm{S}_S \bmod q$
		RA = (randint(2, size = (m, m)) << 1) - 1 # generate $\bm{R}_A \in \{-1, 1\}^{m \times m}$ uniformly at random
		RC = (randint(2, size = (m, m)) << 1) - 1 # generate $\bm{R}_C \in \{-1, 1\}^{m \times m}$ uniformly at random
		Ca = (dot(A.T, SS) % q + dot(RA, EW) % q) % q # $\bm{C}_a \gets \bm{A}^{\mathsf{T}} \bm{S}_S + \bm{R}_A \bm{E}_W \bmod q$
		Cc = (dot(DA.T, SS) % q + dot(RC, EW) % q) % q # $\bm{C}_c \gets \bm{D}_A^{\mathsf{T}} \bm{S}_S + \bm{R}_C \bm{E}_W \bmod q$
		RB = (randint(2, size = (self.__Ft.shape[1], m)) << 1) - 1 # generate $\bm{R}_B \in \{-1, 1\}^{\operatorname{cols}(\bm{F}_t) \times m}$ uniformly at random
		EU = randint(q, size = (n, lS)) # generate $\bm{E}_U \in \mathbb{Z}_q^{n \times \ell_S}$ uniformly at random
		Cb = (dot(self.__Ft.T, SS) % q + dot(RB, EW) % q) % q # $\bm{C}_b \gets \bm{F}_t^{\mathsf{T}} \bm{S}_S + \bm{R}_B \bm{E}_W \bmod q$
		Cu = (dot(US, SS) % q + EU) % q # $\bm{C}_u \gets \bm{U}_S \bm{S}_S + \bm{E}_U \bmod q$
		ES = self.__SampleLeft(A, Cu, q) # $\bm{E}_S \gets \textbf{SampleLeft}(\bm{A}, \bm{C}_u, q)$ such that $\bm{A}\bm{E}_S = \bm{C}_u \bmod q$
		self.__cipherText = (Cw, Ca, Cb, Cc, ES) # $\textit{CT} \gets (\bm{C}_w, \bm{C}_a, \bm{C}_b, \bm{C}_c, \bm{E}_S)$

		# Return #
		return self.__cipherText # $\textbf{return}\ \textit{CT}$
	def Trapdoor(self:object) -> tuple: # $\textbf{Trapdoor}(\textit{pp}, \textit{pk}_S, \textit{pk}_R, \textit{sk}_R, \bm{F}_t) \to \textit{td}$
		self.__requireSetup()
		if any(value is None for value in (self.__pkS, self.__pkR, self.__skR, self.__Ft)):
			raise RuntimeError("The sender keys, receiver keys, and forward key must be generated before trapdoor generation. ")

		# Scheme #
		n, m, q, lR = self.__n, self.__m, self.__q, self.__lR # $(n, m, q, \ell_R) \gets \textit{pp}.(n, m, q, \ell_R)$
		A, US, DA, AW = self.__pkS # $(\bm{A}, \bm{U}_S, \bm{D}_A, \bm{A}_W) \gets \textit{pk}_S$
		DB, BW = self.__pkR[2], self.__pkR[3] # $(\bm{D}_B, \bm{B}_W) \gets (\textit{pk}_R[2], \textit{pk}_R[3])$
		SR, EDoubleW, tk = randint(q, size = (n, lR)), randint(q, size = (m, lR)), randint(q, size = (n, 1)) # generate $\bm{S}_R \in \mathbb{Z}_q^{n \times \ell_R}$, $\bm{E}'_W \in \mathbb{Z}_q^{m \times \ell_R}$, and $\textit{tk} \in \mathbb{Z}_q^{n \times 1}$ uniformly at random
		hashMatrix = self.__hashMatrix(self.__pkS, self.__pkR, tk) # $\bm{H}_{\textit{tk}} \gets H_1(\textit{pk}_S \Vert \textit{pk}_R \Vert \textit{tk})^{-1} \bmod q$
		Tw = (EDoubleW + dot((dot(BW, hashMatrix) % q).T, SR) % q) % q # $\bm{T}_w \gets \bm{E}'_W + (\bm{B}_W \bm{H}_{\textit{tk}})^{\mathsf{T}} \bm{S}_R \bmod q$
		RDoubleA = (randint(2, size = (m, m)) << 1) - 1 # generate $\bm{R}'_A \in \{-1, 1\}^{m \times m}$ uniformly at random
		RDoubleB = (randint(2, size = (self.__Ft.shape[1], m)) << 1) - 1 # generate $\bm{R}'_B \in \{-1, 1\}^{\operatorname{cols}(\bm{F}_t) \times m}$ uniformly at random
		RDoubleC = (randint(2, size = (m, m)) << 1) - 1 # generate $\bm{R}'_C \in \{-1, 1\}^{m \times m}$ uniformly at random
		Ta = (dot(A.T, SR) % q + dot(RDoubleA, EDoubleW) % q) % q # $\bm{T}_a \gets \bm{A}^{\mathsf{T}} \bm{S}_R + \bm{R}'_A \bm{E}'_W \bmod q$
		Tb = (dot(self.__Ft.T, SR) % q + dot(RDoubleB, EDoubleW) % q) % q # $\bm{T}_b \gets \bm{F}_t^{\mathsf{T}} \bm{S}_R + \bm{R}'_B \bm{E}'_W \bmod q$
		Tc = (dot(DB.T, SR) % q + dot(RDoubleC, EDoubleW) % q) % q # $\bm{T}_c \gets \bm{D}_B^{\mathsf{T}} \bm{S}_R + \bm{R}'_C \bm{E}'_W \bmod q$
		EDoubleU = randint(q, size = (n, lR)) # generate $\bm{E}'_U \in \mathbb{Z}_q^{n \times \ell_R}$ uniformly at random
		Tu = (dot(US, SR) % q + EDoubleU) % q # $\bm{T}_u \gets \bm{U}_S \bm{S}_R + \bm{E}'_U \bmod q$
		ER = self.__SampleLeft(self.__Ft, Tu, q) # $\bm{E}_R \gets \textbf{SampleLeft}(\bm{F}_t, \bm{T}_u, q)$ such that $\bm{F}_t\bm{E}_R = \bm{T}_u \bmod q$
		self.__trapdoor = (Tw, Ta, Tb, Tc, ER) # $\textit{td} \gets (\bm{T}_w, \bm{T}_a, \bm{T}_b, \bm{T}_c, \bm{E}_R)$

		# Return #
		return self.__trapdoor # $\textbf{return}\ \textit{td}$
	def Test(self:object) -> bool: # $\textbf{Test}(\textit{pp}, \textit{CT}, \textit{td}) \to y,\ y \in \{0, 1\}$
		self.__requireSetup()

		# Scheme #
		if self.__cipherText is None or self.__trapdoor is None: # $\textbf{if}\ \textit{CT} = \perp \lor \textit{td} = \perp\ \textbf{then}$
			return False # $\quad \textbf{return}\ 0$
		# $\textbf{end if}$
		Cb, ES = self.__cipherText[2], self.__cipherText[4] # $(\bm{C}_b, \bm{E}_S) \gets (\textit{CT}[2], \textit{CT}[4])$
		Ta, ER = self.__trapdoor[1], self.__trapdoor[4] # $(\bm{T}_a, \bm{E}_R) \gets (\textit{td}[1], \textit{td}[4])$
		value = (dot(ER.T, Cb) % self.__q - dot(Ta.T, ES) % self.__q) % self.__q # $\bm{V} \gets \bm{E}_R^{\mathsf{T}}\bm{C}_b - \bm{T}_a^{\mathsf{T}}\bm{E}_S \bmod q$
		centeredValue = minimum(value, self.__q - value) # $\overline{\bm{V}} \gets \min(\bm{V}, q - \bm{V})$ component-wise

		# Return #
		return bool((centeredValue < self.__q >> 2).all()) # $\textbf{return}\ \bigwedge_{i,j} [\overline{V}_{i,j} < \lfloor q / 4 \rfloor]$
	def getLengthOf(self:object, obj:object) -> int|str:
		if isinstance(obj, ndarray):
			return int(obj.nbytes)
		elif isinstance(obj, bool):
			return 1
		elif isinstance(obj, int):
			return max(1, (abs(obj).bit_length() + 7) >> 3)
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, str):
			return len(obj.encode())
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(value) for value in obj)
			return sum(sizes) if all(isinstance(size, int) and size >= 0 for size in sizes) else "N/A"
		elif isinstance(obj, dict):
			sizes = tuple(self.getLengthOf(value) for value in obj.values())
			return sum(sizes) if all(isinstance(size, int) and size >= 0 for size in sizes) else "N/A"
		else:
			return "N/A"


def __conductScheme(parameter:tuple|list|dict, run:int|None = None, isVerbose:bool = False) -> tuple:
	nString, mString, qString, lSString, lRString, runString = ("N/A", ) * 6
	isSystemValid, isSchemeCorrect, isCompleted = (False, ) * 3
	timeSetup, timeKeyGenS, timeKeyGenR, timeKeyUpdate, timeEncryption, timeTrapdoor, timeTest = ("N/A", ) * 7
	sizeParams, sizePkS, sizeSkS, sizePkR, sizeSkR, sizeForwardKey, sizeCipherText, sizeTrapdoor = ("N/A", ) * 8
	if isinstance(parameter, (tuple, list)) and len(parameter) >= 5:
		n, m, q, lS, lR = parameter[:5]
	elif isinstance(parameter, dict):
		n, m, q, lS, lR = tuple(parameter.get(key) for key in ("n", "m", "q", "lS", "lR"))
	else:
		n, m, q, lS, lR = (None, ) * 5
	if all(isinstance(value, int) for value in (n, m, q, lS, lR)):
		nString, mString, qString, lSString, lRString = n, m, q, lS, lR
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Parameters: (n = {0}, m = {1}, q = {2}, lS = {3}, lR = {4})".format(nString, mString, qString, lSString, lRString))
		print("run:", runString)
	try:
		if not all(isinstance(value, int) for value in (n, m, q, lS, lR)):
			raise ValueError("The parameters are invalid. ")
		scheme = SchemeFSMUAEKS()
		startTime = perf_counter()
		params = scheme.Setup(n, m, q, lS, lR)
		timeSetup = perf_counter() - startTime
		isSystemValid = True
		startTime = perf_counter()
		pkS, skS = scheme.KeyGenS()
		timeKeyGenS = perf_counter() - startTime
		startTime = perf_counter()
		pkR, skR = scheme.KeyGenR()
		timeKeyGenR = perf_counter() - startTime
		startTime = perf_counter()
		forwardSecretKey, forwardKey = scheme.KeyUpdate()
		timeKeyUpdate = perf_counter() - startTime
		startTime = perf_counter()
		cipherText = scheme.Encryption()
		timeEncryption = perf_counter() - startTime
		startTime = perf_counter()
		trapdoor = scheme.Trapdoor()
		timeTrapdoor = perf_counter() - startTime
		startTime = perf_counter()
		isSchemeCorrect = scheme.Test()
		timeTest = perf_counter() - startTime
		sizeParams = scheme.getLengthOf(params)
		sizePkS, sizeSkS = scheme.getLengthOf(pkS), scheme.getLengthOf(skS)
		sizePkR, sizeSkR = scheme.getLengthOf(pkR), scheme.getLengthOf(skR)
		sizeForwardKey = scheme.getLengthOf((forwardSecretKey, forwardKey))
		sizeCipherText, sizeTrapdoor = scheme.getLengthOf(cipherText), scheme.getLengthOf(trapdoor)
		isCompleted = True
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Is the system valid? Yes. ")
			print("Is the scheme correct? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Time:", (timeSetup, timeKeyGenS, timeKeyGenR, timeKeyUpdate, timeEncryption, timeTrapdoor, timeTest))
			print("Space:", (sizeParams, sizePkS, sizeSkS, sizePkR, sizeSkR, sizeForwardKey, sizeCipherText, sizeTrapdoor))
			print()
	except BaseException as e:
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Is the system valid? No. The execution failed due to {0}. ".format(repr(e)))
			print()
	return ([
		nString, mString, qString, lSString, lRString, runString,
		isSystemValid, isSchemeCorrect,
		timeSetup, timeKeyGenS, timeKeyGenR, timeKeyUpdate, timeEncryption, timeTrapdoor, timeTest,
		sizeParams, sizePkS, sizeSkS, sizePkR, sizeSkR, sizeForwardKey, sizeCipherText, sizeTrapdoor
	], isCompleted)

def conductScheme(parameter:tuple|list|dict, run:int|None = None, isVerbose:bool = False) -> list:
	result, isCompleted = __conductScheme(parameter, run, isVerbose)
	attempt = 1
	while isCompleted and not result[7] and attempt < MAXIMUM_ATTEMPT_COUNT:
		result, isCompleted = __conductScheme(parameter, run, isVerbose)
		attempt += 1
	return result

def main() -> int:
	flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed = Parser.parse(argv)
	if flag > EXIT_SUCCESS and flag > EOF:
		if any((
			arange is None, asarray is None, concatenate is None, dot is None, eye is None, fill_diagonal is None, 
			kron is None, ndarray is None, triu_indices is None, zeros is None, lstsq is None, randint is None, Matrix is None
		)):
			Parser.disableConsoleEchoes()
			print("The runtime environment of the Python NumPy and SymPy libraries is not correctly configured. ")
			print("Please install the libraries via the active Python package manager (e.g., pip). ")
			errorLevel = EOF
		else:
			outputFilePath, overwritingConfirmed = Parser.checkOverwriting(outputFilePath, overwritingConfirmed)
			Parser.disableConsoleEchoes()
			print("The execution has started. ")
			print()
			
			# Parameters #
			parameters = ((2, 8, 16, 2, 2), (4, 16, 16, 4, 2))
			queries = ("n", "m", "q", "lS", "lR", "runCount")
			validators = ("isSystemValid", "isSchemeCorrect")
			metrics = (
				"Setup (s)", "KeyGenS (s)", "KeyGenR (s)", "KeyUpdate (s)", "Encryption (s)", "Trapdoor (s)", "Test (s)",
				"params (B)", "pkS (B)", "skS (B)", "pkR (B)", "skR (B)", "forwardKey (B)", "cipherText (B)", "trapdoor (B)"
			)
			
			# Scheme #
			columns, queryLength, results = queries + validators + metrics, len(queries), []
			queryValidatorLength, runCountIndex = queryLength + len(validators), queryLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for parameter in parameters:
					runs = [conductScheme(parameter, run = run, isVerbose = isVerbose) for run in range(1, runCount + 1)]
					averages = list(runs[0])
					for index in range(queryLength, queryValidatorLength):
						averages[index] = sum(int(result[index]) for result in runs)
					for index in range(queryValidatorLength, len(columns)):
						values = tuple(result[index] for result in runs)
						averages[index] = sum(values) / runCount if all(isinstance(value, (float, int)) and value > 0 for value in values) else "N/A"
						if isinstance(averages[index], float) and averages[index].is_integer():
							averages[index] = int(averages[index])
					averages[runCountIndex] = runCount
					results.append(averages)
					saver.save(results)
			except KeyboardInterrupt:
				print()
				print("The experiments were interrupted by users. Saved results are retained. ")
			except BaseException as e:
				print()
				print("The experiments were interrupted by {0}. Saved results are retained. ".format(repr(e)))
			errorLevel = EXIT_SUCCESS if results and all(
				all(result[index] == runCount for index in range(queryLength, queryValidatorLength))
				and all(isinstance(result[index], (float, int)) and result[index] > 0 for index in range(queryValidatorLength, len(columns)))
				for result in results
			) else EXIT_FAILURE
	elif EXIT_SUCCESS == flag:
		errorLevel = flag
		Parser.disableConsoleEchoes()
	else:
		errorLevel = EOF
		Parser.disableConsoleEchoes()
	if 0 == waitingTime:
		print("The execution has finished ({0}). ".format(errorLevel))
		print()
	elif isinstance(waitingTime, (float, int)) and 0 < waitingTime < float("inf"):
		integerTime, timeString = int(waitingTime), str(waitingTime)
		decimalTime = waitingTime - integerTime
		if "e" in timeString:
			timeString = str(integerTime) + ("{{0:.{0}f}}".format(decimalPlace).format(decimalTime).strip("0").rstrip(".") if decimalTime >= 10 ** (-decimalPlace) else "")
		timeStringLength = len(timeString)
		print("Please wait {0} second(s) for automatic exit, or exit manually, for example by pressing ``Ctrl + C`` ({1}). ".format(timeString, errorLevel))
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
		print("Please press the Enter key to exit ({0}). ".format(errorLevel))
		try:
			getpass("")
		except:
			print()
	Parser.restoreConsoleEchoes()
	return errorLevel



if "__main__" == __name__:
	exit(main())