from os import chdir, makedirs, name, sep
from os.path import abspath, dirname, exists, isdir, join, split, splitext
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, G2, GT, ZR, pair, Element = (None, ) * 7
from codecs import lookup
from hashlib import md5, sha1, sha3_224, sha3_256, sha3_384, sha3_512
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
	__SchemeName = "SchemeHIBME" # splitext(basename(__file__))[0]
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
		print("This is the official implementation of the HIB-ME cryptographic scheme in Python programming language based on the Python Charm-Crypto framework. ")
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

class SchemeHIBME:
	__DefaultL = 30
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer, but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__l = SchemeHIBME.__DefaultL
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
	def Setup(self:object, l:int = __DefaultL) -> tuple: # $\textbf{Setup}(l) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(l, int) and l >= 3: # boundary check
			self.__l = l
		else:
			self.__l = SchemeHIBME.__DefaultL
			print("Setup: The variable $l$ should be a positive integer not smaller than $3$, but it is not, which has been defaulted to ${0}$. ".format(SchemeHIBME.__DefaultL))
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		alpha, b1, b2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, b_1, b_2 \in \mathbb{Z}_r$ randomly
		s, a = tuple(self.__group.random(ZR) for _ in range(self.__l)), tuple(self.__group.random(ZR) for _ in range(self.__l)) # generate $s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l \in \mathbb{Z}_r$ randomly
		g2, g3 = self.__group.random(G2), self.__group.random(G2) # generate $g_2, g_3 \in \mathbb{G}_2$ randomly
		h = tuple(self.__group.random(G2) for _ in range(self.__l)) # generate $h_1, h_2, \cdots, h_l \in \mathbb{G}_2$ randomly (Note that the indexes in implementations are 1 smaller than those in theory)
		H1 = lambda x:self.__group.hash(x, G1) # $H_1:\mathbb{Z}_r \to \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G2) # $H_2:\mathbb{Z}_r \to \mathbb{G}_2$
		if 512 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha3_384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha3_256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha3_224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			HHat = lambda x:int.from_bytes(sha3_512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $\hat{H}: \mathbb{G}_T \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 224, 256, 384, 512, or 1024 as the security parameter. ".format(self.__group.secparam))
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		A = pair(g1, g2) # $A \gets e(g_1, g_2)$
		gBar = g ** b1 # $\bar{g} \gets g^{b_1}$
		gTilde = g ** b2 # $\tilde{g} \gets g^{b_2}$
		g3Bar = g3 ** (1 / b1) # $\bar{g}_3 \gets g_3^{\frac{1}{b_1}}$
		g3Tilde = g3 ** (1 / b2) # $\tilde{g}_3 \gets g_3^{\frac{1}{b_2}}$
		self.__mpk = (g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde) + h + (H1, H2, HHat, A) # $\textit{mpk} \gets (g, g_1, g_2, g_3, \bar{g}, \tilde{g}, \bar{g}_3, \tilde{g}_3, h_1, h_2, \cdots, h_l, H_1, H_2, \hat{H}, A)$
		self.__msk = (g2 ** alpha, b1, b2) + s + a # $\textit{msk} \gets (g_2^\alpha, b_1, b_2, s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, IDk:tuple) -> tuple: # $\textbf{EKGen}(\textit{ID}_k) \to \textit{ek}_{\textit{ID}_k}$
		# Checks #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDk): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																														\
				"EKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$, but it is not, "	\
				+ "which has been generated randomly with a length of ${1} - 1 = {0}$. ".format(self.__l - 1, self.__l)																					\
			)
		
		# Unpack #
		H1 = self.__mpk[-4]
		s, a = self.__msk[3:-self.__l], self.__msk[-self.__l:]
		k = len(ID_k)
		
		# Scheme #
		Ak = self.__product(tuple(a[j] for j in range(k))) # $A_k \gets \prod\limits_{j = 1}^k a_j$
		ek1 = tuple(H1(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{ek}_{1, i} \gets H_1(I_i)^{s_i A_k}, \forall i \in \{1, 2, \cdots, k\}$
		ek2 = tuple(s[k + i] * Ak for i in range(self.__l - k)) # $\textit{ek}_{2, i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		ek3 = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1, ek2, ek3) # $\textit{ek}_{\textit{ID}_k} \gets (\textit{ek}_1, \textit{ek}_2, \textit{ek}_3)$
		
		# Return #
		return ek_ID_k # \textbf{return} $\textit{ek}_{\textit{ID}_k}$
	def DerivedEKGen(self:object, ekIDkMinus1:tuple, IDk:tuple) -> tuple: # $\textbf{DerivedEKGen}(\textit{ek}_{\textit{ID}_{k - 1}}, \textit{ID}_k) \to \textit{ek}_{\textit{ID}_k}$
		# Checks #
		if not self.__flag:
			print("DerivedEKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedEKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDk): # hybrid check
			ID_k = IDk
			if (																																																		\
				isinstance(ekIDkMinus1, tuple) and len(ekIDkMinus1) == 3 and isinstance(ekIDkMinus1[0], tuple) and len(ekIDkMinus1[0]) == len(ID_k) - 1 and all(isinstance(ele, Element) for ele in ekIDkMinus1[0])		\
				and isinstance(ekIDkMinus1[1], tuple) and len(ekIDkMinus1[1]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in ekIDkMinus1[1]])													\
				and isinstance(ekIDkMinus1[2], tuple) and len(ekIDkMinus1[2]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in ekIDkMinus1[2]])													\
			): # hybrid check
				ek_ID_kMinus1 = ekIDkMinus1
			else:
				ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
				print(																																																						\
					(																																																						\
						"DerivedEKGen: The variable $\\textit{{ek}}_{{\\textit{{ID}}_{{k - 1}}}}$ should be a tuple containing a tuple with $k - 1 = {0}$ element(s) and two tuples with $l - k + 1 = {1}$ element(s), but it is not, "		\
						+ "which has been generated accordingly. "																																											\
					).format(len(ID_k) - 1, self.__l - len(ID_k) + 1)																																										\
				)
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																	\
				(																																																	\
					"DerivedEKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$, but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																														\
				).format(self.__l - 1, self.__l)																																									\
			)
			ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
			print("DerivedEKGen: The variable $\\textit{ek}_{\\textit{ID}_{k - 1}}$ has been generated accordingly. ")
		
		# Unpack #
		H1 = self.__mpk[-4]
		a = self.__msk[-self.__l:]
		k = len(ID_k)
		ek1, ek2, ek3 = ek_ID_kMinus1
		
		# Scheme #
		ek1Prime = tuple(ek1[i] ** a[k - 1] for i in range(k - 1)) # $\textit{ek}'_{1, i} \gets \textit{ek}_{1, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		ek1kPrime = H1(ID_k[k - 1]) ** (ek2[0] * a[k - 1]) # $\textit{ek}'_{1, k} \gets H_1(I_k)^{\textit{ek}_{2, 1} a_k}$
		ek1Prime += (ek1kPrime, ) # $\textit{ek}'_1 \gets \textit{ek}'_1 || \langle\textit{ek}'_{1, k}\rangle$
		ek2Prime = tuple(ek2[i] * a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{ek}'_{2, i} \gets \textit{ek}_{2, i} \cdot a_k, \forall i \in \{2, 3, \cdots, l - k + 1\}$
		ek3Prime = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}'_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1Prime, ek2Prime, ek3Prime) # $\textit{ek}_{\textit{ID}_k} \gets (\textit{ek}'_1, \textit{ek}'_2, \textit{ek}'_3)$
		
		# Return #
		return ek_ID_k # \textbf{return} $\textit{ek}_{\textit{ID}_k}$
	def DKGen(self:object, IDk:tuple) -> tuple: # $\textbf{DKGen}(\textit{ID}_k) \to \textit{dk}_{\textit{ID}_k}$
		# Checks #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDk): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																															\
				(																																															\
					"DKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$, but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																												\
				).format(self.__l - 1, self.__l)																																							\
			)
		
		# Unpack #
		g, g3Bar, g3Tilde, h, H1, H2 = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3]
		g2ToThePowerOfAlpha, b1, b2, s, a = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[3:-self.__l], self.__msk[-self.__l:]
		k = len(ID_k)
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		HI = self.__product(tuple(h[i] ** ID_k[i] for i in range(k))) # $\textit{HI} \gets h_1^{I_1} h_2^{I_2} \cdots h_k^{I_k}$
		a0 = g2ToThePowerOfAlpha ** (b1 ** (-1)) * HI ** (r / b1) * g3Bar ** r # $a_0 \gets g_2^{\frac{\alpha}{b_1}} \cdot \textit{HI}^{\frac{r}{b_1}} \cdot \bar{g}_3^r$
		a1 = g2ToThePowerOfAlpha ** (b2 ** (-1)) * HI ** (r / b2) * g3Tilde ** r # $a_1 \gets g_2^{\frac{\alpha}{b_2}} \cdot \textit{HI}^{\frac{r}{b_2}} \cdot \tilde{g}_3^r$
		Ak = self.__product(tuple(a[j] for j in range(k))) # $A_k \gets \prod\limits_{j = 1}^k a_j$
		dk1 = ( # $\textit{dk}_1 \gets (
			(a0, a1, g ** r) # a_0, a_1, g^r,\allowbreak 
			+ tuple(h[i] ** (r / b1) for i in range(k, self.__l)) # h_{k + 1}^{\frac{r}{b_1}}, h_{k + 2}^{\frac{r}{b_1}}, \cdots, h_l^{\frac{r}{b_1}},\allowbreak 
			+ tuple(h[i] ** (r / b2) for i in range(k, self.__l)) # h_{k + 1}^{\frac{r}{b_2}}, h_{k + 2}^{\frac{r}{b_2}}, \cdots, h_l^{\frac{r}{b_2}},\allowbreak 
			+ tuple(h[i] ** (b1 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_1^{-1}}, h_{k + 2}^{b_1^{-1}}, \cdots, h_l^{b_1^{-1}},\allowbreak 
			+ tuple(h[i] ** (b2 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_2^{-1}}, h_{k + 2}^{b_2^{-1}}, \cdots, h_2^{b_1^{-1}},\allowbreak 
			+ (HI ** (1 / b1), HI ** (1 / b2)) # \textit{HI}^{\frac{1}{b_1}}, \textit{HI}^{\frac{1}{b_2}}
		) # )$
		dk2 = tuple(H2(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{dk}_{2, i} \gets H_2(I_i)^{s_i A_k}, \forall i \in \{1, 2, \cdots, k\}$
		dk3 = tuple(s[k + i] * Ak for i in range(self.__l - k)) # $\textit{dk}_{3, i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		dk4 = tuple(a[i] for i in range(k, self.__l)) # $\textit{dk}_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1, dk2, dk3, dk4) # $\textit{dk}_{\textit{ID}_k} \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3, \textit{dk}_4)$
		
		# Return #
		return dk_ID_k # \textbf{return} $\textit{dk}_{\textit{ID}_k}$
	def DerivedDKGen(self:object, dkIDkMinus1:tuple, IDk:tuple) -> tuple: # $\textbf{DerivedDKGen}(\textit{dk}_{\textit{ID}_{k - 1}}, \textit{ID}_k) \to \textit{dk}_{\textit{ID}_k}$
		# Checks #
		if not self.__flag:
			print("DerivedDKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedDKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDk): # hybrid check
			ID_k = IDk
			if (																																						\
				isinstance(dkIDkMinus1, tuple) and len(dkIDkMinus1) == 4 and isinstance(dkIDkMinus1[0], tuple)															\
				and len(dkIDkMinus1[0]) == ((self.__l - len(ID_k) + 1) << 2) + 5 and all(isinstance(ele, Element) for ele in dkIDkMinus1[0])							\
				and isinstance(dkIDkMinus1[1], tuple) and len(dkIDkMinus1[1]) == len(ID_k) - 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[1]])			\
				and isinstance(dkIDkMinus1[2], tuple) and len(dkIDkMinus1[2]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[2]])	\
				and isinstance(dkIDkMinus1[3], tuple) and len(dkIDkMinus1[3]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[3]])	\
			): # hybrid check
				dk_ID_kMinus1 = dkIDkMinus1
			else:
				dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
				print(																																										\
					(																																										\
						"DerivedDKGen: The variable $\\textit{{dk}}_{{\\textit{{ID}}_{{k - 1}}}}$ should be a tuple containing a tuple with $(l - k + 1) \\times 4 + 5 = {0}$ elements, "	\
						+ "a tuple with $k - 1 = {1}$ element(s), and two tuples with $l - k + 1 = {2}$ element(s), but it is not, which has been generated accordingly. "					\
					).format(((self.__l - len(ID_k) + 1) << 2) + 5, len(ID_k) - 1, self.__l - len(ID_k) + 1)																				\
				)
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																	\
				(																																																	\
					"DerivedDKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$, but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																														\
				).format(self.__l - 1, self.__l)																																									\
			)
			dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
			print("DerivedDKGen: The variable $\\textit{dk}_{\\textit{ID}_{k - 1}}$ has been generated accordingly. ")
		
		# Unpack #
		g, g3Bar, g3Tilde, h, H1, H2 = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3]
		a = self.__msk[-self.__l:]
		k = len(ID_k)
		dk1, dk2, dk3, dk4 = dk_ID_kMinus1
		a0, a1, b = dk1[0], dk1[1], dk1[2]
		lengthPerToken = self.__l - k + 1
		c0, c1, d0, d1 = dk1[3:3 + lengthPerToken], dk1[3 + lengthPerToken:3 + (lengthPerToken << 1)], dk1[-2 - (lengthPerToken << 1):-2 - lengthPerToken], dk1[-2 - lengthPerToken:-2]
		f0, f1 = dk1[-2], dk1[-1]
		
		# Scheme #
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
		a0Prime = a0 * c0[0] ** ID_k[k - 1] * (f0 * d0[0] ** ID_k[k - 1] * g3Bar) ** t # $a'_0 \gets a_0 \cdot c_{0, k}^{I_k} \cdot (f_0 \cdot d_{0, k}^{I_k} \cdot \bar{g}_3)^t$
		a1Prime = a1 * c1[0] ** ID_k[k - 1] * (f1 * d1[0] ** ID_k[k - 1] * g3Tilde) ** t # $a'_1 \gets a_1 \cdot c_{1, k}^{I_k} \cdot (f_1 \cdot d_{1, k}^{I_k} \cdot \tilde{g}_3)^t$
		dk1Prime = ( # $\textit{dk}'_1 \gets (
			(a0, a1, b * g ** t) # a'_0, a'_1, b \cdot g^t, 
			+ tuple(c0[i] * d0[i] ** t for i in range(1, self.__l - k + 1)) # c_{0, k + 1} \cdot d_{0, k + 1}^t, c_{0, k + 2} \cdot d_{0, k + 2}^t, \cdots, c_{0, l} \cdot d_{0, l}^t, 
			+ tuple(c1[i] * d1[i] ** t for i in range(1, self.__l - k + 1)) # c_{1, k + 1} \cdot d_{1, k + 1}^t, c_{1, k + 2} \cdot d_{1, k + 2}^t, \cdots, c_{1, l} \cdot d_{1, l}^t, 
			+ tuple(d0[i] for i in range(1, self.__l - k + 1)) # d_{0, k + 1}, d_{0, k + 2}, \cdots, d_{0, l}, 
			+ tuple(d1[i] for i in range(1, self.__l - k + 1)) # d_{1, k + 1}, d_{1, k + 2}, \cdots, d_{1, l}, 
			+ (f0 * c0[0] ** ID_k[k - 1], f1 * c1[0] ** ID_k[k - 1]) # f_0 \cdot c_{0, k}^{I_k}, f_1 \cdot c_{1, k}^{I_k}
		) # )$
		dk2Prime = tuple(dk2[i] ** a[k - 1] for i in range(k - 1)) # $\textit{dk}'_{2, i} \gets \textit{dk}_{2, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		dk2kPrime = H2(ID_k[k - 1]) ** (dk3[0] * a[k - 1]) # $\textit{dk}'_{2, k} \gets H_2(I_k)^{\textit{dk}_{3, 1} a_k}$
		dk2Prime += (dk2kPrime, ) # $\textit{dk}'_2 \gets \textit{dk}'_2 || \langle\textit{dk}'_{2, k}\rangle$
		dk3Prime = tuple(dk3[i] * a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{dk}'_{3, i} \gets \textit{dk}_{3, i} \cdot a_k, \forall i \in \{2, 3, \cdots, l - k + 1\}$
		dk4Prime = tuple(a[k + i] for i in range(self.__l - k)) # $\textit{dk}'_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1Prime, dk2Prime, dk3Prime, dk4Prime) # $\textit{dk}_{\textit{ID}_k} \gets (\textit{dk}'_1, \textit{dk}'_2, \textit{dk}'_3, \textit{dk}'_4)$
				
		# Return #
		return dk_ID_k # \textbf{return} $\textit{dk}_{\textit{ID}_k}$
	def Enc(self:object, ekIDS:tuple, IDSnd:tuple, IDRev:tuple, message:int|bytes) -> Element: # $\textbf{Enc}(\textit{ek}_{\textit{ID}_S}, \textit{ID}_\textit{Rev}, M) \to \textit{CT}$
		# Checks #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(IDSnd, tuple) and 2 <= len(IDSnd) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDSnd): # hybrid check
			ID_Snd = IDSnd
			if (
				isinstance(ekIDS, tuple) and len(ekIDS) == 3 and isinstance(ekIDS[0], tuple) and len(ekIDS[0]) == len(ID_Snd) and all(isinstance(ele, Element) for ele in ekIDS[0])
				and isinstance(ekIDS[1], tuple) and len(ekIDS[1]) == self.__l - len(ID_Snd) and all(isinstance(ele, Element) for ele in ekIDS[1])
				and isinstance(ekIDS[2], tuple) and len(ekIDS[2]) == self.__l - len(ID_Snd) and all(isinstance(ele, Element) for ele in ekIDS[2])
			): # hybrid check
				ek_ID_S = ekIDS
			else:
				ek_ID_S = self.EKGen(ID_Snd)
				print(
					"Enc: The variable $\\textit{{ek}}_{{\\textit{{ID}}_S}}$ should be a tuple containing a tuple with $n = {0}$ elements and two tuples with $l - n = {1}$ element(s), but it is not, which has been generated accordingly. ".format(	\
						len(ID_Snd), self.__l - len(ID_Snd)																																																\
					)																																																									\
				)
		else:
			ID_Snd = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																					\
				(																																																					\
					"Enc: The variable $\\textit{{ID}}_\textit{{Snd}}$ should be a tuple containing $n = \\|\\textit{{ID}}_\\textit{{Snd}}\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $n \\in [2, {0}]$, but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																																		\
				).format(self.__l - 1, self.__l)																																													\
			)
			ek_ID_S = self.EKGen(ID_Snd)
			print("Enc: The variable $\\textit{ek}_{\\textit{ID}_S}$ has been generated accordingly. ")
		if isinstance(IDRev, tuple) and 2 <= len(IDRev) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDRev): # hybrid check
			ID_Rev = IDRev
		else:
			ID_Rev = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																					\
				(																																																					\
					"Enc: The variable $\\textit{{ID}}_\textit{{Rev}}$ should be a tuple containing $m = \\|\\textit{{ID}}_\\textit{{Rev}}\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $m \\in [2, {0}]$, but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																																		\
				).format(self.__l - 1, self.__l)																																													\
			)
		if isinstance(message, int) and message >= 0: # type check
			M = message & self.__operand
			if message != M:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			M = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			M = int.from_bytes(b"SchemeHIBME", byteorder = "big") & self.__operand
			print("Enc: The variable $M$ should be an integer or a ``bytes`` object, but it is not, which has been defaulted to b\"SchemeHIBME\". ")
		
		# Unpack #
		g, g3, gBar, gTilde, h, H1, H2, HHat, A = self.__mpk[0], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3], self.__mpk[-2], self.__mpk[-1]
		s, a = self.__msk[3:-self.__l], self.__msk[-self.__l:]
		n, m = len(ID_Snd), len(ID_Rev)
		
		# Scheme #
		s1, s2, eta = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2, \eta \in \mathbb{Z}_r$ randomly
		T = A ** (s1 + s2) # $T \gets A^{s_1 + s_2}$
		if m == n: # \textbf{if} $m = n$ \textbf{then}
			K = self.__product(tuple(pair(g ** eta * ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(n))) # \quad$K \gets \prod_{i = 1}^n e(g^{\eta} \cdot \textit{ek}_{1, i}, H_2(I'_i))$
		elif m > n: # \textbf{else if} $m > n$ \textbf{then}
			An = self.__product(tuple(a[i] for i in range(n))) # \quad$A_n \gets \prod\limits_{i = 1}^n a_i$
			Bmn = self.__product(tuple(a[i] for i in range(n, m))) # \quad$B_n^m \gets \prod\limits_{i = n + 1}^m a_i$
			K = ( # \quad$K \gets
				( # (
					self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(n))) # \prod\limits_{i = 1}^n e(\textit{ek}_{1, i}, H_2(I'_i))
					* self.__product(tuple(pair(H1(ID_Snd[n - 1]), H2(ID_Rev[i])) ** (s[i] * An) for i in range(n, m))) # \cdot \prod\limits_{i = n + 1}^m e(H_1(I_n), H_2(I'_i))^{s_i A_n}
				) ** Bmn # )^{B_n^m}
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(g^{\eta}, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # \textbf{else if} $m < n$ \textbf{then}
			K = ( # \quad$K \gets
				self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(m))) # \prod\limits_{i = 1}^m e(\textit{ek}_{1, i}, H_2(I'_i))
				* self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[m - 1])) for i in range(m, n))) # \prod\limits_{i = m + 1}^n e(\textit{ek}_{1, i}, H_2(I'_m))
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # e(g^{\eta}, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		# \textbf{end if}
		C1 = M ^ HHat(T) ^ HHat(K) # $C_1 \gets M \oplus \hat{H}(T) \oplus \hat{H}(K)$
		C2 = gBar ** s1 # $C_2 \gets \bar{g}^{s_1}$
		C3 = gTilde ** s2 # $C_3 \gets \tilde{g}^{s_2}$
		C4 = (self.__product(tuple(h[i] ** ID_Snd[i] for i in range(n))) * g3) ** (s1 + s2) # $C_4 \gets (h_1^{I_1} h_2^{I_2} \cdots h_n^{I_n} \cdot g_3)^{s_1 + s_2}$
		C5 = g ** eta # $C_5 \gets g^{\eta}$
		CT = (C1, C2, C3, C4, C5) # $\textit{CT} \gets (C_1, C_2, C_3, C_4, C_5)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec(self:object, dkIDR:tuple, IDRev:tuple, IDSnd:tuple, cipherText:tuple) -> bytes: # $\textbf{Dec}(\textit{dk}_{\textit{ID}_R}, \textit{ID}_\textit{Rev}, \textit{ID}_\textit{Snd}, \textit{CT}) \to M$
		# Checks #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(IDRev, tuple) and 2 <= len(IDRev) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDRev): # hybrid check
			ID_Rev = IDRev
			if (																																		\
				isinstance(dkIDR, tuple) and len(dkIDR) == 4 and isinstance(dkIDR[0], tuple)															\
				and len(dkIDR[0]) == ((self.__l - len(ID_Rev)) << 2) + 5 and all(isinstance(ele, Element) for ele in dkIDR[0])							\
				and isinstance(dkIDR[1], tuple) and len(dkIDR[1]) == len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[1]])				\
				and isinstance(dkIDR[2], tuple) and len(dkIDR[2]) == self.__l - len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[2]])		\
				and isinstance(dkIDR[3], tuple) and len(dkIDR[3]) == self.__l - len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[3]])		\
			): # hybrid check
				dk_ID_R = dkIDR
			else:
				dk_ID_R = self.DKGen(ID_Rev)
				print(																																					\
					(																																					\
						"Dec: The variable $\\textit{dk}_{\\textit{ID}_R}$ should be a tuple containing a tuple with $(l - m) \\times 4 + 5 = {0}$ elements, "			\
						+ "a tuple with $m - 1 = {1}$ element(s), and two tuples with $l - m = {2}$ element(s), but it is not, which has been generated accordingly. "	\
					).format(((self.__l - len(ID_Rev)) << 2) + 5, len(ID_Rev), self.__l - len(ID_Rev))																	\
				)
		else:
			ID_Rev = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																					\
				(																																																					\
					"Dec: The variable $\\textit{{ID}}_\\textit{{Rev}}$ should be a tuple containing $m = \\|\\textit{{ID}}_\\textit{{Rev}}\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $m \\in [2, {0}]$, but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																																		\
				).format(self.__l - 1, self.__l)																																													\
			)
			dk_ID_R = self.DKGen(ID_Rev)
			print("Dec: The variable $\\textit{dk}_{\\textit{ID}_R}$ has been generated accordingly. ")
		if isinstance(IDSnd, tuple) and 2 <= len(IDSnd) < self.__l and all(isinstance(ele, Element) and ele.type == ZR for ele in IDSnd): # hybrid check
			ID_Snd = IDSnd
		else:
			ID_Snd = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																																					\
				(																																																					\
					"Dec: The variable $\\textit{{ID}}_\\textit{{Snd}}$ should be a tuple containing $n = \\|\\textit{{ID}}_\\textit{{Snd}}\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $n \\in [2, {0}]$, but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																																		\
				).format(self.__l - 1, self.__l)																																													\
			)
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and isinstance(cipherText[0], int) and all(isinstance(ele, Element) for ele in cipherText[1:]): # hybrid check
			CT = cipherText
		else:
			CT = self.Enc(self.EKGen(ID_Snd), ID_Snd, ID_Rev, int.from_bytes(b"SchemeHIBME", byteorder = "big") & self.__operand)
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing an integer and 4 elements, but it is not, which has been generated randomly with $M$ set to b\"SchemeHIBME\". ")
		
		# Unpack #
		H1, H2, HHat = self.__mpk[-4], self.__mpk[-3], self.__mpk[-2]
		s, a = self.__msk[3:-self.__l], self.__msk[-self.__l:]
		C1, C2, C3, C4, C5 = CT
		dk1, dk2, dk3, dk4 = dk_ID_R
		m, n = len(ID_Rev), len(ID_Snd)
		
		# Scheme #
		TPrime = pair(dk1[2], C4) / (pair(C2, dk1[0]) * pair(C3, dk1[1])) # $T' = \cfrac{e(\textit{dk}_{1, 3}, C_4)}{e(C_2, \textit{dk}_{1, 1})e(C_3, \textit{dk}_{1, 2})}$
		if m == n: # \textbf{if} $m = n$ \textbf{then}
			KPrime = ( # \quad$K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \prod\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i}) 
				 * pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(n)))) # \cdot e(C_5, \prod\limits_{i = 1}^n H_2(I'_i))
			) # $
		elif m > n: # \textbf{else if} $m > n$ \textbf{then}
			KPrime = ( # \quad$K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \prod\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i})
				* self.__product(tuple(pair(H1(ID_Snd[n - 1]), dk2[i]) for i in range(n, m))) # \cdot \prod\limits_{i = n + 1}^m e(H_1(I_n), \textit{dk}_{2, i})
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(C_5, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # \textbf{else if} $m < n$ \textbf{then}
			Am = self.__product(tuple(a[i] for i in range(m))) # \quad$A_m \gets \prod\limits_{i = 1}^m a_i$
			Bnm = self.__product(tuple(a[i] for i in range(m, n))) # \quad$B_n^m \gets \prod\limits_{i = m + 1}^n a_i$
			KPrime = ( # \quad$K' \gets
				( # (
					self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(m))) # \prod\limits_{i = 1}^m e(H_1(I_i), \textit{dk}_{2, i})
					* self.__product(tuple(pair(H1(ID_Snd[i]), H2(ID_Rev[m - 1])) ** (s[i] * Am) for i in range(m, n))) # \cdot \prod\limits_{i = m + 1}^n e(H_1(I_i), H_2(I'_m))^{s_i A_m}
				) ** Bnm # )^{B_m^n}
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(C_5, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		# \textbf{end if}
		M = C1 ^ HHat(TPrime) ^ HHat(KPrime) # $M \gets C_1 \oplus \hat{H}(T') \oplus \hat{H}(K')$
		
		# Return #
		return M # \textbf{return} $M$
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


def conductScheme(curveParameter:tuple|list|dict|str, l:int = 30, m:int = 20, n:int = 10, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, lString, mString, nString, runString = "N/A", 512, "N/A", "N/A", "N/A", "N/A" # the default value of the security parameter in the Python Charm-Crypto framework is 512
	isSystemValid, isDeriverPassed, isSchemeCorrect = False, False, False
	timeSetup, timeEKGen, timeDerivedEKGen, timeDKGen, timeDerivedDKGen, timeEnc, timeDec = ("N/A", ) * 7
	sizeZR, sizeG1, sizeG2, sizeGT = ("N/A", ) * 4
	sizeMpk, sizeMsk, sizeEkIDS, sizeEkIDSDerived, sizeDkIDR, sizeDkIDRDerived, sizeCT = ("N/A", ) * 7
	
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
	if isinstance(l, int):
		lString = l
	else:
		flag = False
	if isinstance(m, int):
		mString = m
	else:
		flag = False
	if isinstance(n, int):
		nString = n
	else:
		flag = False
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Curve: ({0}, {1})".format(curveName, securityParameter))
		print("$l$:", lString)
		print("$m$:", mString)
		print("$n$:", nString)
		print("run:", runString)
	if flag and 2 <= m < l and 2 <= n < l:
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
		print("Is the system valid? No. The parameters $l$, $m$, and $n$ should be three positive integers satisfying $2 \\leqslant m < l \\land 2 \\leqslant n < l$. ")
		print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemeHIBME = SchemeHIBME(group)
		sizeZR, sizeG1, sizeG2, sizeGT = schemeHIBME.getLengthOf(group.random(ZR)), schemeHIBME.getLengthOf(group.random(G1)), schemeHIBME.getLengthOf(group.random(G2)), schemeHIBME.getLengthOf(group.random(GT))
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemeHIBME.Setup(l = l)
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemeHIBME.getLengthOf(mpk), schemeHIBME.getLengthOf(msk)
		
		# EKGen #
		startTime = perf_counter()
		ID_Snd = tuple(group.random(ZR) for _ in range(n))
		ek_ID_S = schemeHIBME.EKGen(ID_Snd)
		endTime = perf_counter()
		timeEKGen = endTime - startTime
		sizeEkIDS = schemeHIBME.getLengthOf(ek_ID_S)
		
		# DerivedEKGen #
		startTime = perf_counter()
		ek_ID_SMinus1 = schemeHIBME.EKGen(ID_Snd[:-1]) # remove the last one to generate the ek_ID_SMinus1
		ek_ID_SDerived = schemeHIBME.DerivedEKGen(ek_ID_SMinus1, ID_Snd)
		endTime = perf_counter()
		timeDerivedEKGen = endTime - startTime
		sizeEkIDSDerived = schemeHIBME.getLengthOf(ek_ID_SDerived)
		
		# DKGen #
		startTime = perf_counter()
		ID_Rev = tuple(group.random(ZR) for _ in range(m))
		dk_ID_R = schemeHIBME.DKGen(ID_Rev)
		endTime = perf_counter()
		timeDKGen = endTime - startTime
		sizeDkIDR = schemeHIBME.getLengthOf(dk_ID_R)
		
		# DerivedDKGen #
		startTime = perf_counter()
		dk_ID_RMinus1 = schemeHIBME.DKGen(ID_Rev[:-1]) # remove the last one to generate the dk_ID_RMinus1
		dk_ID_RDerived = schemeHIBME.DerivedDKGen(dk_ID_RMinus1, ID_Rev)
		endTime = perf_counter()
		timeDerivedDKGen = endTime - startTime
		sizeDkIDRDerived = schemeHIBME.getLengthOf(dk_ID_RDerived)
		
		# Enc #
		startTime = perf_counter()
		message = int.from_bytes(b"SchemeHIBME", byteorder = "big")
		CT = schemeHIBME.Enc(ek_ID_S, ID_Snd, ID_Rev, message)
		CTDerived = schemeHIBME.Enc(ek_ID_SDerived, ID_Snd, ID_Rev, message)
		endTime = perf_counter()
		timeEnc = endTime - startTime
		sizeCT = schemeHIBME.getLengthOf(CT)
		
		# Dec #
		startTime = perf_counter()
		M = schemeHIBME.Dec(dk_ID_R, ID_Rev, ID_Snd, CT)
		MDerived = schemeHIBME.Dec(dk_ID_RDerived, ID_Rev, ID_Snd, CTDerived)
		endTime = perf_counter()
		isDeriverPassed = MDerived == message
		isSchemeCorrect = M == message
		timeDec = endTime - startTime
		
		# Destruction #
		del schemeHIBME
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Original:", message)
			print("Derived:", MDerived)
			print("Decrypted:", M)
			print("Is the deriver passed (M' == message)? {0}. ".format("Yes" if isDeriverPassed else "No"))
			print("Is the scheme correct (M == message)? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Time:", (timeSetup, timeEKGen, timeDerivedEKGen, timeDKGen, timeDerivedDKGen, timeEnc, timeDec))
			print("Space:", (sizeZR, sizeG1, sizeG2, sizeGT, sizeMpk, sizeMsk, sizeEkIDS, sizeEkIDSDerived, sizeDkIDR, sizeDkIDRDerived, sizeCT))
			print()
	
	# End #
	return [																					\
		curveName, securityParameter, lString, mString, nString, runString, 					\
		isSystemValid, isDeriverPassed, isSchemeCorrect, 										\
		timeSetup, timeEKGen, timeDerivedEKGen, timeDKGen, timeDerivedDKGen, timeEnc, timeDec, 	\
		sizeZR, sizeG1, sizeG2, sizeGT, 														\
		sizeMpk, sizeMsk, sizeEkIDS, sizeEkIDSDerived, sizeDkIDR, sizeDkIDRDerived, sizeCT		\
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
			queries = ("curveParameter", "secparam", "l", "m", "n", "runCount")
			validators = ("isSystemValid", "isDeriverPassed", "isSchemeCorrect")
			metrics = (																									\
				"Setup (s)", "EKGen (s)", "DerivedEKGen (s)", "DKGen (s)", "DerivedDKGen (s)", "Enc (s)", "Dec (s)", 	\
				"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 							\
				"mpk (B)", "msk (B)", "EK (B)", "EK' (B)", "DK (B)", "DK' (B)", "CT (B)"								\
			)
			getValidatorJudges = lambda x:x[queryLength:queryValidatorLength]
			getMetricJudges = lambda x:x[queryValidatorLength:]
			
			# Scheme #
			columns, queryLength, results = queries + validators + metrics, len(queries), []
			length, queryValidatorLength, runCountIndex = len(columns), queryLength + len(validators), queryLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for l in range(10, 31, 5):
						for m in range(5, l, 5):
							for n in range(5, l, 5):
								averages = conductScheme(curveParameter, l = l, m = m, n = n, run = 1, isVerbose = isVerbose)
								for run in range(2, runCount + 1):
									result = conductScheme(curveParameter, l = l, m = m, n = n, run = run, isVerbose = isVerbose)
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