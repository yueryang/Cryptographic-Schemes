import os
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
except:
	PairingGroup, G1, GT, ZR, pair, Element = (None, ) * 6
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
	__SchemeName = "SchemeIBMEMR" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the IBMEMR cryptographic scheme in Python programming language based on the Python charm library. ")
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

class SchemeIBMEMR:
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
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__d = 30
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __computeCoefficients(self:object, roots:tuple|list|set, k:Element|int|float|None = None) -> tuple:
		flag = False
		if isinstance(roots, (tuple, list, set)) and roots:
			n = len(roots)
			if isinstance(roots[0], Element) and all(isinstance(root, Element) and root.type == roots[0].type for root in roots):
				flag, coefficients = True, [None] * (n - 1) + [roots[0], self.__group.init(roots[0].type, 1)]
				offset = k if isinstance(k, Element) and k.type == roots[0].type else None
			elif isinstance(roots[0], (int, float)) and all(isinstance(root, (int, float)) for root in roots):
				flag, coefficients = True, [None] * (n - 1) + [roots[0], 1]
				offset = k if isinstance(k, (int, float)) else None
		if flag:
			cnt = n - 2
			for r in roots[1:]:
				coefficients[cnt] = r * coefficients[cnt + 1]
				for i in range(cnt + 1, n - 1):
					coefficients[i] += r * coefficients[i + 1]
				coefficients[n - 1] += r
				cnt -= 1
			for i in range(n - 1, -1, -2):
				coefficients[i] = -coefficients[i]
			if offset is not None:
				coefficients[0] += offset
			return tuple(coefficients)
		else:
			return (k, )
	def __concat(self:object, *vector:tuple|list) -> bytes:
		abcBytes = b""
		if isinstance(vector, (tuple, list)):
			for item in vector:
				if isinstance(item, (tuple, list)):
					abcBytes += self.__concat(*item)
				elif isinstance(item, Element):
					abcBytes += self.__group.serialize(item)
				elif isinstance(item, bytes):
					abcBytes += item
				else:
					try:
						abcBytes += bytes(item)
					except:
						pass
		return abcBytes
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
	def Setup(self:object, d:int = 30, seed:int|None = None) -> tuple: # $\textbf{Setup}(d) \to (\textit{mpk}, \textit{msk})$
		# Checks #
		self.__flag = False
		if isinstance(d, int) and d >= 1: # boundary check
			self.__d = d
		else:
			self.__d = 30
			print("Setup: The variable $d$ should be a positive integer but it is not, which has been defaulted to $30$. ")
		self.__seed = seed % self.__d if isinstance(seed, int) else randbelow(self.__d)
		
		# Scheme #
		p = self.__group.order() # $p \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_1: \mathbb{Z}_r \to \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_2: \mathbb{Z}_r \to \mathbb{G}_1$
		if 512 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $\hat{H}: \mathbb{G}_T \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \to \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_4: \mathbb{G}_T \to \mathbb{Z}_r$
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \to \mathbb{G}_1$
		g0, g1 = self.__group.random(G1), self.__group.random(G1) # generate $g_0, g_1 \in \mathbb{G}_1$ randomly
		w, alpha, gamma, k, t1, t2 = self.__group.random(ZR, 6) # generate $w, \alpha, \gamma, k, t_1, t_2 \in \mathbb{Z}_r$ randomly
		Omega = pair(g, g) ** w # $\Omega \gets e(g, g)^w$
		v1 = g ** t1 # $v_1 \gets g^{t_1}$
		v2 = g ** t2 # $v_2 \gets g^{t_2}$
		v3 = g ** gamma # $v_3 \gets g^\gamma$
		v4 = g ** k # $v_4 \gets g^k$
		self.__mpk = (p, g, g0, g1, v1, v2, v3, v4, Omega, H1, H2, H3, H4, H5, HHat) # $ \textit{mpk} \gets (p, g, g_0, g_1, v_1, v_2, v_3, v_4, \Omega, H_1, H_2, H_3, H_4, H_5, \hat{H})$
		self.__msk = (w, alpha, gamma, k, t1, t2) # $\textit{msk} \gets (w, \alpha, \gamma, k, t_1, t_2)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, idS:Element) -> Element: # $\textbf{EKGen}(\textit{id}_S) \to \textit{ek}_{\textit{id}_S}$
		# Checks #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("EKGen: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[9]
		alpha = self.__msk[1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def DKGen(self:object, idR:Element) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \to \textit{dk}_{\textit{id}_R}$
		# Checks #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("DKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[10]
		w, alpha, gamma, t1, t2 = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[4], self.__msk[5]
		
		# Scheme #
		dk1 = H2(id_R) ** alpha # $\textit{dk}_1 \gets H_2(\textit{id}_R)^\alpha$
		dk2 = g ** (w / t1) * (g0 * g1 ** id_R) ** (gamma / t1) # $\textit{dk}_2 \gets g^{w / t_1} (g_0 g_1^{\textit{id}_R})^{\gamma / t_1}$
		dk3 = g ** (w / t2) * (g0 * g1 ** id_R) ** (gamma / t2) # $\textit{dk}_3 \gets g^{w / t_2} (g_0 g_1^{\textit{id}_R})^{\gamma / t_2}$
		dk_id_R = (dk1, dk2, dk3) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3)$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def TDKGen(self:object, idR:Element) -> tuple: # $\textbf{TDKGen}(\textit{id}_R) \to \textit{td}_{\textit{id}_R}$
		# Checks #
		if not self.__flag:
			print("TDKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TDKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("TDKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[10]
		w, alpha, k, t1, t2 = self.__msk[0], self.__msk[1], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		td1 = g ** (-(1 / t1)) * (g0 * g1 ** id_R) ** (k / t1) # $\textit{td}_1 \gets g^{-1 / t_1} (g_0 g_1^{\textit{id}_R})^{k / t_1}$
		td2 = g ** (-(1 / t2)) * (g0 * g1 ** id_R) ** (k / t2) # $\textit{td}_2 \gets g^{-1 / t_2} (g_0 g_1^{\textit{id}_R})^{k / t_2}$
		td_id_R = (td1, td2) # $\textit{td}_{\textit{id}_R} \gets (\textit{td}_1, \textit{td}_2)$
		
		# Return #
		return td_id_R # \textbf{return} $\textit{td}_{\textit{id}_R}$
	def Enc(self:object, ekidS:Element, idR:Element, message:int|bytes) -> object: # $\textbf{Enc}(\textit{ek}_{\textit{id}_S}, \textit{id}_R, m) \to \textit{ct}$
		# Checks #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekidS, Element): # type check
			ek_id_S = ekidS
		else:
			ek_id_S = self.EKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_S}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBMEMR", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBMEMR\". ")
		
		# Unpack #
		g, g0, g1, v1, v2, v3, v4, H2, H3, H4, H5, HHat = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]
		w = self.__msk[0]
		
		# Scheme #
		S = tuple(self.__group.random(ZR) for _ in range(self.__seed)) + (id_R, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - self.__seed - 1)) # generate $S \gets (\textit{id}_1, \textit{id}_2, \cdots, \textit{id}_R, \cdots, \textit{id}_d)$ randomly
		s1, s2, beta, sigma, K, R = self.__group.random(ZR, 6) # generate $s_1, s_2, \beta, \sigma, K, R \in \mathbb{Z}_r$ randomly
		r = H3(self.__group.serialize(sigma) + m.to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")) # $r \gets H_3(\sigma || m)$
		ct1 = g ** beta # $\textit{ct}_1 \gets g^\beta$
		ct2 = v1 ** s1 # $\textit{ct}_2 \gets v_1^{s_1}$
		ct3 = v2 ** s2 # $\textit{ct}_3 \gets v_2^{s_2}$
		KArray = tuple(pair(H2(S[i]), ek_id_S * ct1) for i in range(self.__d)) # $K_i \gets e(H_2(\textit{id}_i), ek_{\textit{id}_S} \cdot \textit{ct}_1), \forall i \in \{1, 2, \cdots, d\}$
		aArray = self.__computeCoefficients(						\
			tuple(H4(KArray[i]) for i in range(self.__d)), k = K	\
		) # Compute $a_0, a_1, a_2, \cdots a_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $F(x) = \prod\limits_{i = 1}^d (x - H_4(K_i)) + K = a_0 + \sum\limits_{i = 1}^d a_i x^i$
		s = s1 + s2 # $s \gets s_1 + s_2$
		RArray = tuple(pair(v3, (g0 * g1 ** S[i]) ** s) for i in range(self.__d)) # $R_i \gets e(v_3, (g_0 g_1^{\textit{id}_i})^s), \forall i \in \{1, 2, \cdots, d\}$
		bArray = self.__computeCoefficients(												\
			tuple(H4(RArray[i] * pair(g, g) ** (w * s)) for i in range(self.__d)), k = R	\
		) # Compute $b_0, b_1, b_2, \cdots, b_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $L(x) = \prod\limits_{i = 1}^d (x - H_4(R_i \cdot e(g, g)^{ws})) + R = b_0 + \sum\limits_{i = 1}^d b_i x^i$
		ct4 = HHat(K) ^ HHat(R) ^ int.from_bytes(m.to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big") + self.__group.serialize(sigma), byteorder = "big") # $\textit{ct}_4 \gets \hat{H}(K) \oplus \hat{H}(R) \oplus (m || \sigma)$
		VArray = tuple(pair(v4, (g0 * g1 ** S[i]) ** s) for i in range(self.__d)) # $V_i \gets e(v_4, (g_0 g_1^{\textit{id}_i})^s), \forall i \in \{1, 2, \cdots, d\}$
		cArray = self.__computeCoefficients(									\
			tuple(H4(VArray[i] * pair(g, g) ** (-s)) for i in range(self.__d))	\
		) # Compute $c_0, c_1, c_2, \cdots, c_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $G(x) = \prod\limits_{i = 1}^d (x - H_4(V_i \cdot e(g, g)^{-s})) = c_0 + \sum\limits_{i = 1}^d c_i x^i$
		ct5 = g ** r # $\textit{ct}_5 \gets g^r$
		ct6 = H5(																					\
			self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(		\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(sigma)), byteorder = "big"				\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)										\
		) ** r # $\textit{ct}_6 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots || c_d)^r$
		ct = (ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray, cArray) # $\textit{ct} \gets (\textit{ct}_1, \textit{ct}_2, \textit{ct}_3, \textit{ct}_4, \textit{ct}_5, \textit{ct}_6)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def Dec(self:object, dkidR:tuple, idR:Element, idS:Element, cipherText:tuple) -> int|bool: # $\textbf{Dec}(\textit{dk}_{\textit{id}_R}, \textit{id}_R, \textit{id}_S, \textit{ct}) \to m$
		# Checks #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
			if isinstance(dkidR, tuple) and len(dkidR) == 3 and all(isinstance(ele, Element) for ele in dkidR): # hybrid check
				dk_id_R = dkidR
			else:
				dk_id_R = self.DKGen(id_R)
				print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ should be a tuple containing 3 elements but it is not, which has been generated accordingly. ")
		else:
			id_R = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_id_R = self.DKGen(id_R)
			print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ has been generated accordingly. ")
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if (																																																										\
			isinstance(cipherText, tuple) and len(cipherText) == 9 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element) and isinstance(cipherText[5], Element)		\
			and all(isinstance(ele, tuple) and len(ele) >= 1 and all(isinstance(sEle, Element) and sEle.type == ZR for sEle in ele) for ele in cipherText[6:]) and len(cipherText[6]) == len(cipherText[7]) == len(cipherText[8])					\
		): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(id_S), id_R, int.from_bytes(b"SchemeIBMEMR", byteorder = "big"))
			print("Dec: The variable $\\textit{ct}$ should be a tuple containing 9 objects but it is not, which has been generated with $m$ set to b\"SchemeIBMEMR\". ")
		
		# Unpack #
		g, H1, H2, H3, H4, H5, HHat = self.__mpk[1], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]
		dk1, dk2, dk3 = dk_id_R
		ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray, cArray = ct
		
		# Scheme #
		if pair(																												\
			ct5, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(		\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(self.__group.random(ZR))), byteorder = "big"	\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)) 											\
		) == pair(ct6, g): # \textbf{if} $e(\textit{ct}_5, H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots c_d)) = e(\textit{ct}_6, g)$ \textbf{then}
			KPrimePrime = H4(pair(dk1, H1(id_S)) * pair(H2(id_R), ct1)) # \quad$K'' \gets H_4(e(\textit{dk}_1, H_1(\textit{id}_S)) \cdot e(H_2(\textit{id}_R), \textit{ct}_1))$
			RPrimePrime = H4(pair(dk2, ct2) * pair(dk3, ct3)) # \quad$R'' \gets H_4(e(\textit{dk}_2, \textit{ct}_2) \cdot e(\textit{dk}_3, \textit{ct}_3))$
			KPrime = self.__computePolynomial(KPrimePrime, aArray) # \quad$K' \gets \sum\limits_{i = 0}^d a_i K''^i$
			RPrime = self.__computePolynomial(RPrimePrime, bArray) # \quad$R' \gets \sum\limits_{i = 0}^d b_i R''^i$
			token = len(self.__group.serialize(self.__group.random(ZR)))
			m_sigma = (ct4 ^ HHat(KPrime) ^ HHat(RPrime)).to_bytes(((self.__group.secparam + 7) >> 3) + token, byteorder = "big") # \quad$m || \sigma \gets \textit{ct}_4 \oplus \hat{H}(K') \oplus \hat(H)(R')$
			r = H3(m_sigma) # \quad$r \gets H_3(m || \sigma)$
			if ct5 != g ** r: # \quad\textbf{if} $\textit{ct}_5 \neq g^r$ \textbf{then}
				m = False # \quad\quad$m \gets \perp$
			else:
				m = int.from_bytes(m_sigma[:-token], byteorder = "big")
			# \quad\textbf{end if}
		else: # \textbf{else}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def ReceiverVerify(self:object, cipherText:tuple, tdidR:tuple) -> bool: # $\textbf{ReceiverVerify}(\textit{ct}, \textit{td}_{\textit{id}_R}) \to y, y \in \{0, 1\}$
		# Checks #
		if (																																																										\
			isinstance(cipherText, tuple) and len(cipherText) == 9 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element) and isinstance(cipherText[5], Element)		\
			and all(isinstance(ele, tuple) and len(ele) >= 1 and all(isinstance(sEle, Element) and sEle.type == ZR for sEle in ele) for ele in cipherText[6:]) and len(cipherText[6]) == len(cipherText[7]) == len(cipherText[8])					\
		): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(self.__group.random(ZR)), self.__group.random(ZR), int.from_bytes(b"SchemeIBMEMR", byteorder = "big"))
			print("ReceiverVerify: The variable $\\textit{ct}$ should be a tuple containing 9 objects but it is not, which has been generated with $m$ set to b\"SchemeIBMEMR\". ")
		if isinstance(tdidR, tuple) and len(tdidR) == 2 and isinstance(tdidR[0], Element) and isinstance(tdidR[1], Element):
			td_id_R = tdidR
		else:
			td_id_R = self.TDKGen(self.__group.random(ZR))
			print("ReceiverVerify: The variable $\\textit{td}_{\textit{id}_R}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, H4, H5 = self.__mpk[1], self.__mpk[12], self.__mpk[13]
		ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray , cArray = ct
		td1, td2 = td_id_R
		
		# Scheme #
		if pair(																												\
			ct5, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(		\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(self.__group.random(ZR))), byteorder = "big"	\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)) 											\
		) == pair(ct6, g): # \textbf{if} $e(\textit{ct}_5, H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots c_d)) = e(\textit{ct}_6, g)$ \textbf{then}
			VPrime = H4(pair(td1, ct2) * pair(td2, ct3)) # \quad$V' \gets H_4(e(\textit{td}_1, \textit{ct}_2) \cdot e(\textit{td}_2, \textit{ct}_3))$
			y = self.__computePolynomial(VPrime, cArray) == self.__group.init(ZR, 0) # \quad$y \gets \sum\limits_{i = 0}^d c_i V'^i = 0$
		else: # \textbf{else}
			y = False # \quad$y \gets 0$
		# \textbf{end if}
		
		# Return #
		return y # \textbf{return} $y$
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


