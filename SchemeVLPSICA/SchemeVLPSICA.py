from os import chdir, makedirs, name, sep
from os.path import abspath, dirname, exists, isdir, join, split, splitext
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, G2, GT, ZR, pair, Element = (None, ) * 7
from codecs import lookup
from hashlib import md5, sha1, sha3_224, sha3_256, sha3_384, sha3_512
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
	__SchemeName = "SchemeVLPSICA" # splitext(basename(__file__))[0]
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
		print("This is the official implementation of the VL-PSI-CA cryptographic scheme in Python programming language based on the Python Charm-Crypto framework. ")
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

class SchemeVLPSICA:
	__DefaultM, __DefaultN, __DefaultD = 10, 10, 10
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer, but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__m = SchemeVLPSICA.__DefaultM
		self.__n = SchemeVLPSICA.__DefaultN
		self.__d = SchemeVLPSICA.__DefaultD
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __product(self:object, elements:object) -> Element:
		try:
			if isinstance(elements, (tuple, list)):
				result = elements[0]
				for element in elements[1:]:
					result *= element
			else:
				it = iter(elements)
				result = next(it)
				for element in it:
					result *= element
			return result if isinstance(result, Element) else self.__group.init(ZR, result)
		except Exception:
			return self.__group.init(ZR, 1)
	def __computeLagrangeCoefficients(self:object, xPoints:tuple|list, yPoints:tuple|list, x:Element) -> Element:
		if (																																													\
			isinstance(xPoints, (tuple, list)) and isinstance(yPoints, (tuple, list)) and len(xPoints) == len(yPoints) and all(isinstance(ele, Element) and ele.type == ZR for ele in xPoints)	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in yPoints) and isinstance(x, Element) and x.type == ZR																	\
		):
			n, result = len(xPoints), self.__group.init(ZR, 1)
			for i in range(n):
				L_i = self.__group.init(ZR, 1)
				for j in range(n):
					if i != j:
						L_i *= (x - xPoints[j]) / (xPoints[i] - xPoints[j])
				result += yPoints[i] * L_i
			return result
		else:
			return self.__init(ZR, 0)
	def Setup(self:object, m:int = __DefaultM, n:int = __DefaultN, d:int = __DefaultD) -> tuple: # $\textbf{Setup}(m, n, d) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(m, int) and m >= 1:
			self.__m = m
		else:
			self.__m = SchemeVLPSICA.__DefaultM
			print("Setup: The variable $m$ should be a positive integer, but it is not, which has been defaulted to ${0}$. ".format(SchemeVLPSICA.__DefaultM))
		if isinstance(n, int) and n >= 1:
			self.__n = n
		else:
			self.__n = SchemeVLPSICA.__DefaultN
			print("Setup: The variable $n$ should be a positive integer, but it is not, which has been defaulted to ${0}$. ".format(SchemeVLPSICA.__DefaultN))
		if isinstance(d, int) and d >= 1:
			self.__d = d
		else:
			self.__d = SchemeVLPSICA.__DefaultD
			print("Setup: The variable $d$ should be a positive integer, but it is not, which has been defaulted to ${0}$. ".format(SchemeVLPSICA.__DefaultD))
		
		# Scheme #
		g1 = self.__group.init(G1, 1) # $g_1 \gets 1_{\mathbb{G}_1}$
		g2 = self.__group.init(G2, 1) # $g_2 \gets 1_{\mathbb{G}_2}$
		s = self.__group.random(ZR) # generate $s \in \mathbb{Z}_p^*$ randomly
		SVec = tuple(g2 ** (s ** i) for i in range(self.__m + self.__d + 1)) # $\vec{S} \gets (S_0, S_1, \cdots, S_{m + d}) = (g_2^{s_0}, g_2^{s_1}, \cdots, g_2^{s^{m + d}})$
		SPrime = g1 ** s # $S' \gets g_1^s \in \mathbb{G}_1$
		if 512 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha3_384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha3_256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha3_224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $H: \mathbb{G}_T \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 224, 256, 384, 512, or 1024 as the security parameter. ".format(self.__group.secparam))
		self.__mpk = (g1, SPrime, H) # $\textit{mpk} \gets (g_1, S', H)$
		self.__msk = (g2, SVec) # $\textit{msk} \gets (g_2, \vec{S})$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def Sender(self:object, _vVec:tuple, _YVec:tuple) -> tuple: # $\textbf{Sender}(\vec{v}, \vec{Y}) \to (\vec{T} || \vec{T}', \vec{U} || \vec{U}')$
		# Checks #
		if not self.__flag:
			print("Sender: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Sender`` subsequently. ")
			self.Setup()
		if isinstance(_vVec, tuple) and len(_vVec) == self.__d and all(isinstance(ele, Element) and ele.type == ZR for ele in _vVec): # hybrid check
			vVec = _vVec
		else:
			vVec = tuple(self.__group.random(ZR) for _ in range(self.__d))
			print("Sender: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$, but it is not, which has been generated randomly. ")
		if isinstance(_YVec, tuple) and len(_YVec) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in _YVec): # hybrid check
			YVec = _YVec
		else:
			YVec = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Sender: The variable $\\vec{Y}$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$, but it is not, which has been generated randomly. ")
		
		# Unpack #
		g1, SPrime = self.__mpk[0], self.__mpk[1]
		
		# Scheme #
		k = randbelow(self.__n) # generate $k \in \mathbb{N}* \cap [0, n)$ randomly
		pi = lambda x:(x + k) % self.__n # $\pi: x \to (x + k) \% n$
		tVec = tuple(self.__group.random(ZR) for j in range(self.__n)) # generate $\vec{t} \gets (t_1, t_2, \cdots, t_n) \in \mathbb{Z}_r^n$ randomly
		TVec = tuple(g1 ** tVec[j] for j in range(self.__n)) # $\vec{T} \gets (T_1, T_2, \cdots, T_n) = (g_1^{t_1}, g_1^{t_2}, \cdots, g_1^{t_n})$
		UVec = tuple(SPrime * g1 ** (-YVec[pi(j)]) for j in range(self.__n)) # $\vec{U} \gets (U_1, U_2, \cdots, U_n) = (S' \cdot (g_1^{-y_{\pi(1)}}), S' \cdot (g_1^{-y_{\pi(2)}}), \cdots, S' \cdot (g_1^{-y_{\pi(n)}}))$
		tPrimeVec = tuple(self.__group.random(ZR) for _ in range(self.__d)) # generate $\vec{t}' = (t'_1, t'_2, \cdots, t'_d) \in \mathbb{Z}_r^d$ randomly
		TPrimeVec = tuple(g1 ** tPrimeVec[j] for j in range(self.__d)) # $\vec{T}' \gets (T'_1, T'_2, \cdots, T'_d) = (g_1^{t'_1}, g_1^{t'_2}, \cdots, g_1^{t'_d})$
		UPrimeVec = tuple(SPrime * g1 ** (-vVec[j]) ** tPrimeVec[j] for j in range(self.__d)) # $\vec{U}' \gets (U'_1, U'_2, \cdots, U'_d) = (S' \cdot (g_1^{-v_1})^{t'_1}, S' \cdot (g_1^{-v_2})^{t'_2}, \cdots, S' \cdot (g_1^{-v_d})^{t'_d})$
		
		# Return #
		return (TVec + TPrimeVec, UVec + UPrimeVec) # \textbf{return} $(\vec{T} || \vec{T}', \vec{U} || \vec{U}')$
	def Receiver(self:object, _vVec:tuple, _XVec:tuple) -> tuple: # $\textbf{Receiver}(\vec{v}, \vec{X}) \to (R, \vec{R}')$
		# Checks #
		if not self.__flag:
			print("Receiver: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Receiver`` subsequently. ")
			self.Setup()
		if isinstance(_vVec, tuple) and len(_vVec) == self.__d and all(isinstance(ele, Element) and ele.type == ZR for ele in _vVec): # hybrid check
			vVec = _vVec
		else:
			vVec = tuple(self.__group.random(ZR) for _ in range(self.__d))
			print("Receiver: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$, but it is not, which has been generated randomly. ")
		if isinstance(_XVec, tuple) and len(_XVec) == self.__m and all(isinstance(ele, Element) and ele.type == ZR for ele in _XVec): # hybrid check
			XVec = _XVec
		else:
			XVec = tuple(self.__group.random(ZR) for _ in range(self.__m))
			print("Receiver: The variable $\\vec{X}$ should be a tuple containing $m$ elements of $\\mathbb{Z}_r$, but it is not, which has been generated randomly. ")
		
		# Unpack #
		SVec = self.__msk[1]
		
		# Scheme #
		XPrimeVec = XVec + vVec # $\vec{X}' \gets (\vec{X} || \vec{v}) \in \mathbb{Z}_r^{m + d}$
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		xPoints, yPoints = tuple(self.__group.init(ZR, j) for j in range(1, self.__m + self.__d + 1)), XPrimeVec
		R = self.__product(tuple(SVec[j] ** self.__computeLagrangeCoefficients(xPoints, yPoints, self.__group.init(ZR, j)) for j in range(self.__m + self.__d + 1))) ** r # $R \gets \left(\prod\limits_{j = 0}^{m + d} S_j^{p(X', j)}\right)^r$
		RPrimeVec = tuple(
			self.__product(tuple(SVec[j] ** self.__computeLagrangeCoefficients(xPoints, yPoints, self.__group.init(ZR, j)) for j in range(self.__m + self.__d))) ** r for i in range(self.__m + self.__d)
		) # $R_{-i} \gets \left(\prod\limits_{j = 0}^{m + d - 1} S_j^{p(X'_{-i}, j)}\right)^r, \forall i \in {1, 2, \cdots, m + d}$
		del xPoints, yPoints
		
		# Return #
		return (R, RPrimeVec) # \textbf{return} $(R, \vec{R}')$
	def Cloud1(self:object, _TTPrime:tuple, _R:Element) -> tuple: # $\textbf{Cloud1}((\vec{T}, \vec{T}'), R) \to \vec{W}$
		# Checks #
		if not self.__flag:
			print("Cloud1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Cloud1`` subsequently. ")
			self.Setup()
		if isinstance(_TTPrime, tuple) and len(_TTPrime) == self.__n + self.__d and all(isinstance(ele, Element) and ele.type == G1 for ele in _TTPrime): # hybrid check
			TTPrime = _TTPrime
		else:
			TTPrime = tuple(self.__group.random(G1) for _ in range(self.__n + self.__d))
			print("Cloud1: The variable $\\vec{{T}} || \\vec{{T}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$, but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_R, Element) and _R.type == G2: # type check
			R = _R
		else:
			R = self.__group.random(G2)
			print("Cloud1: The variable $R$ should be an element of $\\mathbb{G}_2$, but it is not, which has been generated randomly. ")
		
		# Unpack #
		H = self.__mpk[2]
		
		# Scheme #
		WVec = tuple(H(pair(TTPrime[j], R)) for j in range(self.__n + self.__d)) # $W_j \gets H(e((\vec{T} || \vec{T}')_j, R)), \forall j \in {1, 2, \cdots, n + d}$
		k1 = randbelow(self.__n + self.__d) # generate $k_1 \in \mathbb{N}* \cap [0, n + d)$ randomly
		pi1 = lambda x:(x + k1) % (self.__n + self.__d) # $\pi_1: x \to (x + k_1) \% (n + d)$
		WVec = tuple(WVec[pi1(j)] for j in range(self.__n + self.__d)) # $\vec{W} \gets \{\vec{W}_{\pi_1(j)}\}_j$
		
		# Return #
		return WVec # \textbf{return} $\vec{W}$
	def Cloud2(self:object, _UUPrime:tuple, _RPrimeVec:tuple) -> tuple: # $\textbf{Cloud2}(\vec{U}, R') \to \vec{K}$
		# Checks #
		if not self.__flag:
			print("Cloud2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Cloud2`` subsequently. ")
			self.Setup()
		if isinstance(_UUPrime, tuple) and len(_UUPrime) == self.__n + self.__d and all(isinstance(ele, Element) and ele.type == G1 for ele in _UUPrime): # hybrid check
			UUPrime = _UUPrime
		else:
			UUPrime = tuple(self.__group.random(G1) for _ in range(self.__n + self.__d))
			print("Cloud2: The variable $\\vec{{U}} || \\vec{{U}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$, but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_RPrimeVec, tuple) and len(_RPrimeVec) == self.__m + self.__d and all(isinstance(ele, Element) and ele.type == G2 for ele in _RPrimeVec): # hybrid check
			RPrimeVec = _RPrimeVec
		else:
			RPrimeVec = tuple(self.__group.random(G2) for _ in range(self.__m + self.__d))
			print("Cloud2: The variable $\\vec{{R}}'$ should be a tuple containing $m + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$, but it is not, which has been generated randomly. ".format(self.__m, self.__d, self.__m + self.__d))
		
		# Unpack #
		H = self.__mpk[2]
		
		# Scheme #
		KVec = tuple(H(pair(UUPrime[j], RPrimeVec[i])) for i in range(self.__m + self.__d) for j in range(self.__n + self.__d)) # $\vec{K}_{i(n + d) + j} \gets H(e((\vec{U} || \vec{U}')_j, R'_i)), \forall i \in {1, 2, \cdots, m + d}, \forall j \in {1, 2, \cdots, n + d}$
		k2 = randbelow((self.__m + self.__d) * (self.__n + self.__d)) # generate $k_2 \in \mathbb{N}* \cap [0, (m + d)(n + d))$ randomly
		pi2 = lambda i, j:(i * (self.__n + self.__d) + j + k2) % ((self.__m + self.__d) * (self.__n + self.__d)) # $\pi_2: i, j \to (i(n + d) + j + k_2) \% (m + d)(n + d)$
		KVec = tuple(KVec[pi2(i, j)] for i in range(self.__m + self.__d) for j in range(self.__n + self.__d)) # $\vec{K} \gets \{\vec{K}_{\pi_2(i, j)}\}_{i, j}$
		
		# Return #
		return KVec # \textbf{return} $\vec{K}$
	def Verify(self:object, _KVec:tuple, _WVec:tuple) -> int|bool: # $\textbf{Verify}(\vec{K}, \vec{W}) \to \textit{result}$
		# Checks #
		if not self.__flag:
			print("Verify: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Verify`` subsequently. ")
			self.Setup()
		if isinstance(_KVec, tuple) and len(_KVec) == (self.__m + self.__d) * (self.__n + self.__d) and all(isinstance(ele, int) for ele in _KVec): # hybrid check
			KVec = _KVec
		else:
			KVec = self.Cloud2(tuple(self.__group.random(G1) for _ in range(self.__n + self.__d)), tuple(self.__group.random(G2) for _ in range(self.__m + self.__d)))
			print("Verify: The variable $\\vec{{K}}$ should be a tuple containing $(m + d)(n + d) = {0}$ integers, but it is not, which has been generated randomly. ".format((self.__m + self.__d) * (self.__n + self.__d)))
		if isinstance(_WVec, tuple) and len(_WVec) == self.__n + self.__d and all(isinstance(ele, int) for ele in _WVec): # hybrid check
			WVec = _WVec
		else:
			WVec = self.Cloud1(tuple(self.__group.random(G1) for _ in range(self.__n + self.__d)), self.__group.random(G2))
			print("Verify: The variable $\\vec{{W}}$ should be a tuple containing $n + d = {0} + {1} = {2}$ integers, but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		
		# Unpack #
		pass
		
		# Scheme #
		if set(WVec) <= set(KVec): # \textbf{if} $\vec{W} \subseteq \vec{K}$ \textbf{then}
			result = self.__n # \quad$\textit{result} \gets |\vec{K} \cap \vec{W}| - d = |\vec{W}| - d = n + d - d = n$
		else: # \textbf{else}
			result = False # \quad$\textit{result} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return result # \textbf{return} $\textit{result}$
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


def conductScheme(curveParameter:tuple|list|dict|str, m:int = 10, n:int = 10, d:int = 10, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, mString, nString, dString, runString = "N/A", 512, "N/A", "N/A", "N/A", "N/A" # the default value of the security parameter in the Python Charm-Crypto framework is 512
	isSystemValid, isSchemeCorrect = False, False
	timeSetup, timeSender, timeReceiver, timeCloud1, timeCloud2, timeVerify = ("N/A", ) * 6
	sizeZR, sizeG1, sizeG2, sizeGT = ("N/A", ) * 4
	sizeMpk, sizeMsk, sizeTTPrime, sizeUUPrime, sizeR, sizeRPrimeVec, sizeWVec, sizeKVec = ("N/A", ) * 8
	
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
	if isinstance(m, int) and m >= 1:
		mString = m
	else:
		flag = False
	if isinstance(n, int) and n >= 1:
		nString = n
	else:
		flag = False
	if isinstance(d, int) and d >= 1:
		dString = d
	else:
		flag = False
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Curve: ({0}, {1})".format(curveName, securityParameter))
		print("$m$:", mString)
		print("$n$:", nString)
		print("$d$:", dString)
		print("run:", runString)
	if flag:
		try:
			group = PairingGroup(curveName, secparam = securityParameter)
			pair(group.random(G1), group.random(G2))
			isSystemValid = True
			if not isinstance(isVerbose, bool) or isVerbose:
				print("Is the system valid? Yes. ")
		except BaseException as e:
			if not isinstance(isVerbose, bool) or isVerbose:
				print("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to {0}. ".format(repr(e)))
				print()
	elif not isinstance(isVerbose, bool) or isVerbose:
		print("Is the system valid? No. The parameters $m$, $n$, and $d$ should be three positive integers. ")
		print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemeVLPSICA = SchemeVLPSICA(group)
		sizeZR, sizeG1, sizeG2, sizeGT = (																\
			schemeVLPSICA.getLengthOf(group.random(ZR)), schemeVLPSICA.getLengthOf(group.random(G1)), 	\
			schemeVLPSICA.getLengthOf(group.random(G2)), schemeVLPSICA.getLengthOf(group.random(GT))	\
		)
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemeVLPSICA.Setup(m = m, n = n, d = d)
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemeVLPSICA.getLengthOf(mpk), schemeVLPSICA.getLengthOf(msk)
		
		# Sender #
		startTime = perf_counter()
		vVec = tuple(group.random(ZR) for _ in range(d))
		YVec = tuple(group.random(ZR) for _ in range(n))
		TTPrime, UUPrime = schemeVLPSICA.Sender(vVec, YVec)
		endTime = perf_counter()
		timeSender = endTime - startTime
		sizeTTPrime, sizeUUPrime = schemeVLPSICA.getLengthOf(TTPrime), schemeVLPSICA.getLengthOf(UUPrime)
		
		# Receiver #
		startTime = perf_counter()
		XVec = tuple(group.random(ZR) for _ in range(m))
		R, RPrimeVec = schemeVLPSICA.Receiver(vVec, XVec)
		endTime = perf_counter()
		timeReceiver = endTime - startTime
		sizeR, sizeRPrimeVec = schemeVLPSICA.getLengthOf(R), schemeVLPSICA.getLengthOf(RPrimeVec)
		
		# Cloud1 #
		startTime = perf_counter()
		WVec = schemeVLPSICA.Cloud1(TTPrime, R)
		endTime = perf_counter()
		timeCloud1 = endTime - startTime
		sizeWVec = schemeVLPSICA.getLengthOf(WVec)
		
		# Cloud2 #
		startTime = perf_counter()
		KVec = schemeVLPSICA.Cloud2(UUPrime, RPrimeVec)
		endTime = perf_counter()
		timeCloud2 = endTime - startTime
		sizeKVec = schemeVLPSICA.getLengthOf(KVec)
		
		# Verify #
		startTime = perf_counter()
		result = schemeVLPSICA.Verify(KVec, WVec)
		endTime = perf_counter()
		isSchemeCorrect = result is not False
		timeVerify = endTime - startTime
		
		# Destruction #
		del schemeVLPSICA
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Verify:", result)
			print("Is the scheme correct (result is not False)? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Time:", (timeSetup, timeSender, timeReceiver, timeCloud1, timeCloud2, timeVerify))
			print("Space:", (sizeZR, sizeG1, sizeG2, sizeGT, sizeMpk, sizeMsk, sizeTTPrime, sizeUUPrime, sizeR, sizeRPrimeVec, sizeWVec, sizeKVec))
			print()
	
	# End #
	return [																					\
		curveName, securityParameter, mString, nString, dString, runString, 					\
		isSystemValid, isSchemeCorrect, 															\
		timeSetup, timeSender, timeReceiver, timeCloud1, timeCloud2, timeVerify, 				\
		sizeZR, sizeG1, sizeG2, sizeGT, 														\
		sizeMpk, sizeMsk, sizeTTPrime, sizeUUPrime, sizeR, sizeRPrimeVec, sizeWVec, sizeKVec	\
	]

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, isVerbose, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		if any((PairingGroup is None, G1 is None, G2 is None, GT is None, ZR is None, pair is None, Element is None)):
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
			curveParameters = ("MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 256), ("SS512", 512), ("SS1024", 512), ("SS1024", 1024))
			queries = ("curveParameter", "secparam", "m", "n", "d", "runCount")
			validators = ("isSystemValid", "isSchemeCorrect")
			metrics = (																						\
				"Setup (s)", "Sender (s)", "Receiver (s)", "Cloud1 (s)", "Cloud 2(s)", "Verify (s)", 		\
				"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 				\
				"mpk (B)", "msk (B)", "(T, T') (B)", "(U, U') (B)", "R (B)", "R' (B)", "W (B)", "K (B)"		\
			)
			getValidatorJudges = lambda x:x[queryLength:queryValidatorLength]
			getMetricJudges = lambda x:x[queryValidatorLength:]
			
			# Scheme #
			columns, queryLength, results = queries + validators + metrics, len(queries), []
			length, queryValidatorLength, runCountIndex = len(columns), queryLength + len(validators), queryLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for m in range(5, 31, 5):
						for n in range(5, 31, 5):
							for d in range(5, 31, 5):
								averages = conductScheme(curveParameter, m = m, n = n, d = d, run = 1, isVerbose = isVerbose)
								for run in range(2, runCount + 1):
									result = conductScheme(curveParameter, m = m, n = n, d = d, run = run, isVerbose = isVerbose)
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