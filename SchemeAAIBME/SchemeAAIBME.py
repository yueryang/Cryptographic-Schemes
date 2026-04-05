import os
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, GT, ZR, pair, Element = (None, ) * 6
from codecs import lookup
from getpass import getpass
from random import shuffle
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
	__SchemeName = "SchemeAAIBME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the AA-IB-ME cryptographic scheme in Python programming language based on the Python charm library. ")
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

class SchemeAAIBME:
	__DefaultN, __DefaultK, __DefaultD = 30, 20, 10
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
		self.__n = SchemeAAIBME.__DefaultN
		self.__k = SchemeAAIBME.__DefaultK
		self.__d = SchemeAAIBME.__DefaultD
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
		if isinstance(coefficients, (tuple, list)) and coefficients and (																		\
			isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)		\
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
	def Setup(self:object, n:int = __DefaultN, k:int = __DefaultK, d:int = __DefaultD) -> tuple: # $\textbf{Setup}(n, k, d) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(n, int) and isinstance(k, int) and isinstance(d, int) and 1 <= d <= k <= n: # boundary check
			self.__n, self.__k, self.__d = n, k, d
		else:
			self.__n, self.__k, self.__d = SchemeAAIBME.__DefaultN, SchemeAAIBME.__DefaultK, SchemeAAIBME.__DefaultD
			print(																																							\
				"Setup: The variables $n$, $k$, and $d$ should be three positive integers satisfying $1 \\leqslant d \\leqslant k \\leqslant n$ but they are not, "			\
				+ "which has been defaulted to ${0}$, ${1}$, and ${2}$, respectively. ".format(SchemeAAIBME.__DefaultN, SchemeAAIBME.__DefaultK, SchemeAAIBME.__DefaultD)	\
			)
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		alpha, beta, t1, t2, t3, t4 = self.__group.random(ZR, 6) # generate $\alpha, \beta, t_1, t_2, t_3, t_4 \in \mathbb{Z}_r$ randomly
		g2, g3 = self.__group.random(G1), self.__group.random(G1) # generate $g_2, g_3 \in \mathbb{G}_1$ randomly
		TVec = tuple(self.__group.random(G1) for i in range(self.__n)) # generate $\bm{T} \gets (\bm{T}_1, \bm{T}_2, \cdots, \bm{T}_n) \in \mathbb{G}_1^n$ randomly
		TPrimeVec = tuple(self.__group.random(G1) for i in range(self.__n)) # generate $\bm{T}' \gets (\bm{T}'_1, \bm{T}'_2, \cdots, \bm{T}'_n) \in \mathbb{G}_1^n$ randomly
		uVec = tuple(self.__group.random(G1) for i in range(self.__n + 1)) # generate $\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n) \in \mathbb{G_1}^n$ randomly
		uPrimeVec = tuple(self.__group.random(G1) for i in range(self.__n + 1)) # generate $\bm{u}' \gets (\bm{u}'_0, \bm{u}'_1, \cdots, \bm{u}'_n) \in \mathbb{G}_1^n$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \to \mathbb{G}_1$
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		g1Prime = g ** beta # $g'_1 \gets g^\beta$
		Y1 = pair(g1, g2) ** (t1 * t2) # $Y_1 \gets e(g_1, g_2)^{t_1 t_2}$
		Y2 = pair(g3, g) ** beta # $Y_2 \gets e(g_3, g)^\beta$
		v1 = g ** t1 # $v_1 \gets g^{t_1}$
		v2 = g ** t2 # $v_2 \gets g^{t_2}$
		v3 = g ** t3 # $v_3 \gets g^{t_3}$
		v4 = g ** t4 # $v_4 \gets g^{t_4}$
		self.__mpk = (												\
			g1, g1Prime, g2, g3, Y1, Y2, v1, v2, v3, v4, uVec, TVec, uPrimeVec, TPrimeVec, H1		\
		) # $ \textit{mpk} \gets (g_1, g'_1, g_2, g_3, Y_1, Y_2, v_1, v_2, v_3, v_4, \bm{u}, \bm{T}, \bm{u}', \bm{T}', H_1)$
		self.__msk = (g2 ** alpha, beta, t1, t2, t3, t4) # $\textit{msk} \gets (g_2^\alpha, \beta, t_1, t_2, t_3, t_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, IDA:tuple, _S:set) -> tuple: # $\textbf{EKGen}(\textit{ID}_A, S) \to \textit{ek}_{\textit{ID}_A}(S)$
		# Checks #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all([isinstance(ele, Element) and ele.type == ZR for ele in IDA]): # hybrid check
			ID_A = IDA
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKGen: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_S, set) and len(_S) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _S):
			S = _S
		else:
			S = list(range(self.__n))
			shuffle(S)
			S = set(S[:self.__d])
			print("EKGen: The variable $S$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g3, uVec, TVec = self.__mpk[3], self.__mpk[10], self.__mpk[11]
		beta = self.__msk[1]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		rVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		ek_ID_A = tuple(																										\
			(g3 ** q(self.__group.init(ZR, i)) * (H(uVec, ID_A) * TVec[i]) ** rVec[i], g ** rVec[i]) for i in range(self.__n)	\
		) # $\textit{ek}_{\textit{ID}_{A_i}} \gets (g_3^{q(i)} [H(\bm{u}', \textit{ID}_A)T'_i]^{r_i}, g^{r_i}), \forall i \in \{1, 2, \cdots, n\}$
		ek_ID_A_S = {i:ek_ID_A[i] for i in S} # generate $\textit{ek}_{\textit{ID}_A}(S) \subset \textit{ek}_{\textit{ID}_A}$ s.t. $\|\textit{ek}_{\textit{ID}_A}(S)\| = d$ randomly
		
		# Return #
		return ek_ID_A_S # \textbf{return} $\textit{ek}_{\textit{ID}_A}(S)$
	def DKGen(self:object, IDB:tuple, _SPrime:set) -> tuple: # $\textbf{DKGen}(\textit{id}_B, S') \to \textit{dk}_{\textit{ID}_B}$
		# Checks #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_SPrime, set) and len(_SPrime) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrime):
			SPrime = _SPrime
		else:
			SPrime = list(range(self.__n))
			shuffle(SPrime)
			SPrime = set(SPrime[:self.__d])
			print("DKGen: The variable $S'$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, uVec, TVec = self.__mpk[2], self.__mpk[10], self.__mpk[11]
		g2ToThePowerOfAlpha, t1, t2, t3, t4 = self.__mpk[0], self.__msk[2], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		k1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_1 = (k_{1, 1}, k_{1, 2}, \cdots, k_{1, n}) \in \mathbb{Z}_r^n$ randomly
		k2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_2 = (k_{2, 1}, k_{2, 2}, \cdots, k_{2, n}) \in \mathbb{Z}_r^n$ randomly
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		dk_ID_B = list(( # $\textit{dk}_{\textit{ID}_{B_i}} \gets (
			g ** (k1Vec[i] * t1 * t2 + k2Vec[i] * t3 * t4), # g^{k_{1, i} t_1 t_2 + k_{2, i} t_3 t_4}
			g2ToThePowerOfAlpha ** (-t2) * (H(uVec, ID_B) * TVec[i]) ** (-k1Vec[i] * t2), # g_2^{-\alpha t_2} [H(\bm{u}, \textit{ID}_B) T_i]^{k_{1, i} t_2}
			g2ToThePowerOfAlpha ** (-t1) * (H(uVec, ID_B) * TVec[i]) ** (-k1Vec[i] * t1), # g_2^{-\alpha t_1} [H(\bm{u}, \textit{ID}_B) T_i]^{k_{1, i} t_1}
			(H(uVec, ID_B) * TVec[i]) ** (-k2Vec[i] * t4), # [H(\bm{u}, \textit{ID}_B) T_i]^{k_{2, i} t_4}
			(H(uVec, ID_B) * TVec[i]) ** (-k2Vec[i] * t3) # [H(\bm{u}, \textit{ID}_B) T_i]^{k_{2, i} t_3}
		) for i in range(self.__n)) # ), \forall i \in \{1, 2, \cdots, n\}$
		shuffle(dk_ID_B)
		dk_ID_B_SPrime = {i:dk_ID_B[i] for i in SPrime} # $\textit{dk}_{\textit{ID}_B}(S') \gets \textit{dk}_{\textit{ID}_B}(i), \forall i \in S'$
		
		# Return #
		return dk_ID_B_SPrime # \textbf{return} $\textit{dk}_{\textit{ID}_B}(S')$
	def Enc(self:object, ekIDAS:dict, IDA:tuple, IDB:tuple, _SPrimePrime:set, _S:set, message:Element) -> tuple: # $\textbf{Enc}(\textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, \textit{ID}_B, S'', S, M) \to \textit{CT}$
		# Checks #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(_SPrimePrime, set) and len(_SPrimePrime) == self.__k and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrimePrime):
			SPrimePrime = _SPrimePrime
			if isinstance(_S, set) and len(_S) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _S):
				S = _S
			else:
				S = list(SPrimePrime)
				shuffle(S)
				S = set(S[:self.__d])
				print("Enc: The variable $S$ should be a subset of $S''$ containing $d$ integers in $[0, n)$ but it is not, which has been generated accordingly. ")
		else:
			SPrimePrime = list(range(self.__n))
			shuffle(SPrimePrime)
			SPrimePrime = set(SPrimePrime[:self.__k])
			print("Enc: The variable $S''$ should be a set containing $k$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
			S = list(SPrimePrime)
			shuffle(S)
			S = set(S[:self.__d])
			print("Enc: The variable $S$ has been generated accordingly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
			if isinstance(ekIDAS, dict) and len(ekIDAS) == self.__d and all(isinstance(ele, int) for ele in ekIDAS.keys()) and all(isinstance(ele, tuple) and len(ele) == 2 for ele in ekIDAS.values()): # hybrid check
				ek_ID_A_S = ekIDAS
			else:
				ek_ID_A_S = self.EKGen(ID_A, S)
				print("Enc: The variable $\\textit{ek}_{\\textit{ID}_A}(S)$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Enc: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_ID_A_S = self.EKGen(ID_A, S)
			print("Enc: The variable $\\textit{ek}_{\\textit{ID}_A}$ has been generated accordingly. ")
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Enc: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Enc: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		Y1, Y2, v1, v2, v3, v4, uVec, TVec, uPrimeVec, TPrimeVec, H1 = (																												\
			self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]	\
		)
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		s = self.__group.random(ZR) # generate $s \in \mathbb{Z}_r$ randomly
		s1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_1 = (s_{1, 1}, s_{1, 2}, \cdots, s_{1, n}) \in \mathbb{Z}_r$ randomly
		s2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_2 = (s_{2, 1}, s_{2, 2}, \cdots, s_{2, n}) \in \mathbb{Z}_r$ randomly
		coefficients = (s, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = s$ randomly
		K_s = Y1 ** s # $K_s \gets Y_1^s$
		K_l = Y2 ** s # $K_l \gets Y_2^s$
		C = M * K_s * K_l # $C \gets M \cdot K_s \cdot K_l$
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		C1Vec = {i:(H(uVec, ID_B) * TVec[i]) ** q(self.__group.init(ZR, i)) for i in SPrimePrime} # $C_{1, i} \gets [H(\bm{u}, \textit{ID}_B) T_i]^{q(i)}, \forall i \in S''$
		C2Vec = {i:v1 ** (q(self.__group.init(ZR, i)) - s1Vec[i]) for i in SPrimePrime} # $C_{2, i} \gets v_1^{q(i) - s_{1, i}}, \forall i \in S''$
		C3Vec = {i:v2 ** s1Vec[i] for i in SPrimePrime} # $C_{3, i} \gets v_2^{s_{1, i}}, \forall i \in S''$
		C4Vec = {i:v3 ** (q(self.__group.init(ZR, i)) - s2Vec[i]) for i in SPrimePrime} # $C_{4, i} \gets v_3^{q(i) - s_{2, i}}, \forall i \in S''$
		C5Vec = {i:v4 ** s2Vec[i] for i in SPrimePrime} # $C_{5, i} \gets v_4^{s_{2, i}}, \forall i \in S''$
		zVec = {i:self.__group.random(ZR) for i in S} # generate $\vec{z} = (z_{S_1}, z_{S_2}, \cdots, z_{S_d}) \in \mathbb{Z}_r^d$ randomly
		zPrimeVec = {i:self.__group.random(ZR) for i in S} # generate $\vec{z}' = (z'_{S_1}, z'_{S_2}, \cdots, z'_{S_d}) \in \mathbb{Z}_r^d$ randomly
		C6Vec = {i:g ** zPrimeVec[i] for i in S} # $C_{6, i} \gets g^{z'_i}, \forall i \in S$
		C7Vec = {i:(ek_ID_A_S[i][1] * g ** zVec[i]) ** s for i in S} # $C_{7, i} \gets (\textit{ek}_{\textit{ID}_{A_{i, 2}}}(S) \cdot g^{z_i})^s, \forall i \in S$
		C8Vec = {i:ek_ID_A_S[i][0] ** s * (H(uPrimeVec, ID_A) * TPrimeVec[i]) ** (s * zVec[i]) * H1( # $C_{8, i} \gets \textit{ek}_{\textit{ID}_{A_{i, 1}}}(S) \cdot [H(\bm{u}', \textit{ID}_A) T'_i]^{s \cdot z_i} \cdot H_1(
			self.__group.serialize(C) + self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) # C || C_{1, i} || C_{2, i} || C_{3, i}
			+ self.__group.serialize(C4Vec[i]) + self.__group.serialize(C5Vec[i]) + self.__group.serialize(C6Vec[i]) + self.__group.serialize(C7Vec[i]) # C_{4, i} || C_{5, i} || C_{6, i} || C_{7, i}
		) for i in S} # ), \forall i \in S$
		I = S.intersection(SPrimePrime) # $I \gets S \cap S''$
		if len(I) >= self.__d: # \textbf{if} $\|I\| \leqslant d$ \textbf{then}
			IStar = list(I)
			shuffle(IStar)
			IStar = set(IStar[:self.__d]) # \quad generate $I^* \subset I$ s.t. $\|I^*\| = d$ randomly
		else: # \textbf{else}
			IStar = set(I)
			while len(IStar) < self.__d: # \quad generate $I^* \gets I \cup x$ s.t. $x \subset \{0, 1, \cdots, n - 1\} \land \|x\| = d - \|I\| \land I \cap x = \emptyset$ randomly
				IStar.add(randbelow(self.__n))
		# \textbf{end if}
		CT = (																		\
			S, IStar, C, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec, C6Vec, C7Vec, C8Vec		\
		) # $\textit{CT} \gets (S, I^*, C, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5, \vec{C}_6, \vec{C}_7, \vec{C}_8)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec(self:object, dkIDBSPrime:dict, IDB:tuple, IDA:tuple, _SPrimePrime:set, _SPrime:set, cipherText:tuple) -> Element|bool: # $\textbf{Dec}(\textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, \textit{ID}_A, S'', S', \textit{CT}) \to M$
		# Checks #
		if isinstance(_SPrimePrime, set) and len(_SPrimePrime) == self.__k and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrimePrime):
			SPrimePrime = _SPrimePrime
			if isinstance(_SPrime, set) and len(_SPrime) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrime):
				SPrime = _SPrime
			else:
				SPrime = list(SPrimePrime)
				shuffle(SPrime)
				SPrime = set(SPrime[:self.__d])
				print("Dec: The variable $S'$ should be a subset of $S''$ containing $d$ integers in $[0, n)$ but it is not, which has been generated accordingly. ")
		else:
			SPrimePrime = list(range(self.__n))
			shuffle(SPrimePrime)
			SPrimePrime = set(SPrimePrime[:self.__k])
			print("Dec: The variable $S''$ should be a set containing $k$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
			SPrime = list(SPrimePrime)
			shuffle(SPrime)
			SPrime = set(SPrime[:self.__d])
			print("Dec: The variable $S'$ has been generated accordingly. ")
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
			if (																															\
				isinstance(dkIDBSPrime, dict) and len(dkIDBSPrime) == self.__d and all(isinstance(ele, int) for ele in dkIDBSPrime.keys())	\
				and all(isinstance(ele, tuple) and len(ele) == 5 for ele in dkIDBSPrime.values())											\
			): # hybrid check
				dk_ID_B_SPrime = dkIDBSPrime
			else:
				dk_ID_B_SPrime = self.DKGen(ID_B, SPrime)
				print("Dec: The variable $\\textit{dk}_{\\textit{ID}_B}(S)'$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Dec: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_ID_B_S_Prime = self.DKGen(ID_B, SPrime)
			print("Dec: The variable $\\textit{dk}_{\\textit{ID}_B}(S)'$ has been generated accordingly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Dec: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if (																							\
			isinstance(cipherText, tuple) and len(cipherText) == 11 and isinstance(cipherText[0], set)	\
			and isinstance(cipherText[1], set) and isinstance(cipherText[2], Element)					\
			and all(isinstance(ele, dict) and len(ele) == self.__k for ele in cipherText[3:8])			\
			and all(isinstance(ele, dict) and len(ele) == self.__d for ele in cipherText[8:])			\
		): # hybrid check
			CT = cipherText
		else:
			S = list(SPrimePrime)
			shuffle(S)
			S = set(S[:self.__d])
			CT = self.Enc(self.EKGen(ID_A, S), ID_A, ID_B, SPrimePrime, S, self.__group.random(GT))
			del S
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing 2 sets, 1 element, 5 $k$-pair dictionaries, and 3 $d$-pair dictionaries but it is not, which has been generated randomly. ")
		
		# Unpack #
		uPrimeVec, TPrimeVec, H1 = self.__mpk[12], self.__mpk[13], self.__mpk[14]
		S, IStar, C, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec, C6Vec, C7Vec, C8Vec = CT[0], CT[1], CT[2], CT[3], CT[4], CT[5], CT[6], CT[7], CT[8], CT[9], CT[10]
		
		# Scheme #
		CTVec = {																																										\
			i:self.__group.serialize(C) + self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
			+ self.__group.serialize(C5Vec[i]) + self.__group.serialize(C6Vec[i]) + self.__group.serialize(C7Vec[i]) for i in IStar														\
		} # $\textit{CT}_i \gets C || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i} || C_{5, i} || C_{6, i} || C{7, i}, \forall i \in I^*$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		I = set(SPrime).intersection(SPrimePrime) # $I \gets S' \cap S''$
		if len(I) >= self.__d: # \textbf{if} $\|I\| \leqslant d$ \textbf{then}
			I = list(I)
			shuffle(I)
			I = set(I[:self.__d]) # \quad generate $I \subset S' \cap S''$ s.t. $\|I\| = d$ randomly
		else: # \textbf{else}
			while len(I) < self.__d: # \quad generate $I \gets I \cup x$ s.t. $x \subset \{0, 1, \cdots, n - 1\} \land \|x\| = d - \|I\| \land I \cap x = \emptyset$ randomly
				I.add(randbelow(self.__n))
		# \textbf{end if}
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		KlPrime = self.__product(
			tuple((pair(C8Vec[i], g) / (pair(H(uPrimeVec, ID_A) * TPrimeVec[i], C7Vec[i]) *pair(H1(CTVec[i]), C6Vec[i]))) ** Delta(i, IStar, 0) for i in IStar)
		) # $K'_l \gets \prod\limits_{i \in I^*} \left(\frac{e(C_{8, i}, g)}{e([H(\bm{u}', \textit{ID}_A) T'_i] e(H_1(\textit{CT}_i), C_{6, i})}\right)^{\Delta_{i, I^*}(0)}$
		KsPrime = self.__product(																										\
			tuple((																														\
				(pair(C1Vec[i], dk_ID_B_SPrime[i][0]) * pair(C2Vec[i], dk_ID_B_SPrime[i][1]) * pair(C3Vec[i], dk_ID_B_SPrime[i][2]))	\
				/ (pair(C4Vec[i], dk_ID_B_SPrime[i][3]) * pair(C5Vec[i], dk_ID_B_SPrime[i][4]))											\
			) ** Delta(i, I, 0) for i in I)																								\
		) # $K'_s \gets \prod\limits_{i \in I} \left(\right)^{\Delta_{i, j}(0)}$
		if len(S.intersection(SPrimePrime)) >= self.__d and len(SPrime.intersection(SPrimePrime)) >= self.__d: # \textbf{if} $|S \cap S''| \leqslant d \land |S' \cap S''| \leqslant d$ \textbf{then}
			M = C * KsPrime * KlPrime # \quad$M \gets C \cdot K'_s \cdot K'_l$
		else: # \textbf{else}
			M = False # \quad$M \gets \perp$
		# \textbf{end if}
		
		# Return #
		return M # \textbf{return} $M$
	def EKeySanity(self:object, ekIDAS:dict, IDA:tuple, _S:set) -> bool: # $\textbf{EKeySanity}(\textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, S) \to y, y \in \{0, 1\}$
		# Checks #
		if not self.__flag:
			print("EKeySanity: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKeySanity`` subsequently. ")
			self.Setup()
		if isinstance(_S, set) and len(_S) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _S):
			S = _S
		else:
			S = list(range(self.__n))
			shuffle(S)
			S = set(S[:self.__d])
			print("EKeySanity: The variable $S$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
			if isinstance(ekIDAS, dict) and len(ekIDAS) == self.__d and all(isinstance(ele, int) for ele in ekIDAS.keys()) and all(isinstance(ele, tuple) and len(ele) == 2 for ele in ekIDAS.values()): # hybrid check
				ek_ID_A_S = ekIDAS
			else:
				ek_ID_A_S = self.EKGen(ID_A, S)
				print("EKeySanity: The variable $\\textit{ek}_{\\textit{ID}_A}(S)$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKeySanity: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_ID_A_S = self.EKGen(ID_A, S)
			print("EKeySanity: The variable $\\textit{ek}_{\\textit{ID}_A}$ has been generated accordingly. ")
		
		# Unpack #
		g3, g1Prime, uPrimeVec, TPrimeVec = self.__mpk[3], self.__mpk[1], self.__mpk[12], self.__mpk[13]
		
		# Scheme #
		if len(S) >= self.__d: # \textbf{if} $\|S\| \leqslant d$ \textbf{then}
			SPrimePrimePrime = list(S)
			shuffle(SPrimePrimePrime)
			SPrimePrimePrime = set(SPrimePrimePrime[:self.__d]) # \quad generate $S''' \subset S$ s.t. $\|S'''\| = d$ randomly
		else: # \textbf{else}
			SPrimePrimePrime = set(S)
			while len(SPrimePrimePrime) < self.__d: # \quad generate $S''' \gets S''' \cup x$ s.t. $x \subset \{0, 1, \cdots, n - 1\} \land \|x\| = d - \|S'''\| \land S''' \cap x = \emptyset$ randomly
				SPrimePrimePrime.add(randbelow(self.__n))
		# \textbf{end if}
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta_{i, S}(x) := \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		
		# Return #
		return self.__product(tuple(																															\
			(pair(ek_ID_A_S[i][0], g) / (pair(H(uPrimeVec, ID_A) * TPrimeVec[i], ek_ID_A_S[i][1]))) ** Delta(i, SPrimePrimePrime, 0) for i in SPrimePrimePrime	\
		)) == pair(g3, g1Prime) # \textbf{return} $\prod\limits_{i \in S'''} \left(\frac{e(g_3^{j(i)}[H'(\textbf{u}', \textit{ID}_A)T'_i]^{r_i}, g)}{e([H'(\bm{u}', \textit{ID}_A) T'_i, g^{r'_i})}\right)^{\Delta_{i, S}(0)} = \mathbb{S}e(g_3, g'_1)$
	def DKeySanity(self:object, dkIDBSPrime:dict, IDB:tuple, _SPrime:set) -> bool: # $\textbf{DKeySanity}(\textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, S') \to y, y \in \{0, 1\}$
		# Checks #
		if not self.__flag:
			print("DKeySanity: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKeySanity`` subsequently. ")
			self.Setup()
		if isinstance(_SPrime, set) and len(_SPrime) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrime):
			SPrime = _SPrime
		else:
			SPrime = list(range(self.__n))
			shuffle(SPrime)
			SPrime = set(SPrime[:self.__d])
			print("DKeySanity: The variable $S'$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
			if (																															\
				isinstance(dkIDBSPrime, dict) and len(dkIDBSPrime) == self.__d and all(isinstance(ele, int) for ele in dkIDBSPrime.keys())	\
				and all(isinstance(ele, tuple) and len(ele) == 5 for ele in dkIDBSPrime.values())											\
			): # hybrid check
				dk_ID_B_SPrime = dkIDBSPrime
			else:
				dk_ID_B_SPrime = self.DKGen(ID_B, SPrime)
				print("DKeySanity: The variable $\\textit{dk}_{\\textit{ID}_B}(S')$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKeySanity: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_ID_B_SPrime = self.DKGen(ID_B, SPrime)
			print("DKeySanity: The variable $\\textit{dk}_{\\textit{ID}_B}(S')$ has been generated accordingly. ")
		
		# Unpack #
		Y1, v1, v2, v3, v4, uVec, TVec = self.__mpk[4], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11]
		
		# Scheme #
		s1Vec = {i:self.__group.random(ZR) for i in SPrime} # generate $\vec{s}_1 = (s_{1, 1}, s_{1, 2}, \cdots, s_{1, n}) \in \mathbb{Z}_r$ randomly
		s2Vec = {i:self.__group.random(ZR) for i in SPrime} # generate $\vec{s}_2 = (s_{2, 1}, s_{2, 2}, \cdots, s_{2, n}) \in \mathbb{Z}_r$ randomly
		H = lambda vec, ID:vec[0] * self.__product( # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), 
			tuple(vec[j + 1] ** ID[j] for j in range(self.__n)) # \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) 
		) # \to \bm{u}_0\prod\limits_{j \in \{1, 2, \cdots, n\}} \bm{u}_j^{\textit{ID}_j}$
		D1Vec = {i:H(uVec, ID_B) * TVec[i] for i in SPrime} # $D_{1, i} \gets H(\bm{u}, \textit{ID}_B) T_i, \forall i \in S'$
		D2Vec = {i:v1 ** (self.__group.init(ZR, 1) - s1Vec[i]) for i in SPrime} # $D_{2, i} \gets v_1^{1 - s_{1, i}}, \forall i \in S'$
		D3Vec = {i:v2 ** s1Vec[i] for i in SPrime} # $D_{3, i} \gets v_2^{s_{1, i}}, \forall i \in S'$
		D4Vec = {i:v3 ** (self.__group.init(ZR, 1) - s2Vec[i]) for i in SPrime} # $D_{4, i} \gets v_3^{1 - s_{2, i}}, \forall i \in S'$
		D5Vec = {i:v4 ** s2Vec[i] for i in SPrime} # $D_{5, i} \gets v_4^{s_{2, i}}, \forall i \in S'$
		Y1Reciprocal = 1 / Y1
		
		# Return #
		return all( # \textbf{return} $\bigwedge\limits_{i \in S'} \left(\frac{e(D_{1, i}, \textit{dk}_{\textit{ID}_{B_{i, 1}}}) e(D_{2, i}, \textit{dk}_{\textit{ID}_{B_{i, 2}}})
			(pair(D1Vec[i], dk_ID_B_SPrime[i][0]) * pair(D2Vec[i], dk_ID_B_SPrime[i][1]) * pair(D3Vec[i], dk_ID_B_SPrime[i][2])) # e(D_{3, i}, \textit{dk}_{\textit{ID}_{B_{i, 3}}})}
			/ (pair(D4Vec[i], dk_ID_B_SPrime[i][3]) * pair(D5Vec[i], dk_ID_B_SPrime[i][4])) == Y1Reciprocal for i in SPrime # {e(D_{4, i}, \textit{dk}_{\textit{ID}_{B_{i, 4}}})
		) # e(D_{5, i}, \textit{dk}_{\textit{ID}_{B_{i, 5}}})} = Y_1^{-1}\right)$
	def Trace1(self:object, EMathcal_ID_A:callable, ekIDAS:dict, IDA:tuple, _S:set) -> bool: # $\textbf{Trace1}(\mathcal{E}_{\textit{ID}_A}, \textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, S) \to y, y \in \{0, 1\}$
		# Checks #
		if not self.__flag:
			print("Trace1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Trace1`` subsequently. ")
			self.Setup()
		if isinstance(_S, set) and len(_S) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _S):
			S = _S
		else:
			S = list(range(self.__n))
			shuffle(S)
			S = set(S[:self.__d])
			print("Trace1: The variable $S$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
			if isinstance(ekIDAS, dict) and len(ekIDAS) == self.__d and all(isinstance(ele, int) for ele in ekIDAS.keys()) and all(isinstance(ele, tuple) and len(ele) == 2 for ele in ekIDAS.values()): # hybrid check
				ek_ID_A_S = ekIDAS
			else:
				ek_ID_A_S = self.EKGen(ID_A, S)
				print("Trace1: The variable $\\textit{ek}_{\\textit{ID}_A}(S)$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Trace1: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_ID_A_S = self.EKGen(ID_A, S)
			print("Trace1: The variable $\\textit{ek}_{\\textit{ID}_A}$ has been generated accordingly. ")
		
		# Unpack #
		pass
		
		# Scheme #
		if self.EKeySanity(ek_ID_A_S, ID_A, S): # \textbf{if} $\textbf{EKeySanity}(\textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, S)$ \textbf{then}
			M = self.__group.random(GT) # \quad generate $M \in \mathbb{G}_T$ randomly
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n)) # \quad generate $\textit{ID}_B = (\textit{ID}_{B_1}, \textit{ID}_{B_2}, \cdots, \textit{ID}_{B_n}) \in \mathbb{Z}_r$ randomly
			SPrimePrime = set(S)
			while len(SPrimePrime) < self.__k: # \quad generate $S''$ s.t. $S \subset S'' \subset \{0, 1, \cdots, n - 1\} \land \|S''\| = k$ randomly
				SPrimePrime.add(randbelow(self.__n))
			SPrime = list(SPrimePrime)
			shuffle(SPrime)
			SPrime = set(SPrime[:self.__d]) # \quad generate $S' \subset S''$ s.t. $\|S'\| = d$ randomly
			try: # \textbf{return} $\textbf{Dec}(\textbf{DKGen}(\textit{ID}_B, S'), \textit{ID}_B, \textit{ID}_A, S'', S', \mathcal{E}_{\textit{ID}_A}(\textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, \textit{ID}_B, S'', S, M)) = M$
				return self.Dec(self.DKGen(ID_B, SPrime), ID_B, ID_A, SPrimePrime, SPrime, EMathcal_ID_A(ek_ID_A_S, ID_A, ID_B, SPrimePrime, S, M)) == M
			except:
				return False
		else: # \textbf{else}
			return False # \quad\textbf{return} $0$
		# \textbf{end if}
		
		# Return #
		pass
	def Trace2(self:object, DMathcal_ID_B:callable, dkIDBSPrime:dict, IDB:tuple, _SPrime:set) -> bool: # $\textbf{Trace2}(\mathcal{D}_{\textit{ID}_B}, \textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, S') \to y, y \in \{0, 1\}$
		# Checks #
		if not self.__flag:
			print("Trace2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Trace2`` subsequently. ")
			self.Setup()
		if isinstance(_SPrime, set) and len(_SPrime) == self.__d and all(isinstance(ele, int) and 0 <= ele < self.__n for ele in _SPrime):
			SPrime = _SPrime
		else:
			SPrime = list(range(self.__n))
			shuffle(SPrime)
			SPrime = set(SPrime[:self.__d])
			print("Trace2: The variable $S'$ should be a set containing $d$ integers in $[0, n)$ but it is not, which has been generated randomly. ")
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
			if isinstance(dkIDBSPrime, dict) and len(dkIDBSPrime) == self.__d and all(isinstance(ele, int) for ele in dkIDBSPrime.keys()) and all(isinstance(ele, tuple) and len(ele) == 5 for ele in dkIDBSPrime.values()): # hybrid check
				dk_ID_B_SPrime = dkIDBSPrime
			else:
				dk_ID_B_SPrime = self.DKGen(ID_B, SPrime)
				print("Trace2: The variable $\\textit{dk}_{\\textit{ID}_B}(S')$ should be a ``dict`` containing $d$ ``int``--``tuple`` pairs but it is not, which has been generated accordingly. ")
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Trace2: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_ID_B_SPrime = self.DKGen(ID_B, SPrime)
			print("Trace2: The variable $\\textit{dk}_{\\textit{ID}_B}(S')$ has been generated accordingly. ")
		
		# Unpack #
		pass
		
		# Scheme #
		if self.DKeySanity(dk_ID_B_SPrime, ID_B, SPrime): # \textbf{if} $\textbf{DKeySanity}(\textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, S')$ \textbf{then}
			M = self.__group.random(GT) # \quad generate $M \in \mathbb{G}_T$ randomly
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n)) # \quad generate $\textit{ID}_A = (\textit{ID}_{A_1}, \textit{ID}_{A_2}, \cdots, \textit{ID}_{A_n}) \in \mathbb{Z}_r$ randomly
			SPrimePrime = set(SPrime)
			while len(SPrimePrime) < self.__k: # \quad generate $S''$ s.t. $S' \subset S'' \subset \{0, 1, \cdots, n - 1\} \land \|S''\| = k$ randomly
				SPrimePrime.add(randbelow(self.__n))
			S = list(SPrimePrime)
			shuffle(S)
			S = set(S[:self.__d]) # \quad generate $S \subset S''$ s.t. $\|S\| = d$ randomly
			try: # \textbf{return} $\mathcal{D}_{\textit{ID}_B}(\textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, \textit{ID}_A, S'', S', \textbf{Enc}(\textbf{EKGen}(\textit{ID}_A, S), \textit{ID}_A, \textit{ID}_B, S'', S, M) = M$
				return DMathcal_ID_B(dk_ID_B_SPrime, ID_B, ID_A, SPrimePrime, SPrime, self.Enc(self.EKGen(ID_A, S), ID_A, ID_B, SPrimePrime, S, M)) == M
			except Exception as e:
				return False
		else: # \textbf{else}
			return False # \quad\textbf{return} $0$
		# \textbf{end if}
		
		# Return #
		pass
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


def conductScheme(curveParameter:tuple|list|dict|str, n:int = 30, k:int = 20, d:int = 10, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, nString, kString, dString, runString = "N/A", 512, "N/A", "N/A", "N/A", "N/A" # the default value of the security parameter in the Python charm library is 512
	isSystemValid, isSchemeCorrect, isEKeySanity, isDKeySanity, isTracing1Verified, isTracing2Verified = (False, ) * 6
	timeSetup, timeEKGen, timeDKGen, timeEnc, timeDec, timeEKeySanity, timeDKeySanity, timeTrace1, timeTrace2 = ("N/A", ) * 9
	sizeZR, sizeG1G2, sizeGT = ("N/A", ) * 3
	sizeMpk, sizeMsk, sizeEkIDAS, sizeDkIDBSPrime, sizeCT = ("N/A", ) * 5
	
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
	if isinstance(k, int):
		kString = k
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
		print("$k$:", kString)
		print("$d$:", dString)
		print("run:", runString)
	if flag and 1 <= d <= k <= n:
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
		print("Is the system valid? No. The parameters $n$, $k$, and $d$ should be three positive integers satisfying $1 \\leqslant d \\leqslant k \\leqslant n$. ")
		print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemeAAIBME = SchemeAAIBME(group)
		sizeZR, sizeG1G2, sizeGT = schemeAAIBME.getLengthOf(group.random(ZR)), schemeAAIBME.getLengthOf(group.random(G1)), schemeAAIBME.getLengthOf(group.random(GT))
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemeAAIBME.Setup(n = n, k = k, d = d)
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemeAAIBME.getLengthOf(mpk), schemeAAIBME.getLengthOf(msk)
		
		# EKGen #
		startTime = perf_counter()
		ID_A = tuple(group.random(ZR) for _ in range(n))
		SPrimePrime = list(range(n))
		shuffle(SPrimePrime)
		SPrimePrime = set(SPrimePrime[:k])
		S = list(SPrimePrime)
		shuffle(S)
		S = set(S[:d])
		ek_ID_A_S = schemeAAIBME.EKGen(ID_A, S)
		endTime = perf_counter()
		timeEKGen = endTime - startTime
		sizeEkIDAS = schemeAAIBME.getLengthOf(ek_ID_A_S)
		
		# DKGen #
		startTime = perf_counter()
		ID_B = tuple(group.random(ZR) for _ in range(n))
		SPrime = list(SPrimePrime)
		shuffle(SPrime)
		SPrime = set(SPrime[:d])
		dk_ID_B_SPrime = schemeAAIBME.DKGen(ID_B, SPrime)
		endTime = perf_counter()
		timeDKGen = endTime - startTime
		sizeDkIDBSPrime = schemeAAIBME.getLengthOf(dk_ID_B_SPrime)
		
		# Enc #
		startTime = perf_counter()
		message = group.random(GT)
		CT = schemeAAIBME.Enc(ek_ID_A_S, ID_A, ID_B, SPrimePrime, S, message)
		endTime = perf_counter()
		timeEnc = endTime - startTime
		sizeCT = schemeAAIBME.getLengthOf(CT)
		
		# Dec #
		startTime = perf_counter()
		M = schemeAAIBME.Dec(dk_ID_B_SPrime, ID_B, ID_A, SPrimePrime, SPrime, CT)
		endTime = perf_counter()
		isSchemeCorrect = M == message
		timeDec = endTime - startTime
		
		# EKeySanity #
		startTime = perf_counter()
		isEKeySanity = schemeAAIBME.EKeySanity(ek_ID_A_S, ID_A, S)
		endTime = perf_counter()
		timeEKeySanity = endTime - startTime
		
		# DKeySanity #
		startTime = perf_counter()
		isDKeySanity = schemeAAIBME.DKeySanity(dk_ID_B_SPrime, ID_B, SPrime)
		endTime = perf_counter()
		timeDKeySanity = endTime - startTime
		
		# Trace1 #
		startTime = perf_counter()
		isTracing1Verified = schemeAAIBME.Trace1(schemeAAIBME.Enc, ek_ID_A_S, ID_A, S)
		endTime = perf_counter()
		timeTrace1 = endTime - startTime
		
		# Trace2 #
		startTime = perf_counter()
		isTracing2Verified = schemeAAIBME.Trace2(schemeAAIBME.Dec, dk_ID_B_SPrime, ID_B, SPrime)
		endTime = perf_counter()
		timeTrace2 = endTime - startTime
		
		# Destruction #
		del schemeAAIBME
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Original:", message)
			print("Decrypted:", M)
			print("Is the scheme correct (M == message)? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Is EKey Sanity? {0}. ".format("Yes" if isEKeySanity else "No"))
			print("Is DKey Sanity? {0}. ".format("Yes" if isDKeySanity else "No"))
			print("Is tracing 1 verified (M1 == message1)? {0}. ".format("Yes" if isTracing1Verified else "No"))
			print("Is tracing 2 verified (M2 == message2)? {0}. ".format("Yes" if isTracing2Verified else "No"))
			print("Time:", (timeSetup, timeEKGen, timeDKGen, timeEnc, timeDec, timeEKeySanity, timeDKeySanity, timeTrace1, timeTrace2))
			print("Space:", (sizeZR, sizeG1G2, sizeGT, sizeMpk, sizeMsk, sizeEkIDAS, sizeDkIDBSPrime, sizeCT))
			print()
	
	# End #
	return [																										\
		curveName, securityParameter, nString, kString, dString, runString, 										\
		isSystemValid, isSchemeCorrect, isEKeySanity, isDKeySanity, isTracing1Verified, isTracing2Verified, 		\
		timeSetup, timeEKGen, timeDKGen, timeEnc, timeDec, timeEKeySanity, timeDKeySanity, timeTrace1, timeTrace2, 	\
		sizeZR, sizeG1G2, sizeGT, 																					\
		sizeMpk, sizeMsk, sizeEkIDAS, sizeDkIDBSPrime, sizeCT														\
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
			queries = ("curveParameter", "secparam", "n", "k", "d", "runCount")
			validators = ("isSystemValid", "isSchemeCorrect", "isEKeySanity", "isDKeySanity", "isTracing1Verified", "isTracing2Verified")
			metrics = (																	\
				"Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", "EKeySanity (s)", "DKeySanity (s)", "Trace1 (s)", "Trace2 (s)", 			\
				"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 				\
				"mpk (B)", "msk (B)", "ek_ID_A_S (B)", "dk_ID_B_SPrime (B)", "CT (B)"	\
			)
			
			# Scheme #
			columns, qLength, results = queries + validators + metrics, len(queries), []
			length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for n in range(15, 31, 5):
						for k in range(10, n, 5):
							for d in range(5, k, 5):
								averages = conductScheme(curveParameter, n = n, k = k, d = d, run = 1)
								for run in range(2, runCount + 1):
									result = conductScheme(curveParameter, n = n, k = k, d = d, run = run)
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