def conductScheme(curveParameter:tuple|list|dict|str, d:int = 30, run:int|None = None, isVerbose:bool = True) -> list:
	# Begin #
	curveName, securityParameter, dString, runString = "N/A", 512, "N/A", "N/A" # the default value of the security parameter in the Python charm library is 512
	isSystemValid, isSchemeCorrect, isTracingVerified = False, False, False
	timeSetup, timeEKGen, timeDKGen, timeTDKGen, timeEnc, timeDec, timeReceiverVerify = ("N/A", ) * 7
	sizeZR, sizeG1G2, sizeGT = ("N/A", ) * 3
	sizeMpk, sizeMsk, sizeEkIdS, sizeDkIdR, sizeTdIdR, sizeCt = ("N/A", ) * 6
	
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
	if isinstance(d, int):
		dString = d
	else:
		flag = False
	if isinstance(run, int) and run >= 1:
		runString = run
	if not isinstance(isVerbose, bool) or isVerbose:
		print("Curve: ({0}, {1})".format(curveName, securityParameter))
		print("$d$:", dString)
		print("run:", runString)
	if flag and d >= 1:
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
		print("Is the system valid? No. The parameter $d$ should be a positive integer. ")
		print()
	
	# Execution #
	if isSystemValid:
		# Initialization #
		schemeIBMEMR = SchemeIBMEMR(group)
		sizeZR, sizeG1G2, sizeGT = schemeIBMEMR.getLengthOf(group.random(ZR)), schemeIBMEMR.getLengthOf(group.random(G1)), schemeIBMEMR.getLengthOf(group.random(GT))
		
		# Setup #
		startTime = perf_counter()
		mpk, msk = schemeIBMEMR.Setup(d = d)
		endTime = perf_counter()
		timeSetup = endTime - startTime
		sizeMpk, sizeMsk = schemeIBMEMR.getLengthOf(mpk), schemeIBMEMR.getLengthOf(msk)
		
		# EKGen #
		startTime = perf_counter()
		id_S = group.random(ZR)
		ek_id_S = schemeIBMEMR.EKGen(id_S)
		endTime = perf_counter()
		timeEKGen = endTime - startTime
		sizeEkIdS = schemeIBMEMR.getLengthOf(ek_id_S)
		
		# DKGen #
		startTime = perf_counter()
		id_R = group.random(ZR)
		dk_id_R = schemeIBMEMR.DKGen(id_R)
		endTime = perf_counter()
		timeDKGen = endTime - startTime
		sizeDkIdR = schemeIBMEMR.getLengthOf(dk_id_R)
		
		# TDKGen #
		startTime = perf_counter()
		td_id_R = schemeIBMEMR.TDKGen(id_R)
		endTime = perf_counter()
		timeTDKGen = endTime - startTime
		sizeTdIdR = schemeIBMEMR.getLengthOf(td_id_R)
		
		# Enc #
		startTime = perf_counter()
		message = int.from_bytes(b"SchemeIBMEMR", byteorder = "big")
		ct = schemeIBMEMR.Enc(ek_id_S, id_R, message)
		endTime = perf_counter()
		timeEnc = endTime - startTime
		sizeCt = schemeIBMEMR.getLengthOf(ct)
		
		# Dec #
		startTime = perf_counter()
		m = schemeIBMEMR.Dec(dk_id_R, id_R, id_S, ct)
		endTime = perf_counter()
		isSchemeCorrect = not isinstance(m, bool) and m == message
		timeDec = endTime - startTime
		
		# ReceiverVerify #
		startTime = perf_counter()
		isTracingVerified = schemeIBMEMR.ReceiverVerify(ct, td_id_R)
		endTime = perf_counter()
		timeReceiverVerify = endTime - startTime
		
		# Destruction #
		del schemeIBMEMR
		if not isinstance(isVerbose, bool) or isVerbose:
			print("Original:", message)
			print("Decrypted:", m)
			print("Is the scheme correct (m == message)? {0}. ".format("Yes" if isSchemeCorrect else "No"))
			print("Is the tracing verified? {0}. ".format("Yes" if isTracingVerified else "No"))
			print("Time:", (timeSetup, timeEKGen, timeDKGen, timeTDKGen, timeEnc, timeDec, timeReceiverVerify))
			print("Space:", (sizeZR, sizeG1G2, sizeGT, sizeMpk, sizeMsk, sizeEkIdS, sizeDkIdR, sizeTdIdR, sizeCt))
			print()
	
	# End #
	return [																				\
		curveName, securityParameter, dString, runString, 									\
		isSystemValid, isSchemeCorrect, isTracingVerified, 									\
		timeSetup, timeEKGen, timeDKGen, timeTDKGen, timeEnc, timeDec, timeReceiverVerify, 	\
		sizeZR, sizeG1G2, sizeGT, 															\
		sizeMpk, sizeMsk, sizeEkIdS, sizeDkIdR, sizeTdIdR, sizeCt							\
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
			queries = ("curveParameter", "secparam", "d", "runCount")
			validators = ("isSystemValid", "isSchemeCorrect", "isTracingVerified")
			metrics = (																								\
				"Setup (s)", "EKGen (s)", "DKGen (s)", "TDKGen (s)", "Enc (s)", "Dec (s)", "ReceiverVerify (s)", 	\
				"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 											\
				"mpk (B)", "msk (B)", "ek_id_S (B)", "dk_id_R (B)", "td_id_R (B)", "ct (B)"							\
			)
			
			# Scheme #
			columns, qLength, results = queries + validators + metrics, len(queries), []
			length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
			saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
			try:
				for curveParameter in curveParameters:
					for d in range(5, 31, 5):
						averages = conductScheme(curveParameter, d = d, run = 1)
						for run in range(2, runCount + 1):
							result = conductScheme(curveParameter, d = d, run = run)
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