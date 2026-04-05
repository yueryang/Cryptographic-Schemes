import os
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, GT, ZR, pair, Element = (None, ) * 6
from codecs import lookup
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from random import shuffle
from time import perf_counter, sleep
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Parser:
	__SchemeName = "SchemeFuzzyME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is a possible implementation of the Fuzzy-ME cryptographic scheme in Python programming language based on the Python charm library. ")
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

class SchemeFuzzyME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		try:
			pair(self.__group.random(G1), self.__group.random(G1))
		except:
			self.__group = PairingGroup("SS512", secparam = self.__group.secparam)
			print("Init: This scheme is only applicable to symmetric groups of prime orders. The curve name has been defaulted to \"SS512\". ")
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__n = 30
		self.__d = 10
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
	def __computePolynomial(self:object, x:Element|int|float, coefficients:tuple|list) -> Element|int|float|None:
		if isinstance(coefficients, (tuple, list)) and coefficients and (															\
			isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)	\
			or isinstance(x, (int, float)) and all(isinstance(coefficient, (int, float)) for coefficient in coefficients)						\
		):
			n, eleResult = len(coefficients) - 1, coefficients[0]
			for i in range(1, n):
				eResult = x
				for _ in range(i - 1):
					eResult *= x
				eleResult += coefficients[i] * eResult
			eResult = x
			for _ in range(n - 1):
				eResult *= x
			eleResult += eResult
			return eleResult
		else:
			return None
	def Setup(self:object, n:int = 30, d:int = 10) -> tuple: # $\textbf{Setup}(n, d) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(n, int) and n >= 1: # boundary check
			self.__n = n
		else:
			self.__n = 30
			print("Setup: The variable $n$ should be a positive integer but it is not, which has been defaulted to $30$. ")
		if isinstance(d, int) and d >= 2: # boundary check
			self.__d = d
		else:
			self.__d = 10
			print("Setup: The variable $d$ should be a positive integer not smaller than $2$ but it is not, which has been defaulted to $10$. ")
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		g2, g3 = self.__group.random(G1), self.__group.random(G1) # generate $g_2, g_3 \in \mathbb{G}_1$ randomly
		tVec = tuple(self.__group.random(G1) for _ in range(n + 1)) # generate $\vec{t} = (t_1, t_2, \cdots, t_{n + 1}) \in \mathbb{G}_1^{n + 1}$ randomly
		lVec = tuple(self.__group.random(G1) for _ in range(n + 1)) # generate $\vec{l} = (l_1, l_2, \cdots, l_{n + 1}) \in \mathbb{G}_1^{n + 1}$ randomly
		alpha, beta, theta1, theta2, theta3, theta4 = self.__group.random(ZR, 6) # generate $\alpha, \beta, \theta_1, \theta_2, \theta_3, \theta_4 \in \mathbb{Z}_r$ randomly
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		eta1 = g ** theta1 # $\eta_1 \gets g^{\theta_1}$
		eta2 = g ** theta2 # $\eta_2 \gets g^{\theta_2}$
		eta3 = g ** theta3 # $\eta_3 \gets g^{\theta_3}$
		eta4 = g ** theta4 # $\eta_4 \gets g^{\theta_4}$
		Y1 = pair(g1, g2) ** (theta1 * theta2) # $Y_1 \gets \hat{e}(g_1, g_2)^{\theta_1 \theta_2}$
		Y2 = pair(g3, g ** beta) ** (theta1 * theta2) # $Y_2 \gets \hat{e}(g_3, g^\beta)^{\theta_1 \theta_2}$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \to \mathbb{G}_1$
		self.__mpk = (g1, g2, g3, Y1, Y2, tVec, lVec, eta1, eta2, eta3, eta4, H1) # $ \textit{mpk} \gets (g_1, g_2, g_3, Y_1, Y_2, \vec{t}, \vec{l}, \eta_1, \eta_2, \eta_3, \eta_4, H_1)$
		self.__msk = (alpha, beta, theta1, theta2, theta3, theta4) # $\textit{msk} \gets (\alpha, \beta, \theta_1, \theta_2, \theta_3, \theta_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, SA:tuple) -> tuple: # $\textbf{EKGen}(S_A) \to \textit{ek}_{S_A}$
		# Checks #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(SA, tuple) and len(SA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SA): # hybrid check
			S_A = SA
		else:
			S_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKGen: The variable $S_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g3, lVec = self.__mpk[2], self.__mpk[6]
		beta, theta1, theta2 = self.__msk[1], self.__msk[2], self.__msk[3]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \to g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta_{i, N}(x)}$
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		rVec = tuple(self.__group.random(ZR) for _ in S_A) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		EVec = tuple(g3 ** (q(S_A[i]) * theta1 * theta2) * H(S_A[i]) ** rVec[i] for i in range(len(S_A))) # $E_i \gets g_3^{q(a_i) \theta_1 \theta_2} H(a_i)^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		eVec = tuple(g ** rVec[i] for i in range(len(S_A))) # $e_i \gets g^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		ek_S_A = (EVec, eVec) # $\textit{ek}_{S_A} \gets \{E_i, e_i\}_{a_i \in S_A}$
		
		# Return #
		return ek_S_A # \textbf{return} $\textit{ek}_{S_A}$
	def DKGen(self:object, SB:tuple, PA:tuple) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \to \textit{dk}_{\textit{id}_R}$
		# Checks #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(SB, tuple) and len(SB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SB): # hybrid check
			S_B = SB
		else:
			S_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $S_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(PA, tuple) and len(PA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in PA): # hybrid check
			P_A = PA
		else:
			P_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $P_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, g3, tVec, lVec = self.__mpk[1], self.__mpk[2], self.__mpk[5], self.__mpk[6]
		alpha, beta, theta1, theta2, theta3, theta4 = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \to g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta_{i, N}(x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \to g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta_{i, N}(x)}$
		gamma = self.__group.random(ZR) # generate $\gamma \in \mathbb{Z}_r$ randomly
		G_ID = self.__group.random(G1) # generate $G_{\textit{ID}} \in \mathbb{G}_1$ randomly
		coefficientsForF = (alpha, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		f = lambda x:self.__computePolynomial(x, coefficientsForF) # generate a $(d - 1)$ degree polynominal $f(x)$ s.t. $f(0) = \alpha$ randomly
		coefficientsForH = (gamma, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		h = lambda x:self.__computePolynomial(x, coefficientsForH) # generate a $(d - 1)$ degree polynominal $h(x)$ s.t. $h(0) = \gamma$ randomly
		coefficientsForQPrime = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		qPrime = lambda x:self.__computePolynomial(x, coefficientsForQPrime) # generate a $(d - 1)$ degree polynominal $q'(x)$ s.t. $q'(0) = \beta$ randomly
		k1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_1 = (k_{1, 1}, k_{1, 2}, \cdots, k_{1, n}) \in \mathbb{Z}_r^n$ randomly
		k2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_2 = (k_{2, 1}, k_{2, 2}, \cdots, k_{2, n}) \in \mathbb{Z}_r^n$ randomly
		rPrime1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r}'_1 = (r'_{1, 1}, r'_{1, 2}, \cdots, r'_{1, n}) \in \mathbb{Z}_r^n$ randomly
		rPrime2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r}'_2 = (r'_{2, 1}, r'_{2, 2}, \cdots, r'_{2, n}) \in \mathbb{Z}_r^n$ randomly
		dk_S_B_0 = tuple(g ** (k1Vec[i] * theta1 * theta2 + k2Vec[i] * theta3 * theta4) for i in range(self.__n)) # $\textit{dk}_{S_{B_{0, i}}} \gets g^{k_{1, i} \theta_1 \theta_2 + k_{2, i} \theta_3 \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_1 = tuple(																												\
			g2 ** (-f(S_B[i]) * theta2) * G_ID ** (-h(S_B[i]) * theta2) * T(S_B[i]) ** (-k1Vec[i] * theta2) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{1, i}}} \gets g_2^{-f(b_i) \theta_2} (G_{\textit{ID}})^{-h(b_i) \theta_2} [T(b_i)]^{-k_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_2 = tuple(																												\
			g2 ** (-f(S_B[i]) * theta1) * G_ID ** (-h(S_B[i]) * theta1) * T(S_B[i]) ** (-k1Vec[i] * theta1) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{2, i}}} \gets g_2^{-f(b_i) \theta_1} (G_{\textit{ID}})^{-h(b_i) \theta_1} [T(b_i)]^{-k_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_3 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{S_{B_{3, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_4 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{S_{B_{4, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B = (dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4) # $\textit{dk}_{S_B} \gets (\textit{dk}_{S_{B_0}}, \textit{dk}_{S_{B_1}}, \textit{dk}_{S_{B_2}}, \textit{dk}_{S_{B_3}}, \textit{dk}_{S_{B_4}})$
		dk_P_A_0 = tuple(g ** (rPrime1Vec[i] * theta1 * theta2 + rPrime2Vec[i] * theta3 * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{0, i}}} \gets g^{r'_{1, i} \theta_1 \theta_2 + r'_{i, 2} \theta_3 \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_1 = tuple(																															\
			g2 ** (-2 * qPrime(P_A[i]) * theta2) * G_ID ** (h(P_A[i]) * theta2) * H(P_A[i]) ** (-rPrime1Vec[i] * theta2) for i in range(self.__n)	\
		) # $\textit{dk}_{P_{A_{1, i}}} \gets g_2^{-2q'(a_i) \theta_2} (G_{\textit{ID}})^{h(a_i \theta_2)} H(a_i)^{-r'_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_2 = tuple(																															\
			g2 ** (-2 * qPrime(P_A[i]) * theta1) * G_ID ** (h(P_A[i]) * theta1) * H(P_A[i]) ** (-rPrime1Vec[i] * theta1) for i in range(self.__n)	\
		) # $\textit{dk}_{P_{A_{2, i}}} \gets g_2^{-2q'(a_i) \theta_1} (G_{\textit{ID}})^{h(a_i \theta_1)} H(a_i)^{-r'_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_3 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_4 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A = (dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4) # $\textit{dk}_{P_A} \gets (\textit{dk}_{P_{A_0}}, \textit{dk}_{P_{A_1}}, \textit{dk}_{P_{A_2}}, \textit{dk}_{P_{A_3}}, \textit{dk}_{P_{A_4}})$
		dk_SBPA = (dk_S_B, dk_P_A) # $\textit{dk}_{S_B, P_A} \gets (\textit{dk}_{S_B}, \textit{dk}_{P_A})$
		
		# Return #
		return dk_SBPA # \textbf{return} $\textit{dk}_{S_B, P_A}$
	def Encryption(self:object, ekSA:tuple, SA:tuple, PB:tuple, message:Element) -> tuple: # $\textbf{Encryption}(\textit{ek}_{S_A}, S_A, P_B, M) \to \textit{CT}$
		# Checks #
		if not self.__flag:
			print("Encryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Encryption`` subsequently. ")
			self.Setup()
		if isinstance(SA, tuple) and len(SA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SA): # hybrid check
			S_A = SA
			if isinstance(ekSA, tuple) and len(ekSA) == 2 and isinstance(ekSA[0], tuple) and isinstance(ekSA[1], tuple) and len(ekSA[0]) == len(ekSA[1]) == self.__n: # hybrid check
				ek_S_A = ekSA
			else:
				ek_S_A = self.EKGen(S_A)
				print("Encryption: The variable $\\textit{ek}_{S_A}$ should be a tuple containing 2 tuples but it is not, which has been generated accordingly. ")
		else:
			S_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Encryption: The variable $S_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_S_A = self.EKGen(S_A)
			print("Encryption: The variable $\\textit{ek}_{S_A}$ has been generated accordingly. ")
		if isinstance(PB, tuple) and len(PB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in PB): # hybrid check
			P_B = PB
		else:
			P_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Encryption: The variable $P_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Encryption: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, g3, Y1, Y2, tVec, lVec, eta1, eta2, eta3, eta4, H1 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11]
		EVec, eVec = ek_S_A
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \to g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta_{i, N}(x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \to g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta_{i, N}(x)}$
		s, s1, s2, tau = self.__group.random(ZR, 4) # generate $s, s_1, s_2, \tau \in \mathbb{Z}_r$ randomly
		K_s = Y1 ** s # $K_s \gets Y_1^s$
		K_l = Y2 ** s * pair(g3, g ** (-tau)) # $K_l \gets Y_2^s \cdot \hat{e}(g_3, g^{-\tau})$
		C0 = M * K_s * K_l # $C_0 \gets M \cdot K_s \cdot K_l$
		C1 = eta1 ** (s - s1) # $C_1 \gets \eta_1^{s - s_1}$
		C2 = eta2 ** s1 # $C_2 \gets \eta_2^{s_1}$
		C3 = eta3 ** (s - s2) # $C_3 \gets \eta_3^{s - s_2}$
		C4 = eta4 ** s2 # $C_4 \gets \eta_4^{s_2}$
		C1Vec = tuple(T(P_B[i]) ** s for i in range(len(P_B))) # $C_{1, i} \gets T(b_i)^s, \forall b_i \in P_B$
		C2Vec = tuple(H(S_A[i]) ** s for i in range(len(S_A))) # $C_{2, i} \gets H(a_i)^s, \forall a_i \in S_A$
		coefficients = (tau, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		l = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $l(x)$ s.t. $l(0) = \tau$ randomly
		xiVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{\xi} = (\xi_1, \xi_2, \cdots, \xi_n) \in \mathbb{Z}_r^n$ randomly
		chiVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{\chi} = (\chi_1, \chi_2, \cdots, \chi_n) \in \mathbb{Z}_r^n$ randomly
		C3Vec = tuple(eVec[i] * g ** xiVec[i] for i in range(self.__n)) # $C_{3, i} \gets e_i \cdot g^{\xi_i}, \forall i \in \{1, 2, \cdots, n\}$
		C4Vec = tuple(g ** chiVec[i] for i in range(self.__n)) # $C_{4, i} \gets g^{\chi_i}, \forall i \in \{1, 2, \cdots, n\}$
		C5Vec = tuple(EVec[i] ** s * g3 ** l(S_A[i]) * H(S_A[i]) ** (s * xiVec[i]) * H1(																	\
			self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)	\
			+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
		) for i in range(self.__n)) # $C_{5, i} \gets E_i^s \cdot g_3^{l(a_i)} H(a_i)^{s \cdot \xi_i} \cdot H_1(C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i})^{\chi_i}$
		CT = (C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec) # $\textit{CT} \gets (C_0, C_1, C_2, C_3, C_4, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Decryption(self:object, dkSBPA:tuple, SA:tuple, PA:tuple, SB:tuple, PB:tuple, cipherText:tuple) -> Element|bool: # $\textbf{Decryption}(\textit{dk}_{S_B, P_A}, S_A, P_A, S_B, P_B, \textit{CT}) \to M$
		# Checks #
		if not self.__flag:
			print("Decryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Decryption`` subsequently. ")
			self.Setup()
		if (																																								\
			isinstance(SA, tuple) and isinstance(PA, tuple) and isinstance(SB, tuple) and isinstance(PB, tuple) and len(SA) == len(PA) == len(SA) == len(SB) == self.__n	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SA) and all(isinstance(ele, Element) and ele.type == ZR for ele in PA)							\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SB) and all(isinstance(ele, Element) and ele.type == ZR for ele in PB)							\
		): # hybrid check
			S_A, P_A, S_B, P_B = SA, PA, SB, PB
			if (																																								\
				isinstance(dkSBPA, tuple) and len(dkSBPA) == 2 and isinstance(dkSBPA[0], tuple) and isinstance(dkSBPA[1], tuple) and len(dkSBPA[0]) == len(dkSBPA[1]) == 5		\
				and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[0]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[1])		\
			): # hybrid check
				dk_SBPA = dkSBPA
			else:
				dk_SBPA = self.DKGen(S_B, P_A)
				print("Decryption: The variable $\\textit{dk}_{S_B, P_A}$ should be a tuple containing 2 tuples but it is not, which has been generated accordingly. ")
		else:
			S_A, P_A = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			S_B, P_B = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Decryption: Each of the variables $S_A$, $P_A$, $S_B$, and $P_B$ should be a tuple containing 4 elements of $\\mathbb{Z}_r$ but at least one of them is not, all of which have been generated randomly. ")
			dk_SBPA = self.DKGen(S_B, P_A)
			print("Decryption: The variable $\\textit{dk}_{S_B, P_A}$ has been generated accordingly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 10 and all(isinstance(ele, Element) for ele in cipherText[:5]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in cipherText[5:]): # hybrid check
			CT = cipherText
		else:
			CT = self.Enc(self.EKGen(S_A), S_A, P_B, self.__group.random(GT))
			print("Decryption: The variable $\\textit{CT}$ should be a tuple containing 5 elements and 5 tuples but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[11]
		dk_S_B, dk_P_A = dk_SBPA
		dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4 = dk_S_B
		dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4 = dk_P_A
		C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec = CT
		
		# Scheme #
		WAPrime = set(S_A).intersection(P_A) # $W'_A \gets S_A \cap P_A$
		WBPrime = set(S_B).intersection(P_B) # $W'_B \gets S_B \cap P_B$
		if len(WAPrime) >= self.__d and len(WBPrime) >= self.__d: # \textbf{if} $|W'_A| \leqslant d \land |W'_B| \leqslant d$ \textbf{then}
			WA = tuple(WAPrime)[:self.__d] # \quad generate $W_A \subset W'_A$ s.t. $|W_A| = d$ randomly
			WB = tuple(WBPrime)[:self.__d] # \quad generate $W_B \subset W'_B$ s.t. $|W_B| = d$ randomly
			g = self.__group.init(G1, 1) # \quad$g \gets 1_{\mathbb{G}_1}$
			Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # \quad$\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
			KsPrime = self.__product(tuple(( # \quad$K'_s \gets \prod\limits_{b_i \in W_B} (
				pair(C1Vec[i], dk_S_B_0[i]) * pair(C1, dk_S_B_1[i]) * pair(C2, dk_S_B_2[i]) # \hat{e}(C_{1, i}, \textit{dk}_{S_{B_{0, i}}}) \hat{e}(C_1, \textit{dk}_{S_{B_{1, i}}}) \hat{e}(C_2, \textit{dk}_{S_{B_{2, i}}})
				* pair(C3, dk_S_B_3[i]) * pair(C4, dk_S_B_4[i]) # \hat{e}(C_3, \textit{dk}_{S_{B_{3, i}}}) \hat{e}(C_4, \textit{dk}_{S_{B_{4, i}}})
			) ** Delta(S_B[i], WB, 0) for i in range(self.__n))) # )^{\Delta_{b_i, W_B}(0)}$
			CTVec = tuple(																																			\
				(																																					\
					self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)	\
					+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
				) for i in range(self.__n)																															\
			) # \quad$\textit{CT}_i \gets C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i}, \forall i \in \{1, 2, \cdots, n\}$
			KlPrime = self.__product(tuple( # \quad$K'_l \gets \prod\limits_{a_i \in W_A} 
				( # \left(
					(pair(C1Vec[i], dk_P_A_0[i]) * pair(C1, dk_P_A_1[i]) * pair(C2, dk_P_A_2[i])) # \frac{\hat{e}(C_{1, i}, \textit{dk}_{P_{A_{0, i}}}) \hat{e}(C_1, \textit{dk}_{P_{A_{1, i}}}) \hat{e}(C_2, \textit{dk}_{P_{A_{i, 2}}})}
					/ (pair(H1(CTVec[i]), C4Vec[i]) # {\hat{e}(H_1(\textit{CT}_i), C_{4, i}) \cdot \hat{e}(C_{3, i}, C_{2, i})}
					* pair(C3Vec[i], C2Vec[i])) * pair(C3, dk_P_A_3[i]) * pair(C4, dk_P_A_4[i]) * pair(C5Vec[i], g) # \cdot \hat{e}(C_3, \textit{dk}_{P_{A_{i, 3}}}) \hat{e}(C_4, \textit{dk}_{P_{A_{i, 4}}}) \hat{e}(C_{5, i}, g)
				) ** Delta(S_A[i], WA, 0) for i in range(self.__n) # \right)^{\Delta_{a_i, W_A}(0)}
			)) # $
			M = C0 * KsPrime * KlPrime # \quad$M \gets C_0 \cdot K'_s \cdot K'_l$
		else: # \textbf{else}
			M = False # \quad$M \gets \perp$
		# \textbf{end if}
		
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


def conductScheme(curveParameter:tuple|list|dict|str, n:int = 30, d:int = 10, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, nString, dString, runString = "N/A", 512, "N/A", "N/A", "N/A" # the default value of the security parameter in the Python charm library is 512
	isSystemValid, isSchemeCorrect = False, False
	timeSetup, timeEKGen, timeDKGen, timeEncryption, timeDecryption = ("N/A", ) * 5
	sizeZR, sizeG1G2, sizeGT = ("N/A", ) * 3
	sizeMpk, sizeMsk, sizeEkSA, sizeDkSBPA, sizeCT = ("N/A", ) * 5
	
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
	if isinstance(n, int):
		nString = n
	else:
		flag = False
	if isinstance(d, int):
		dString = d
	else:
		flag = False
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Curve: ({0}, {1})".format(curveName, securityParameter))
		print("$n$:", nString)
		print("$d$:", dString)
		print("run:", runString)
	if flag and n >= 1 and d >= 2:
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
	elif not isinstance(isVerbose, bool) or isVerbose:
		print("Is the system valid? No. The parameter $n$ should be a positive integer, and the parameter $d$ should be a positive integer not smaller than $2$. ")
		print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemeFuzzyME = SchemeFuzzyME(group)
		sizeZR, sizeG1G2, sizeGT = schemeFuzzyME.getLengthOf(group.random(ZR)), schemeFuzzyME.getLengthOf(group.random(G1)), schemeFuzzyME.getLengthOf(group.random(GT))
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemeFuzzyME.Setup(n = n, d = d)
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemeFuzzyME.getLengthOf(mpk), schemeFuzzyME.getLengthOf(msk)
		
		# EKGen #
		startTime = perf_counter()
		S_A = tuple(group.random(ZR) for _ in range(n))
		ek_S_A = schemeFuzzyME.EKGen(S_A)
		endTime = perf_counter()
		timeEKGen = endTime - startTime
		sizeEkSA = schemeFuzzyME.getLengthOf(ek_S_A)
		
		# DKGen #
		startTime = perf_counter()
		S_B = tuple(group.random(ZR) for _ in range(n))
		P_A = list(S_A)
		shuffle(P_A)
		P_A = P_A[:d] + list(group.random(ZR) for _ in range(n - d))
		shuffle(P_A)
		P_A = tuple(P_A)
		dk_SBPA = schemeFuzzyME.DKGen(S_B, P_A)
		endTime = perf_counter()
		timeDKGen = endTime - startTime
		sizeDkSBPA = schemeFuzzyME.getLengthOf(dk_SBPA)
		
		# Encryption #
		startTime = perf_counter()
		P_B = list(S_B)
		shuffle(P_B)
		P_B = P_B[:d] + list(group.random(ZR) for _ in range(n - d))
		shuffle(P_B)
		P_B = tuple(P_B)
		message = group.random(GT)
		CT = schemeFuzzyME.Encryption(ek_S_A, S_A, P_B, message)
		endTime = perf_counter()
		timeEncryption = endTime - startTime
		sizeCT = schemeFuzzyME.getLengthOf(CT)
		
		# Decryption #
		startTime = perf_counter()
		M = schemeFuzzyME.Decryption(dk_SBPA, S_A, P_A, S_B, P_B, CT)
		endTime = perf_counter()
		isSchemeCorrect = not isinstance(M, bool) and M == message
		timeDecryption = endTime - startTime
		
		# Destruction #
		del schemeFuzzyME
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Original:", message)
			print("Decrypted:", M)
			print("Is the scheme correct (M == message)? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Time:", (timeSetup, timeEKGen, timeDKGen, timeEncryption, timeDecryption))
			print("Space:", (sizeZR, sizeG1G2, sizeGT, sizeMpk, sizeMsk, sizeEkSA, sizeDkSBPA, sizeCT))
			print()
	
	# End #
	return [																\
		curveName, securityParameter, nString, dString, runString, 			\
		isSystemValid, isSchemeCorrect, 									\
		timeSetup, timeEKGen, timeDKGen, timeEncryption, timeDecryption, 	\
		sizeZR, sizeG1G2, sizeGT, 											\
		sizeMpk, sizeMsk, sizeEkSA, sizeDkSBPA, sizeCT						\
	]

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		if any((PairingGroup is None, G1 is None, GT is None, ZR is None, pair is None, Element is None)):
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
			curveParameters = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
			queries = ("curveParameter", "secparam", "n", "d", "runCount")
			validators = ("isSystemValid", "isSchemeCorrect")
			metrics = (																		\
				"Setup (s)", "EKGen (s)", "DKGen (s)", "Encryption (s)", "Decryption (s)", 	\
				"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 					\
				"mpk (B)", "msk (B)", "ek_S_A (B)", "dk_SBPA (B)", "CT (B)"					\
			)
			
			# Scheme #
			columns, qLength, results = queries + validators + metrics, len(queries), []
			length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for n in range(10, 31, 5):
						for d in range(5, n, 5):
							averages = conductScheme(curveParameter, n = n, d = d, run = 1)
							for run in range(2, runCount + 1):
								result = conductScheme(curveParameter, n = n, d = d, run = run)
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
			errorLevel = EXIT_SUCCESS if results and all(all(																							\
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