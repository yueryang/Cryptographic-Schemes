from os import chdir, makedirs, name, sep
from os.path import abspath, dirname, exists, isdir, join, split, splitext
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, GT, ZR, pair, Element = (None, ) * 6
from codecs import lookup
from hashlib import md5, sha1, sha3_224, sha3_256, sha3_384, sha3_512
from math import ceil, log
from secrets import randbelow
from time import perf_counter, sleep
from warnings import filterwarnings
filterwarnings(																																												\
	"ignore", category = DeprecationWarning, 																																				\
	message = "^Curve \'SS[0-9]+\' provides only ~80-bit security, which is below the 128-bit minimum recommended by NIST. Use \'BN254\' \\(128-bit\\) or stronger for production use\\.$"	\
)
try:
	chdir(abspath(dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Parser:
	__SchemeName = "SchemePBAC" # splitext(basename(__file__))[0]
	__OptionEncoding = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
	__DefaultEncoding = "utf-8"
	__OptionHelp = ("h", "/h", "-h", "help", "/help", "--help")
	__OptionOutput = ("o", "/o", "-o", "output", "/output", "--output")
	__DefaultExtension = ".xlsx"
	__DefaultOutputFileName = __SchemeName + __DefaultExtension
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
	def __init__(self:object, arguments:tuple|list) -> object:
		self.__arguments = tuple(argument for argument in arguments if isinstance(argument, str)) if isinstance(arguments, (tuple, list)) else ()
		self.__originalConsoleAttributes = None
		self.__echolessConsoleAttributes = None
		self.__tcsetattr = None
	def __formatOption(self:object, option:tuple|list, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, (tuple, list)) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	def __printHelp(self:object) -> None:
		print("This is the official implementation of the PBAC cryptographic scheme in Python programming language based on the Python Charm-Crypto framework. ")
		print()
		print("Options (case-insensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(Parser.__OptionHelp)))
		print("\t{0} [|.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(	\
			self.__formatOption(Parser.__OptionOutput), Parser.__SchemeName, repr(Parser.__DefaultOutputFileName)												\
		))
		print("\t{0} [s|ms|microsecond|ns|ps|0|3|6|9|12|...]\t\tSpecify the decimal place, which should be a non-negative integer. The default value is {1}. ".format(	\
			self.__formatOption(Parser.__OptionPlace), Parser.__DefaultPlace)																							\
		)
		print("\t{0}\t\tDisable the verbose console outputs. ".format(self.__formatOption(Parser.__OptionQuiet)))
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the run count, which must be a positive integer. The default value is {1}. ".format(self.__formatOption(Parser.__OptionRun), Parser.__DefaultRun))
		print(																																							\
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(self.__formatOption(Parser.__OptionTime))	\
			+ "Passing inf requires users to manually press the enter key before exiting. The default value is {0}. ".format(Parser.__DefaultTime)						\
		)
		print("\t{0}\t\tIndicate to confirm the overwriting of the existing output file. ".format(self.__formatOption(Parser.__OptionYes)))
		print()
	def __handlePath(self:object, filePath:str) -> str:
		if isinstance(filePath, str):
			if isdir(filePath) or filePath.endswith((sep, "/")):
				print("Parser: The output file path passed looks like a folder, which would be connected with the default file name {0}. ".format(repr(Parser.__DefaultOutputFileName)))
				return self.__handlePath(join(filePath, Parser.__DefaultOutputFileName))
			elif splitext(split(filePath)[1])[1][1:].upper() in Parser.__ProtectedExtensionNames:
				print("Parser: The extension name of the output file path passed is one of the protected extension names, which would be reset to the default extension {0}. ".format(repr(self.__DefaultExtension)))
				return self.__handlePath(splitext(filePath)[0] + Parser.__DefaultExtension)
			else:
				return filePath
		else:
			return Parser.__DefaultOutputFileName
	def __parseRealNumber(self:object, string:str) -> int|float|None:
		try:
			realNumberString = "".join(ch for ch in string if ch.isalnum() or ch in "+-.").lower()
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
					for ch in decimalPartString.rstrip("0")[::-1]:
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
	def parse(self:object) -> tuple:
		flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed = (																	\
			max(EXIT_SUCCESS, EOF) + 1, Parser.__DefaultEncoding, Parser.__DefaultOutputFileName, Parser.__DefaultPlace, True, Parser.__DefaultRun, Parser.__DefaultTime, False		\
		)
		index, argumentCount, buffers = 1, len(self.__arguments), []
		while index < argumentCount:
			argument = self.__arguments[index].lower()
			if argument in Parser.__OptionEncoding:
				index += 1
				if index < argumentCount:
					try:
						lookup(self.__arguments[index])
						encoding = self.__arguments[index]
					except:
						flag = EOF
						buffers.append("Parser: The value [0] = {1} for the encoding option is invalid. ".format(index, repr(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the encoding option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionHelp:
				self.__printHelp()
				flag = EXIT_SUCCESS
				break
			elif argument in Parser.__OptionOutput:
				index += 1
				if index < argumentCount:
					outputFilePath = self.__handlePath(self.__arguments[index])
				else:
					flag = EOF
					buffers.append("Parser: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionPlace:
				index += 1
				if index < argumentCount:
					decimalPlaceLower = self.__arguments[index].lower()
					if decimalPlaceLower in Parser.__PlaceTranslations:
						decimalPlace = Parser.__PlaceTranslations[decimalPlaceLower]
					else:
						p = self.__parseRealNumber(self.__arguments[index])
						if p is None:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option cannot be recognized. ".format(index, repr(self.__arguments[index])))
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
					r = self.__parseRealNumber(self.__arguments[index])
					if r is None:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the run count option is invalid. ".format(index, repr(self.__arguments[index])))
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
					t = self.__parseRealNumber(self.__arguments[index])
					if t is None:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the waiting time option is invalid. ".format(index, repr(self.__arguments[index])))
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
				buffers.append("Parser: The option [{0}] = {1} is unknown. ".format(index, repr(self.__arguments[index])))
			index += 1
		if EOF == flag:
			for buffer in buffers:
				print(buffer)
		return (flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed)
	def checkOverwriting(self:object, outputFP:str, overwriting:bool) -> tuple:
		if isinstance(outputFP, str) and isinstance(overwriting, bool):
			outputFilePath, overwritingConfirmed, flag = outputFP, overwriting, False
			while outputFilePath and exists(outputFilePath):
				if isfile(outputFilePath):
					if not overwritingConfirmed:
						flag = True
						try:
							overwritingConfirmed = input("The file {0} exists. Overwrite the file or not [yN]? ".format(repr(outputFilePath))).upper() in ("Y", "YES", "1", "T", "TRUE")
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
						outputFilePath = self.__handlePath(input("Please specify a new output file path or leave it empty for console output: "))
					except:
						print()
			if flag:
				print()
			return (outputFilePath, overwritingConfirmed)
		else:
			return (outputFP, overwriting)
	def disableConsoleEchoes(self:object) -> bool:
		if "posix" == name:
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
		if "posix" == name:
			try:
				self.__tcsetattr(0, 0, self.__originalConsoleAttributes)
			except:
				return False
		return True
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

class Saver:
	def __init__(self:object, outputFilePath:str = Parser.getDefaultOutputFilePath(), columns:tuple|list = tuple(), decimalPlace:int = Parser.getDefaultPlace(), encoding:str = Parser.getDefaultEncoding()) -> object:
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else Parser.getDefaultOutputFilePath()
		self.__columns = tuple(column for column in columns if isinstance(column, str)) if isinstance(columns, (tuple, list)) else tuple()
		self.__decimalPlace = decimalPlace if isinstance(decimalPlace, int) and decimalPlace >= 0 else Parser.getDefaultPlace()
		self.__encoding = encoding if isinstance(encoding, str) else Parser.getDefaultEncoding()
		self.__folderPath = dirname(self.__outputFilePath)
		self.__extensionName = splitext(split(self.__outputFilePath)[1])[1][1:].upper()
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
		if not self.__folderPath:
			return True
		elif exists(self.__folderPath):
			return isdir(self.__folderPath)
		else:
			try:
				makedirs(self.__folderPath)
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
										self.__escapeHTML = lambda x:str(x).replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#39;")	\
											.replace("<", "&lt;").replace(">", "&gt;").replace("\r\n", "<br />").replace("\n", "<br />").replace("\r", "<br />")
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
												f.write("\t\t\t\t\t<td>{0}</td>\n".format(																	\
													"{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else self.__escapeHTML(r)	\
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
										self.__escapeTEX = lambda x:"\\textbackslash{}".join(													\
											string.replace("#", "\\#").replace("$", "\\$").replace("%", "\\%").replace("&", "\\&")				\
											.replace("_", "\\_").replace("{", "\\{").replace("}", "\\}")										\
											.replace("<", "\\textless{}").replace(">", "\\textgreater{}")										\
											.replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")								\
											for string in "".join(character for character in str(x) if ' ' <= character <= '~').split("\\")		\
										)
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										maxLength = max(len(self.__columnsTEX) if isinstance(self.__columnsTEX, (tuple, list)) else 0, max(len(result) for result in results))
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
												f.write(" & ".join((																	\
													"${0}$" if isinstance(r, int) else "${{0:.{0}f}}$".format(self.__decimalPlace)		\
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
											worksheet.write(i, j, "{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r, self.__styleXLSValues)
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
										self.__escapeXML = lambda x:"".join(character for character in str(x) if ' ' <= character <= '~')		\
											.replace("&", "&amp;").replace("\"", "&quot;").replace("\'", "&apos;").replace("<", "&lt;").replace(">", "&gt;")
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
													f.write("  - - {0}\n".format(															\
														self.__dumpsJSON(result[0], indent = "\t", sort_keys = True, ensure_ascii = True)	\
													))
													for r in result[1:]:
														f.write("    - {0}\n".format(													\
															self.__dumpsJSON(r, indent = "\t", sort_keys = True, ensure_ascii = True)	\
														))
												else:
													f.write("  - []")
										else:
											f.write("results: []")
								elif self.__extensionName in Parser.getProtectedExtensionNames():
									print("Saver: Failed to save the results to {0} since {1} is one of the protected extension names. ".format(repr(self.__outputFilePath), self.__extensionName))
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
								print("Saver: Failed to save the results to {0} in the {1} format due to the following exception(s). \n\t{2}".format(	\
									repr(self.__outputFilePath), self.__extensionName, repr(e)															\
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
									print("Saver: Failed to save the results to {0} due to the following exception(s). \n\t{1}".format(repr(self.__outputFilePath), repr(e)))
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

class SchemePBAC:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		try:
			pair(self.__group.random(G1), self.__group.random(G1))
		except:
			self.__group = PairingGroup("SS512", secparam = self.__group.secparam)
			print("Init: This scheme is only applicable to symmetric groups of prime orders. The curve name has been defaulted to \"SS512\". ")
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer, but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		s, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $s, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \to \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \to \mathbb{G}_1$
		H3 = lambda x1, x2, x3:self.__group.hash(																						\
			self.__group.serialize(x1) + self.__group.serialize(x2) + (self.__group.serialize(x3) if isinstance(x3, Element) else (		\
				x3.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") if isinstance(x3, int) else bytes(x3)					\
			)), ZR																														\
		) # $H_3: \mathbb{G}_T^2 \times \{0, 1\}^\lambda \to \mathbb{Z}_r$
		if 512 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha3_384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha3_256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha3_224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H4 = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest() * ceil(self.__group.secparam / 512), byteorder = "big") & self.__operand # $H_4: \{0, 1\}^* \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 224, 256, 384, 512, or 1024 as the security parameter. ".format(self.__group.secparam))
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \to \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \to \mathbb{G}_1$
		gHat = g ** s # $\hat{g} \gets g^s$
		self.__mpk = (g, gHat, H1, H2, H3, H4, H5, H6) # $ \textit{mpk} \gets (g, \hat{g}, H_1, H_2, H_3, H_4, H_5, H_6)$
		self.__msk = (s, alpha) # $\textit{msk} \gets (s, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, idS:bytes) -> Element: # $\textbf{SKGen}(\textit{id}_S) \to \textit{ek}_{\textit{id}_S}$
		# Checks #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("SKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def RKGen(self:object, idR:bytes) -> tuple: # $\textbf{RKGen}(\textit{id}_R) \to \textit{dk}_{\textit{id}_R}$
		# Checks #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("RKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[3]
		s, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H2(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 1} \gets H_2(\textit{id}_R)^\alpha$
		dk_id_R2 = H2(id_R) ** s # $\textit{dk}_{\textit{id}_R, 2} \gets H_2(\textit{id}_R)^s$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def Enc(self:object, ekid1:Element, id2:Element, message:int|bytes) -> tuple: # $\textbf{Enc}(\textit{ek}_{\textit{id}_1}, \textit{id}_2, m) \to C$
		# Checks #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element) and ekid1.type == G1: # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_1}$ should be an element of $\\mathbb{G}_1$, but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\textit{id}_2$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemePBAC", byteorder = "big") & self.__operand
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object, but it is not, which has been defaulted to b\"SchemePBAC\". ")
		
		# Unpack #
		g, gHat, H2, H3, H4, H5 = self.__mpk[0], self.__mpk[1], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6]
		
		# Scheme #
		eta_1, eta_2 = self.__group.random(GT), self.__group.random(GT) # generate $\eta_1, \eta_2 \in \mathbb{G}_T$ randomly
		r = H3(eta_1, eta_2, m) # $r \gets H_3(\eta_1, \eta_2, m)$
		C1 = g ** r # $C_1 \gets g^r$
		C2 = eta_1 * pair(gHat, H2(id_2) ** r) # $C_2 \gets \eta_1 \cdot e(\hat{g}, H_2(\textit{id}_2)^r)$
		C3 = eta_2 * pair(ek_id_1, H2(id_2)) # $C_3 \gets \eta_2 \cdot e(\textit{ek}_{\textit{id}_1}, H_2(\textit{id}_2))$
		C4 = m ^ H4(eta_1) ^ H4(eta_2) # $C_4 \gets m \oplus H_4(\eta_1) \oplus H_4(\eta_2)$
		S = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) ** r # $S \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)^r$
		C = (C1, C2, C3, C4, S) # $C \gets (C_1, C_2, C_3, C_4, S)$
		
		# Return #
		return C # \textbf{return} $C$
	def PKGen(self:object, ekid2:Element, dkid2:tuple, id1:bytes, id2:bytes, id3:bytes) -> tuple: # $\textbf{PKGen}(\textit{ek}_{\textit{id}_2}, \textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{id}_2, \textit{id}_3) \to \textit{rk}$
		# Checks #
		if not self.__flag:
			print("PKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``PKGen`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(ekid2, Element) and ekid2.type == G1: # type check
				ek_id_2 = ekid2
			else:
				ek_id_2 = self.SKGen(id_2)
				print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element of $\\mathbb{G}_1$, but it is not, which has been generated accordingly. ")
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements, but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
			ek_id_2 = self.SKGen(id_2)
			print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.RKGen(id_2)
			print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_3$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2, H6 = self.__mpk[3], self.__mpk[7]
		
		# Scheme #
		N1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") # generate $N_1 \in \{0, 1\}^\lambda$ randomly
		N2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") # generate $N_2 \in \{0, 1\}^\lambda$ randomly
		K1 = pair(dk_id_2[1], H2(id_3)) # $K_1 \gets e(\textit{dk}_{\textit{id}_2, 2}, H_2(\textit{id}_3))$
		K2 = pair(ek_id_2, H2(id_3)) # $K_2 \gets e(\textit{ek}_{\textit{id}_2}, H_2(\textit{id}_3))$
		rk_1 = (N1, H6(self.__group.serialize(K1) + id_2 + id_3 + N1) * dk_id_2[1]) # $\textit{rk}_1 \gets (N_1, H_6(K_1 || \textit{id}_2 || \textit{id}_3 || N_1) \cdot \textit{dk}_{\textit{id}_2, 2})$
		rk_2 = (N2, H6(self.__group.serialize(K2) + id_2 + id_3 + N2) * dk_id_2[0]) # $\textit{rk}_2 \gets (N_2, H_6(K_2 || \textit{id}_2 || \textit{id}_3 || N_2) \cdot \textit{dk}_{\textit{id}_2, 1})$
		rk = (id_1, id_2, rk_1, rk_2) # $\textit{rk} \gets (\textit{id}_1, \textit{id}_2, \textit{rk}_1, \textit{rk}_2)$
		
		# Return #
		return rk # \textbf{return} $\textit{rk}$
	def ProxyEnc(self:object, reKey:tuple, cipherText:tuple) -> tuple|bool: # $\textbf{ProxyEnc}(\textit{ct}, \textit{rk}) \to \textit{CT}$
		# Checks #
		if not self.__flag:
			print("ProxyEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ProxyEnc`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all(isinstance(ele, bytes) for ele in reKey[:2]) and all(isinstance(ele, tuple) for ele in reKey[-2:]): # hybrid check
			rk, id2Generated = reKey, reKey[1]
		else:
			rk = self.PKGen(																																				\
				self.SKGen(id2Generated), self.RKGen(id2Generated), randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), 	\
				id2Generated, randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")											\
			)
			print("ProxyEnc: The variable $\\textit{rk}$ should be a tuple containing 2 ``bytes`` object and 2 tuples, but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("ProxyEnc: The variable $C$ should be a tuple containing 4 elements and an integer, but it is not, which has been generated randomly with $m$ set to b\"SchemePBAC\". ")
		del id2Generated
		
		# Unpack #
		g, H1, H5 = self.__mpk[0], self.__mpk[2], self.__mpk[6]
		id_1, id_2, rk_1, rk_2 = rk
		C1, C2, C3, C4, S = C
		
		# Scheme #
		h = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) # $h \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)$
		if pair(h, C1) == pair(g, S): # \textbf{if} $e(h, C_1) = e(g, S) $\textbf{then}
			t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
			C2Prime = C2 / (pair(C1, rk_1[1] * h ** t) / pair(g ** t, S)) # $C_2' \gets C_2 / \cfrac{e(C_1, \textit{rk}_{1, 2} \cdot h^t)}{e(g^t, S)}$
			C3Prime = C3 / pair(H1(id_1), rk_2[1]) # $C_3' \gets C_3 / e(H_1(\textit{id}_1), \textit{rk}_{2, 2})$
			CT = (id_1, C1, C2Prime, C3Prime, C4, rk_1[0], rk_2[0]) # $\textit{CT} \gets (\textit{id}_1, C_1, C_2', C_3', C_4, \textit{rk}_{1, 1}, \textit{rk}_{2, 1})$
		else: # \textbf{else}
			CT = False # \quad$\textit{CT} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec1(self:object, dkid2:tuple, id2:bytes, id1:bytes, cipherText:tuple) -> int|bool: # $\textbf{Dec}_1(\textit{dk}_{\textit{id}_2}, \textit{id}_2, \textit{id}_1, \textit{ct}) \to m$
		# Checks #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements, but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_2$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
			dk_id_2 = self.RKGen(id_2)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id_2, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("Dec1: The variable $C$ should be a tuple containing 4 elements and an integer, but it is not, which has been generated randomly with $m$ set to b\"SchemePBAC\". ")
		
		# Unpack #
		g, H1, H3, H4, H5 = self.__mpk[0], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6]
		C1, C2, C3, C4, S = C
		
		# Scheme #
		h = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) # $h \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)$
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
		eta_1 = C2 / (pair(C1, dk_id_2[1] * h ** t) / pair(g ** t, S)) # $\eta_1 \gets C_2 / \cfrac{e(C_1, \textit{dk}_{\textit{id}_2, 2} \cdot h^t)}{e(g^t, S)}$
		eta_2 = C3 / pair(dk_id_2[0], H1(id_1)) # $\eta_2 \gets C_3 / e(\textit{dk}_{\textit{id}_2, 1}, H_1(\textit{id}_1))$
		m = C4 ^ H4(eta_1) ^ H4(eta_2) # $m \gets C_4 \oplus H_4(\eta_1) \oplus H_4(\eta_2)$
		r = H3(eta_1, eta_2, m) # $r \gets H_3(\eta_1, \eta_2, m)$
		if S != h ** r or C1 != g ** r: # \textbf{if} $S \neq h^r \lor C_1 \neq g^r$ \textbf{then}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkid3:tuple, id3:bytes, id2:bytes, cipherText:tuple|bool) -> int|bool: # $\textbf{Dec}_2(\textit{dk}_{\textit{id}_3}, \textit{id}_3, \textit{id}_2, \textit{CT}) \to m'$
		# Checks #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all(isinstance(ele, Element) for ele in dkid3): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.RKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements, but it is not, which has been generated randomly. ")
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
			dk_id_3 = self.RKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object, but it is not, which has been generated randomly. ")
		if (																																							\
			isinstance(cipherText, tuple) and len(cipherText) == 7 and isinstance(cipherText[0], bytes) and all(isinstance(ele, Element) for ele in cipherText[1:4])	\
			and isinstance(cipherText[4], int) and isinstance(cipherText[5], bytes) and isinstance(cipherText[6], bytes)												\
		): # hybrid check
			CT = cipherText
		elif isinstance(cipherText, bool):
			return False
		else:
			CT = self.ProxyEnc(self.PKGen(self.SKGen(id_2), self.RKGen(id_2), id_1, id_2, id_3), self.Enc(self.SKGen(id_1), id_2, b"SchemePBAC"))
			print("Dec2: The variable $\\textit{CT}$ should be a tuple containing 7 objects, but it is not, which has been generated randomly with $m$ set to b\"SchemePBAC\". ")
		
		# Unpack #
		g, H1, H2, H3, H4, H6 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[7]
		id_1, C1, C2Prime, C3Prime, C4, N1, N2 = CT
		
		# Scheme #
		K1Prime = pair(dk_id_3[1], H2(id_2)) # $K_1' \gets e(\textit{dk}_{\textit{id}_3, 2}, H_2(\textit{id}_2))$
		K2Prime = pair(dk_id_3[0], H1(id_2)) # $K_2' \gets e(\textit{dk}_{\textit{id}_3, 1}, H_1(\textit{id}_2))$
		eta1Prime = C2Prime * pair(C1, H6(self.__group.serialize(K1Prime) + id_2 + id_3 + N1)) # $\eta_1' \gets C_2' \cdot e(C_1, H_6(K_1' || \textit{id}_2 || \textit{id}_3 || N_1))$
		eta2Prime = C3Prime * pair(H6(self.__group.serialize(K2Prime) + id_2 + id_3 + N2), H1(id_1)) # $\eta_2' \gets C_3' \cdot e(H_6(K_2' || \textit{id}_2 || \textit{id}_3 || N_2), H_1(\textit{id}_1))$
		mPrime = C4 ^ H4(eta1Prime) ^ H4(eta2Prime) # $m' \gets C_4 \oplus H_4(\eta_1') \oplus H_4(\eta_2')$
		rPrime = H3(eta1Prime, eta2Prime, mPrime) # $r' \gets H_3(\eta_1', \eta_2', m')$
		if C1 != g ** rPrime: # \textbf{if} $C_1 \neq g^{r'}$ \textbf{then}
			mPrime = False # \quad$m' \gets \perp$
		# \textbf{end if}
		
		# Return #
		return mPrime # \textbf{return} $m'$
	def getLengthOf(self:object, obj:Element|int|bytes|tuple|list|set|dict) -> int|str:
		if isinstance(obj, Element):
			return len(self.__group.serialize(obj))
		elif isinstance(obj, int) or callable(obj):
			return (self.__group.secparam + 7) >> 3
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(o) for o in obj)
			return sum(sizes) if all(isinstance(size, int) and size >= 1 for size in sizes) else "N/A"
		elif isinstance(obj, dict):
			sizes = tuple(self.getLengthOf(value) for value in obj.values())
			return sum(sizes) if all(isinstance(size, int) and size >= 1 for size in sizes) else "N/A"
		else:
			return "N/A"


def conductScheme(curveParameter:tuple|list|dict|str, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, runString = "N/A", 512, "N/A" # the default value of the security parameter in the Python Charm-Crypto framework is 512
	isSystemValid, isProxyEncPassed, isDec1Passed, isDec2Passed = (False, ) * 4
	timeSetup, timeSKGen, timeRKGen, timeEnc, timePKGen, timeProxyEnc, timeDec1, timeDec2 = ("N/A", ) * 8
	sizeZR, sizeG1G2, sizeGT = ("N/A", ) * 3
	sizeMpk, sizeMsk, sizeEkId1, sizeEkId2, sizeDkId2, sizeDkId3, sizeC, sizeRk, sizeCT = ("N/A", ) * 9
	
	# Checks #
	if isinstance(curveParameter, (tuple, list)):
		if len(curveParameter) >= 1 and isinstance(curveParameter[0], str) and curveParameter[0].isalnum():
			curveName = curveParameter[0]
		if len(curveParameter) >= 2 and isinstance(curveParameter[1], int) and curveParameter[1] >= 1:
			securityParameter = curveParameter[1]
	elif isinstance(curveParameter, dict):
		if "curveName" in curveParameter and isinstance(curveParameter["curveName"], str) and curveParameter["curveName"].isalnum():
			curveName = curveParameter["curveName"]
		if "securityParameter" in curveParameter and isinstance(curveParameter["securityParameter"], int) and curveParameter["securityParameter"] >= 1:
			securityParameter = curveParameter["securityParameter"]
	elif isinstance(curveParameter, str) and curveParameter.isalnum():
		curveName = curveParameter
	flag = True
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Curve: ({0}, {1})".format(curveName, securityParameter))
		print("run:", runString)
	if flag:
		try:
			group = PairingGroup(curveName, secparam = securityParameter)
			pair(group.random(G1), group.random(G1))
			isSystemValid = True
			if not isinstance(isVerbose, bool) or isVerbose:
				print("Is the system valid? Yes. ")
		except BaseException as e:
			if not isinstance(isVerbose, bool) or isVerbose:
				print("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to {0}. ".format(repr(e)))
				print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemePBAC = SchemePBAC(group)
		sizeZR, sizeG1G2, sizeGT = schemePBAC.getLengthOf(group.random(ZR)), schemePBAC.getLengthOf(group.random(G1)), schemePBAC.getLengthOf(group.random(GT))
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemePBAC.Setup()
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemePBAC.getLengthOf(mpk), schemePBAC.getLengthOf(msk)
		
		# SKGen #
		startTime = perf_counter()
		id_1 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
		id_2 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
		ek_id_1 = schemePBAC.SKGen(id_1)
		ek_id_2 = schemePBAC.SKGen(id_2)
		endTime = perf_counter()
		timeSKGen = (endTime - startTime) / 2
		sizeEkId1 = schemePBAC.getLengthOf(ek_id_1)
		sizeEkId2 = schemePBAC.getLengthOf(ek_id_2)
		
		# RKGen #
		startTime = perf_counter()
		id_3 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
		dk_id_2 = schemePBAC.RKGen(id_2)
		dk_id_3 = schemePBAC.RKGen(id_3)
		endTime = perf_counter()
		timeRKGen = (endTime - startTime) / 2
		sizeDkId2 = schemePBAC.getLengthOf(dk_id_2)
		sizeDkId3 = schemePBAC.getLengthOf(dk_id_3)
		
		# Enc #
		startTime = perf_counter()
		message = int.from_bytes(b"SchemePBAC", byteorder = "big")
		C = schemePBAC.Enc(ek_id_1, id_2, message)
		endTime = perf_counter()
		timeEnc = endTime - startTime
		sizeC = schemePBAC.getLengthOf(C)
		
		# PKGen #
		startTime = perf_counter()
		rk = schemePBAC.PKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
		endTime = perf_counter()
		timePKGen = endTime - startTime
		sizeRk = schemePBAC.getLengthOf(rk)
		
		# ProxyEnc #
		startTime = perf_counter()
		CT = schemePBAC.ProxyEnc(rk, C)
		endTime = perf_counter()
		timeProxyEnc = endTime - startTime
		isProxyEncPassed = not isinstance(CT, bool)
		sizeCT = schemePBAC.getLengthOf(CT)
		
		# Dec1 #
		startTime = perf_counter()
		m = schemePBAC.Dec1(dk_id_2, id_2, id_1, C)
		endTime = perf_counter()
		timeDec1 = endTime - startTime
		isDec1Passed = m == message
		
		# Dec2 #
		startTime = perf_counter()
		mPrime = schemePBAC.Dec2(dk_id_3, id_3, id_2, CT)
		endTime = perf_counter()
		timeDec2 = endTime - startTime
		isDec2Passed = mPrime == message
		
		# Destruction #
		del schemePBAC
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Original:", message)
			print("Dec1:", m)
			print("Dec2:", mPrime)
			print("Is ``ProxyEnc`` passed? {0}. ".format("Yes" if isProxyEncPassed else "No"))
			print("Is ``Dec1`` passed (m == message)? {0}. ".format("Yes" if isDec1Passed else "No"))
			print("Is ``Dec2`` passed (m' == message)? {0}. ".format("Yes" if isDec2Passed else "No"))
			print("Time:", (timeSetup, timeSKGen, timeRKGen, timeEnc, timePKGen, timeProxyEnc, timeDec1, timeDec2))
			print("Space:", (sizeZR, sizeG1G2, sizeGT, sizeMpk, sizeMsk, sizeEkId1, sizeEkId2, sizeDkId2, sizeDkId3, sizeC, sizeRk, sizeCT))
			print()
	
	# End #
	return [																													\
		curveName, securityParameter, runString, 													\
		isSystemValid, isProxyEncPassed, isDec1Passed, isDec2Passed, 								\
		timeSetup, timeSKGen, timeRKGen, timeEnc, timePKGen, timeProxyEnc, timeDec1, timeDec2, 		\
		sizeZR, sizeG1G2, sizeGT, 																	\
		sizeMpk, sizeMsk, sizeEkId1, sizeEkId2, sizeDkId2, sizeDkId3, sizeC, sizeRk, sizeCT			\
	]

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		if any((PairingGroup is None, G1 is None, GT is None, ZR is None, pair is None, Element is None)):
			parser.disableConsoleEchoes()
			print("The execution environment of the Python Charm-Crypto framework is not handled correctly. ")
			print("Please refer to https://github.com/JHUISI/charm if necessary. ")
			errorLevel = EOF
		else:
			outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
			parser.disableConsoleEchoes()
			print("The execution has started. ")
			print()
			
			# Parameters #
			curveParameters = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
			queries = ("curveParameter", "secparam", "runCount")
			validators = ("isSystemValid", "isProxyEncPassed", "isDec1Passed", "isDec2Passed")
			metrics = (																											\
				"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "PKGen (s)", "ProxyEnc (s)", "Dec1 (s)", "Dec2 (s)", 			\
				"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 														\
				"mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "C (B)", "rk (B)", "CT (B)"	\
			)
			getValidatorJudges = lambda x:x[queryLength:queryValidatorLength]
			getMetricJudges = lambda x:x[queryValidatorLength:]
			
			# Scheme #
			columns, queryLength, results = queries + validators + metrics, len(queries), []
			length, queryValidatorLength, runCountIndex = len(columns), queryLength + len(validators), queryLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					averages = conductScheme(curveParameter, run = 1, isVerbose = isVerbose)
					for run in range(2, runCount + 1):
						result = conductScheme(curveParameter, run = run, isVerbose = isVerbose)
						for idx in range(queryLength, queryValidatorLength):
							averages[idx] += result[idx]
						for idx in range(queryValidatorLength, length):
							averages[idx] = averages[idx] + result[idx] if isinstance(averages[idx], (float, int)) and averages[idx] > 0 and result[idx] > 0 else "N/A"
					averages[runCountIndex] = runCount
					for idx in range(queryValidatorLength, length):
						if isinstance(averages[idx], (float, int)) and averages[idx] > 0:
							averages[idx] /= runCount
							if averages[idx].is_integer():
								averages[idx] = int(averages[idx])
						else:
							averages[idx] = "N/A"
					results.append(averages)
					saver.save(results)
					if isVerbose:
						print()
				if not results:
					print("No experiments were conducted. ")
				elif not isVerbose:
					print()
			except KeyboardInterrupt:
				print()
				print("The experiments were interrupted by users. Saved results are retained. ")
			except BaseException as e:
				print()
				print("The experiments were interrupted by {0}. Saved results are retained. ".format(repr(e)))
			errorLevel = EXIT_SUCCESS if results and all(											\
				all(r == runCount for r in getValidatorJudges(result))								\
				and all(isinstance(r, (float, int)) and r > 0 for r in getMetricJudges(result))		\
				for result in results																\
			) else EXIT_FAILURE
	elif EXIT_SUCCESS == flag:
		errorLevel = flag
		parser.disableConsoleEchoes()
	else:
		errorLevel = EOF
		parser.disableConsoleEchoes()
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
		print("Please press the enter key to exit ({0}). ".format(errorLevel))
		try:
			getpass("")
		except:
			print()
	parser.restoreConsoleEchoes()
	del parser
	return errorLevel



if "__main__" == __name__:
	exit(main())