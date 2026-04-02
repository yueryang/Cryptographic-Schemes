import os
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, G2, GT, ZR, pair, Element = (None, ) * 7
from codecs import lookup
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from secrets import randbelow
from time import perf_counter, sleep
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Parser:
	__SchemeName = "SchemeVLPSICA" # os.path.splitext(os.path.basename(__file__))[0]
	__OptionEncoding = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
	__DefaultEncoding = "utf-8"
	__OptionHelp = ("h", "/h", "-h", "help", "/help", "--help")
	__OptionOutput = ("o", "/o", "-o", "output", "/output", "--output")
	__DefaultExtension = ".xlsx"
	__DefaultOutputFileName = __SchemeName + __DefaultExtension
	__ProtectedExtensionNames = ("C", "CPP", "IPYNB", "JAR", "JAVA", "M", "PY")
	__OptionPlace = ("p", "/p", "-p", "place", "/place", "--place")
	__DefaultPlace = 9
	__PlaceTranslations = {"s":0, "second":0, "ms":3, "millisecond":3, "microsecond":6, "ns":9, "nanosecond":9, "ps":12, "picosecond":12, "fs":15, "femtosecond":15}
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
		print("This is the official implementation of the VL-PSI-CA cryptographic scheme in Python programming language based on the Python charm library. ")
		print()
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(Parser.__OptionHelp)))
		print("\t{0} [|.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(	\
			self.__formatOption(Parser.__OptionOutput), Parser.__SchemeName, repr(Parser.__DefaultOutputFileName)												\
		))
		print("\t{0} [s|ms|microsecond|ns|ps|0|3|6|9|12|...]\t\tSpecify the decimal place, which should be a non-negative integer. The default value is {1}. ".format(	\
			self.__formatOption(Parser.__OptionPlace), Parser.__DefaultPlace)																							\
		)
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the run count, which must be a positive integer. The default value is {1}. ".format(self.__formatOption(Parser.__OptionRun), Parser.__DefaultRun))
		print(																																							\
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(self.__formatOption(Parser.__OptionTime))	\
			+ "Passing inf requires users to manually press the enter key before exiting. The default value is {0}. ".format(Parser.__DefaultTime)						\
		)
		print("\t{0}\t\tIndicate to confirm the overwriting of the existing output file. ".format(self.__formatOption(Parser.__OptionYes)))
		print()
	def __handlePath(self:object, filePath:str) -> str:
		if isinstance(filePath, str):
			if os.path.isdir(filePath) or filePath.endswith((os.sep, "/")):
				print("Parser: The output file path passed looks like a folder, which would be connected with the default file name {0}. ".format(repr(Parser.__DefaultOutputFileName)))
				return self.__handlePath(os.path.join(filePath, Parser.__DefaultOutputFileName))
			elif os.path.splitext(os.path.split(filePath)[1])[1][1:].upper() in Parser.__ProtectedExtensionNames:
				print("Parser: The extension name of the output file path passed is one of the protected extension names, which would be reset to the default extension {0}. ".format(repr(self.__DefaultExtension)))
				return self.__handlePath(os.path.splitext(filePath)[0] + Parser.__DefaultExtension)
			else:
				return filePath
		else:
			return Parser.__DefaultOutputFileName
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
		flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = (																		\
			max(EXIT_SUCCESS, EOF) + 1, Parser.__DefaultEncoding, Parser.__DefaultOutputFileName, Parser.__DefaultPlace, Parser.__DefaultRun, Parser.__DefaultTime, False	\
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
		return (flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed)
	def checkOverwriting(self:object, outputFP:str, overwriting:bool) -> tuple:
		if isinstance(outputFP, str) and isinstance(overwriting, bool):
			outputFilePath, overwritingConfirmed, flag = outputFP, overwriting, False
			while outputFilePath and os.path.exists(outputFilePath):
				if os.path.isfile(outputFilePath):
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
	def __init__(self:object, outputFilePath:str = Parser.getDefaultOutputFilePath(), columns:tuple|list|None = None, decimalPlace:int = Parser.getDefaultPlace(), encoding:str = Parser.getDefaultEncoding()) -> object:
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else Parser.getDefaultOutputFilePath()
		self.__columns = tuple(column for column in columns if isinstance(column, str)) if isinstance(columns, (tuple, list)) else None
		self.__decimalPlace = decimalPlace if isinstance(decimalPlace, int) and decimalPlace >= 0 else Parser.getDefaultPlace()
		self.__encoding = encoding if isinstance(encoding, str) else Parser.getDefaultEncoding()
		self.__folderPath = os.path.dirname(self.__outputFilePath)
		self.__extensionName = os.path.splitext(os.path.split(self.__outputFilePath)[1])[1][1:].upper()
		self.__Writer = None # CSV/TSV
		self.__escapeHTML = None # HTM/HTML
		self.__dumpJSON = None # JSON
		self.__escapeTEX = None # TEX
		self.__columnsTEX = None # TEX
		self.__WorkbookXLS = None #XLS
		self.__styleXLSColumns = None # XLS
		self.__styleXLSValues = None # XLS
		self.__WorkbookXLSX = None # XLSX
		self.__alignmentXLSX = None # XLSX
		self.__fontXLSXColumns = None # XLSX
		self.__fontXLSXValues = None # XLSX
		self.__columnsXML = None # XML
		self.__dumpYAML = None # YAML/YML
	def __handleFolder(self:object) -> bool:
		if not self.__folderPath:
			return True
		elif os.path.exists(self.__folderPath):
			return os.path.isdir(self.__folderPath)
		else:
			try:
				os.makedirs(self.__folderPath)
				return True
			except:
				return False
	def save(self:object, results:tuple|list) -> bool:
		if isinstance(results, (tuple, list)) and all(isinstance(result, (tuple, list)) and all(r is None or isinstance(r, (float, int, str)) for r in result) for result in results):
			if self.__outputFilePath:
				if self.__handleFolder():
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
										self.__escapeHTML = __import__("html").escape
									with open(self.__outputFilePath, "w", newline = "", encoding = self.__encoding) as f:
										f.write("<!DOCTYPE html>{0}<html>{0}\t<head>{0}\t\t<title>{1}</title>{0}".format(os.linesep, Parser.getSchemeName()))
										f.write("\t\t<style>{0}\t\t\ttable {{{0}\t\t\t\twidth: 80%;{0}\t\t\t\tmargin: 20px auto;{0}".format(os.linesep))
										f.write("\t\t\t\tborder-collapse: collapse;{0}\t\t\t\tfont-family: \'Times New Roman\', serif;{0}".format(os.linesep))
										f.write("\t\t\t\tborder-top: 2px solid #000;{0}\t\t\t\tborder-bottom: 2px solid #000;{0}\t\t\t}}{0}".format(os.linesep))
										f.write("\t\t\tth, td {{{0}\t\t\t\tborder: none;{0}\t\t\t\tpadding: 8px 12px;{0}".format(os.linesep))
										f.write("\t\t\t\ttext-align: center;{0}\t\t\t}}{0}\t\t\tthead tr {{{0}".format(os.linesep))
										f.write("\t\t\t\tborder-bottom: 1.5px solid #000;{0}\t\t\t}}{0}\t\t\tth {{{0}\t\t\t\tfont-weight: bold;{0}".format(os.linesep))
										f.write("\t\t\t}}{0}\t\t\tcaption {{{0}\t\t\t\tfont-size: 1.5em;{0}\t\t\t\tmargin: 10px;{0}".format(os.linesep))
										f.write("\t\t\t\tfont-weight: bold;{0}\t\t\t\tcolor: #333;{0}\t\t\t\tcaption-side: top;{0}\t\t\t}}{0}".format(os.linesep))
										f.write("\t\t</style>{0}\t</head>{0}\t<body>{0}\t\t<table>{0}".format(os.linesep))
										f.write("\t\t\t<caption>{1}</caption>{0}\t\t\t<thead>{0}\t\t\t\t<tr>{0}".format(os.linesep, Parser.getSchemeName()))
										for column in self.__columns:
											f.write("\t\t\t\t\t<th>{0}</th>{1}".format(self.__escapeHTML(column, quote = True), os.linesep))
										f.write("\t\t\t\t</tr>{0}\t\t\t</thead>{0}\t\t\t<tbody>{0}".format(os.linesep))
										for result in results:
											f.write("\t\t\t\t<tr>{0}".format(os.linesep))
											for r in result:
												f.write("\t\t\t\t\t<td>{0}</td>{1}".format(																									\
													self.__escapeHTML("{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else str(r), quote = True), os.linesep	\
												))
											f.write("\t\t\t\t</tr>{0}".format(os.linesep))
										f.write("\t\t\t</tbody>{0}\t\t</table>{0}\t</body>{0}</html>".format(os.linesep))
								elif "JSON" == self.__extensionName:
									if self.__dumpJSON is None:
										self.__dumpJSON = __import__("json").dump
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										self.__dumpJSON({"columns":self.__columns, "results":results}, f, indent = "\t")
								elif "TEX" == self.__extensionName:
									if self.__columnsTEX is None:
										if self.__escapeTEX is None:
											self.__escapeTEX = lambda x:"\\textbackslash{}".join(																			\
												s.replace("&", "\\&").replace("%", "\\%").replace("$", "\\$").replace("#", "\\#").replace("_", "\\_").replace("{", "\\{")	\
												.replace("}", "\\}").replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}") for s in str(x).split("\\")		\
											)
										self.__columnsTEX = tuple(self.__escapeTEX(column) for column in self.__columns)
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										maxLength = max(len(self.__columnsTEX) if isinstance(self.__columnsTEX, (tuple, list)) else 0, max(len(result) for result in results))
										f.write("\\documentclass[a4paper]{{article}}{0}\\setlength{{\\parindent}}{{0pt}}{0}".format(os.linesep))
										f.write("\\usepackage{{graphicx}}{0}\\usepackage{{booktabs}}{0}\\usepackage{{rotating}}{0}{0}".format(os.linesep))
										f.write("\\begin{{document}}{0}{0}\\begin{{sidewaystable}}{0}\t\\caption{{The comparison results. }}{0}".format(os.linesep))
										f.write("\t\\centering{0}\t\\resizebox{{\\textwidth}}{{!}}{{%{0}\t\t\\begin{{tabular}}{{".format(os.linesep))
										f.write("c" * maxLength)
										f.write("}}{0}\t\t\t\\toprule{0}\t\t\t\t".format(os.linesep))
										if isinstance(self.__columnsTEX, (tuple, list)) and self.__columnsTEX:
											f.write(" & ".join("\\textbf{{{0}}}".format(column) for column in self.__columnsTEX))
											if len(self.__columnsTEX) < maxLength:
												f.write(" & \\textbf{~}" * (maxLength - len(result)))
										else:
											f.write(" & ".join(("\\textbf{~}", ) * maxLength))
										f.write(" \\\\{0}\t\t\t\\midrule{0}".format(os.linesep))
										for result in results:
											if result:
												f.write("\t\t\t\t")
												f.write(" & ".join((																	\
													"${0}$" if isinstance(r, int) else "${{0:.{0}f}}$".format(self.__decimalPlace)		\
												).format(r) if isinstance(r, (float, int)) else self.__escapeTEX(r) for r in result))
												if len(result) < maxLength:
													f.write(" & ~" * (maxLength - len(result)))
												f.write(" \\\\" + os.linesep)
										f.write("\t\t\t\\bottomrule{0}\t\t\\end{{tabular}}{0}\t}}{0}\t\\label{{tab:comparison}}{0}".format(os.linesep))
										f.write("\\end{{sidewaystable}}{0}{0}\\end{{document}}".format(os.linesep))
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
									workbook = self.__WorkbookXLSX()
									worksheet = workbook.active
									for columnIndex, columnName in enumerate(self.__columns, start = 1):
										cell = worksheet.cell(row = 1, column = columnIndex, value = columnName)
										cell.alignment = self.__alignmentXLSX
										cell.font = self.__fontXLSXColumns
									for i, result in enumerate(results, start = 2):
										for j, r in enumerate(result, start = 1):
											cell = worksheet.cell(row = i, column = j, value = "{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r)
											cell.alignment = self.__alignmentXLSX
											cell.font = self.__fontXLSXValues
									worksheet.freeze_panes = "A2"
									workbook.save(self.__outputFilePath)
								elif "XML" == self.__extensionName:
									if self.__columnsXML is None:
										self.__columnsXML = {}
										for columnIndex, columnName in enumerate(self.__columns):
											columnName = columnName.replace("\'", "Prime")
											startingIndex, stringLength = 0, len(columnName)
											while startingIndex < stringLength:
												ch = columnName[startingIndex]
												if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z' or '_' == ch:
													break
												else:
													startingIndex += 1
											endingIndex = startingIndex + 1
											while endingIndex < stringLength:
												ch = columnName[endingIndex]
												if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z' or '0' <= ch <= '9' or ch in ('_', '-'):
													endingIndex += 1
												else:
													break
											filteredColumnName = columnName[startingIndex:endingIndex]
											self.__columnsXML[columnIndex] = filteredColumnName if filteredColumnName else "_"
									with open(self.__outputFilePath, "w", newline = "", encoding = self.__encoding) as f:
										f.write("<?xml version=\'1.0\' encoding=\'{0}\'?>{1}<data>{1}".format(self.__encoding, os.linesep))
										for result in results:
											f.write("\t<row>" + os.linesep)
											for rIndex, r in enumerate(result):
												tag = self.__columnsXML.get(rIndex, "_")
												if isinstance(r, float):
													rString = "{{0:.{0}f}}".format(self.__decimalPlace).format(r)
												else:
													rString = str(r).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
												f.write(("\t\t<{0}>{1}</{0}>{2}" if rString else "\t\t<{0}/>{2}").format(tag, rString, os.linesep))
											f.write("\t</row>" + os.linesep)
										f.write("</data>")
								elif self.__extensionName in ("YAML", "YML"):
									if self.__dumpYAML is None:
										self.__dumpYAML = __import__("yaml").dump
										__import__("yaml").add_representer(float, lambda dumper, x:dumper.represent_scalar("tag:yaml.org,2002:float", "{{0:.{0}f}}".format(self.__decimalPlace).format(x)))
										__import__("yaml").add_representer(tuple, lambda dumper, x:dumper.represent_mapping("tag:yaml.org,2002:map", x))
									vector, columnLength = [], len(self.__columns)
									for result in results:
										d, resultLength = {}, len(result)
										for index in range(max(columnLength, resultLength)):
											key, value = self.__columns[index] if index < columnLength else None, result[index] if index < resultLength else None
											if key in d:
												if isinstance(key, list):
													d[key].append(value)
												else:
													d[key] = [d[key], value]
											else:
												d[key] = value
										vector.append(tuple(d.items()))
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										self.__dumpYAML(vector, f)
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
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
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
	def Setup(self:object, m:int = 10, n:int = 10, d:int = 10) -> tuple: # $\textbf{Setup}(m, n, d) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(m, int) and m >= 1:
			self.__m = m
		else:
			self.__m = 10
			print("Setup: The variable $m$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		if isinstance(n, int) and n >= 1:
			self.__n = n
		else:
			self.__n = 10
			print("Setup: The variable $n$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		if isinstance(d, int) and d >= 1:
			self.__d = d
		else:
			self.__d = 10
			print("Setup: The variable $d$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		
		# Scheme #
		g1 = self.__group.init(G1, 1) # $g_1 \gets 1_{\mathbb{G}_1}$
		g2 = self.__group.init(G2, 1) # $g_2 \gets 1_{\mathbb{G}_2}$
		s = self.__group.random(ZR) # generate $s \in \mathbb{Z}_p^*$ randomly
		SVec = tuple(g2 ** (s ** i) for i in range(self.__m + self.__d + 1)) # $\vec{S} \gets (S_0, S_1, \cdots, S_{m + d}) = (g_2^{s_0}, g_2^{s_1}, \cdots, g_2^{s^{m + d}})$
		SPrime = g1 ** s # $S' \gets g_1^s \in \mathbb{G}_1$
		if 512 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $H: \mathbb{G}_T \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
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
			print("Sender: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_YVec, tuple) and len(_YVec) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in _YVec): # hybrid check
			YVec = _YVec
		else:
			YVec = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Sender: The variable $\\vec{Y}$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
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
			print("Receiver: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_XVec, tuple) and len(_XVec) == self.__m and all(isinstance(ele, Element) and ele.type == ZR for ele in _XVec): # hybrid check
			XVec = _XVec
		else:
			XVec = tuple(self.__group.random(ZR) for _ in range(self.__m))
			print("Receiver: The variable $\\vec{X}$ should be a tuple containing $m$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
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
			print("Cloud1: The variable $\\vec{{T}} || \\vec{{T}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_R, Element) and _R.type == G2: # type check
			R = _R
		else:
			R = self.__group.random(G2)
			print("Cloud1: The variable $R$ should be an element of $\\mathbb{G}_2$ but it is not, which has been generated randomly. ")
		
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
			print("Cloud2: The variable $\\vec{{U}} || \\vec{{U}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_RPrimeVec, tuple) and len(_RPrimeVec) == self.__m + self.__d and all(isinstance(ele, Element) and ele.type == G2 for ele in _RPrimeVec): # hybrid check
			RPrimeVec = _RPrimeVec
		else:
			RPrimeVec = tuple(self.__group.random(G2) for _ in range(self.__m + self.__d))
			print("Cloud2: The variable $\\vec{{R}}'$ should be a tuple containing $m + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__m, self.__d, self.__m + self.__d))
		
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
			print("Verify: The variable $\\vec{{K}}$ should be a tuple containing $(m + d)(n + d) = {0}$ integers but it is not, which has been generated randomly. ".format((self.__m + self.__d) * (self.__n + self.__d)))
		if isinstance(_WVec, tuple) and len(_WVec) == self.__n + self.__d and all(isinstance(ele, int) for ele in _WVec): # hybrid check
			WVec = _WVec
		else:
			WVec = self.Cloud1(tuple(self.__group.random(G1) for _ in range(self.__n + self.__d)), self.__group.random(G2))
			print("Verify: The variable $\\vec{{W}}$ should be a tuple containing $n + d = {0} + {1} = {2}$ integers but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		
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


def conductScheme(curveParameter:tuple|list|str, m:int = 10, n:int = 10, d:int = 10, run:int|None = None) -> list:
	# Begin #
	if isinstance(m, int) and isinstance(n, int) and isinstance(d, int) and m >= 1 and n >= 1 and d >= 1:
		try:
			if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int):
				if curveParameter[1] >= 1:
					group = PairingGroup(curveParameter[0], secparam = curveParameter[1])
				else:
					group = PairingGroup(curveParameter[0])
			else:
				group = PairingGroup(curveParameter)
		except BaseException as e:
			if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int):
				print("curveParameter =", curveParameter[0])
				if curveParameter[1] >= 1:
					print("secparam =", curveParameter[1])
			elif isinstance(curveParameter, str):
				print("curveParameter =", curveParameter)
			else:
				print("curveParameter = Unknown")
			print("m =", m)
			print("n =", n)
			print("d =", d)
			if isinstance(run, int) and run >= 1:
				print("run =", run)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																																																			\
				([curveParameter[0], curveParameter[1]] if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int) else [(curveParameter if isinstance(curveParameter, str) else None), None])		\
				+ [m, n, d, run if isinstance(run, int) and run >= 1 else None] + [False] * 3 + ["N/A"] * 19																																													\
			)
	else:
		print("Is the system valid? No. The parameters $m$, $n$, and $d$ should be three positive integers. ")
		return (																																																																			\
			([curveParameter[0], curveParameter[1]] if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int) else [(curveParameter if isinstance(curveParameter, str) else None), None])		\
			+ [m if isinstance(m, int) else None, n if isinstance(n, int) else None, d if isinstance(d, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 3 + ["N/A"] * 19																					\
		)
	print("curveParameter =", group.groupType())
	print("secparam =", group.secparam)
	print("m =", m)
	print("n =", n)
	print("d =", d)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeVLPSICA = SchemeVLPSICA(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeVLPSICA.Setup(m, n, d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Sender #
	startTime = perf_counter()
	vVec = tuple(group.random(ZR) for _ in range(d))
	YVec = tuple(group.random(ZR) for _ in range(n))
	TTPrime, UUPrime = schemeVLPSICA.Sender(vVec, YVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Receiver #
	startTime = perf_counter()
	XVec = tuple(group.random(ZR) for _ in range(m))
	R, RPrimeVec = schemeVLPSICA.Receiver(vVec, XVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Cloud1 #
	startTime = perf_counter()
	WVec = schemeVLPSICA.Cloud1(TTPrime, R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Cloud2 #
	startTime = perf_counter()
	KVec = schemeVLPSICA.Cloud2(UUPrime, RPrimeVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Verify #
	startTime = perf_counter()
	result = schemeVLPSICA.Verify(KVec, WVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, isinstance(result, int)]
	spaceRecords = [																																											\
		schemeVLPSICA.getLengthOf(group.random(ZR)), schemeVLPSICA.getLengthOf(group.random(G1)), schemeVLPSICA.getLengthOf(group.random(G2)), schemeVLPSICA.getLengthOf(group.random(GT)), 	\
		schemeVLPSICA.getLengthOf(mpk), schemeVLPSICA.getLengthOf(msk), schemeVLPSICA.getLengthOf(TTPrime), schemeVLPSICA.getLengthOf(UUPrime), schemeVLPSICA.getLengthOf(R), 					\
		schemeVLPSICA.getLengthOf(RPrimeVec), schemeVLPSICA.getLengthOf(WVec), schemeVLPSICA.getLengthOf(KVec)																					\
	]
	del schemeVLPSICA
	print("Verify:", result)
	print("Is the scheme passed (result != False)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, m, n, d, run if isinstance(run, int) and run >= 1 else None] + booleans + timeRecords + spaceRecords

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		if any((PairingGroup is None, G1 is None, G2 is None, GT is None, ZR is None, pair is None, Element is None)):
			parser.disableConsoleEchoes()
			print("The environment of the Python ``charm`` library is not handled correctly. ")
			print("Please refer to https://github.com/JHUISI/charm if necessary. ")
			errorLevel = EOF
		else:
			outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
			parser.disableConsoleEchoes()
			print("The execution has started. ")
			print()
			
			# Parameters #
			curveParameters = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
			queries = ("curveParameter", "secparam", "m", "n", "d", "runCount")
			validators = ("isSystemValid", "isSchemePassed")
			metrics = (																						\
				"Setup (s)", "Sender (s)", "Receiver (s)", "Cloud1 (s)", "Cloud 2(s)", "Verify (s)",		\
				"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 				\
				"mpk (B)", "msk (B)", "(T, T') (B)", "(U, U') (B)", "R (B)", "R' (B)", "W (B)", "K (B)"		\
			)
			
			# Scheme #
			columns, qLength, results = queries + validators + metrics, len(queries), []
			length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for m in range(5, 31, 5):
						for n in range(5, 31, 5):
							for d in range(5, 31, 5):
								averages = conductScheme(curveParameter, m = m, n = n, d = d, run = 1)
								for run in range(2, runCount + 1):
									result = conductScheme(curveParameter, m = m, n = n, d = d, run = run)
									for idx in range(qLength, qvLength):
										averages[idx] += result[idx]
									for idx in range(qvLength, length):
										averages[idx] = averages[idx] + result[idx] if isinstance(averages[idx], (float, int)) and averages[idx] > 0 and result[idx] > 0 else "N/A"
								averages[avgIndex] = runCount
								for idx in range(qvLength, length):
									if isinstance(averages[idx], (float, int)) and averages[idx] > 0:
										averages[idx] /= runCount
										if averages[idx].is_integer():
											averages[idx] = int(averages[idx])
									else:
										averages[idx] = "N/A"
								results.append(averages)
								saver.save(results)
								print()
			except KeyboardInterrupt:
				print()
				print("The experiments were interrupted by users. Saved results are retained. ")
			except BaseException as e:
				print()
				print("The experiments were interrupted by {0}. Saved results are retained. ".format(repr(e)))
			errorLevel = EXIT_SUCCESS if results and all(all(																								\
				tuple(r == runCount for r in result[qLength:qvLength]) + tuple(isinstance(r, (float, int)) and r > 0 for r in result[qvLength:length])	\
			) for result in results) else EXIT_FAILURE
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