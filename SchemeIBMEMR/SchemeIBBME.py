import os
from sys import argv, exit
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the Python ``charm`` library is not handled correctly. ")
	print("Please refer to https://github.com/JHUISI/charm if necessary.  ")
	print("Please press the enter key to exit (-2). ")
	try:
		input()
	except:
		print()
	print()
	exit(-2)
from codecs import lookup
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
	__SchemeName = "SchemeIBBME" # os.path.splitext(os.path.basename(__file__))[0]
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
	def __formatOption(self:object, option:tuple|list, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, (tuple, list)) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	def __printHelp(self:object) -> None:
		print("This is a possible implementation of the IBBME cryptographic scheme in Python programming language based on the Python charm library. \n")
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(Parser.__OptionHelp)))
		print("\t{0} [|.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(	\
			self.__formatOption(Parser.__OptionOutput), Parser.__SchemeName, repr(Parser.__DefaultOutputFileName)												\
		))
		print("\t{0} [s|ms|microsecond|ns|ps|0|3|6|9|12|...]\t\tSpecify the decimal place, which should be a non-negative integer. The default value is {1}. ".format(	\
			self.__formatOption(Parser.__OptionPlace), Parser.__DefaultPlace)																						\
		)
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the run count, which must be a positive integer. The default value is {1}. ".format(self.__formatOption(Parser.__OptionRun), Parser.__DefaultRun))
		print(																																							\
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(self.__formatOption(Parser.__OptionTime))	\
			+ "Passing nan, None, or inf requires users to manually press the enter key before exiting. The default value is {0}. ".format(Parser.__DefaultTime)		\
		)
		print("\t{0}\t\tIndicate to confirm the overwriting of the existing output file. \n".format(self.__formatOption(Parser.__OptionYes)))
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
						try:
							p = int(self.__arguments[index], 0)
							if p >= 0:
								decimalPlace = p
							else:
								flag = EOF
								buffers.append("Parser: The value [{0}] = {1} for the decimal place option should be a non-negative integer. ".format(index, p))
							del p
						except:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option cannot be recognized. ".format(index, repr(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionRun:
				index += 1
				if index < argumentCount:
					try:
						r = int(self.__arguments[index].replace("_", ""), 0)
						if r >= 1:
							runCount = r
						else:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the run count option should be a positive integer. ".format(index, r))
						del r
					except:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the run count option is invalid. ".format(index, repr(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the run count option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionTime:
				index += 1
				if index < argumentCount:
					if self.__arguments[index].strip().lower() in ("+inf", "inf", "n", "nan", "none"):
						waitingTime = float("inf")
					else:
						try:
							t = self.__arguments[index].replace("_", "")
							t = float(t) if "." in self.__arguments[index] or "e" in self.__arguments[index] else int(t, 0)
							if t >= 0:
								waitingTime = int(t) if t.is_integer() else t
							else:
								flag = EOF
								buffers.append("Parser: The value [{0}] = {1} for the waiting time option should be a non-negative value. ".format(index, t))
							del t
						except:
							flag = EOF
							buffers.append("Parser: The type of the value [{0}] = {1} for the waiting time option is invalid. ".format(index, repr(self.__arguments[index])))
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
			outputFilePath, overwritingConfirmed = outputFP, overwriting
			while outputFilePath and os.path.exists(outputFilePath):
				if os.path.isfile(outputFilePath):
					if not overwritingConfirmed:
						try:
							overwritingConfirmed = input("The file {0} exists. Overwrite the file or not [yN]? ".format(repr(outputFilePath))).upper() in ("Y", "YES", "1", "T", "TRUE")
						except:
							print()
				else:
					print("Parser: The path {0} exists not to be a regular file. ".format(repr(outputFilePath)))
				if overwritingConfirmed:
					break
				else:
					try:
						outputFilePath = self.__handlePath(input("Please specify a new output file path or leave it empty for console output: "))
					except:
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

class SchemeIBBME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
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
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec:
			element = vec[0]
			for ele in vec[1:]:
				element *= ele
			return element
		else:
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
	def Setup(self:object, l:int = 30) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(l, int) and l >= 1: # boundary check
			self.__l = l
		else:
			self.__l = 30
			print("Setup: The variable $l$ should be a positive integer but it is not, which has been defaulted to $30$. ")

		# Scheme #
		g, v = self.__group.random(G1), self.__group.random(G1) # generate $g, v \in \mathbb{G}_1$ randomly
		h = self.__group.random(G2) # generate $h \in \mathbb{G}_2$ randomly
		rVec1 = tuple(self.__group.random(ZR) for _ in range(self.__l + 1)) # generate $\vec{r}_1 = (r_{1, 0}, r_{1, 1}, \cdots, r{1, l}) \in \mathbb{Z}_r^{l + 1}$ randomly
		rVec2 = tuple(self.__group.random(ZR) for _ in range(self.__l + 1)) # generate $\vec{r}_2 = (r_{2, 0}, r_{2, 1}, \cdots, r{2, l}) \in \mathbb{Z}_r^{l + 1}$ randomly
		t1, t2, beta1, beta2, alpha, rho, b, tau = self.__group.random(ZR, 8) # generate $t_1, t_2, \beta_1, \beta_2, \alpha, \rho, b, \tau \in \mathbb{Z}_r$ randomly
		rVec = tuple(rVec1[i] + b * rVec2[i] for i in range(self.__l + 1)) # $\vec{r} \gets (r_0, r_1, \cdots, r_l) = \vec{r}_1 + b\vec{r}_2 = (r_{1, 0} + br_{2, 0}, r_{1, 1} + br_{2, 1}, \cdots, r_{1, l} + br_{2, l})$
		t = t1 + b * t2 # $t \gets t_1 + bt_2$
		beta = beta1 + b * beta2 # $\beta \gets \beta_1 + b\beta_2$
		RVec = tuple(g ** rVec[i] for i in range(self.__l + 1)) # $\vec{R} \gets g^{\vec{r}} = (g^{r_0}, g^{r_1}, \cdots, g^{r_l})$
		T = g ** t # $T \gets g^t$
		H0 = lambda x:self.__group.hash(x, G2) # $H_0: \{0, 1\}^* \rightarrow \mathbb{G}_2$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, ZR) # $H_2: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H3 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_3: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		self.__mpk = (																																															\
			v, v ** rho, g, g ** b, RVec, T, pair(g, h) ** beta, h, tuple(h ** rVec1[i] for i in range(l + 1)), tuple(h ** rVec2[i] for i in range(l + 1)), h ** t1, h ** t2, g ** (tau * beta), h ** (tau * beta1), h ** (tau * beta2), h ** (1 / tau), H0, H1, H2, H3	\
		) # $\textit{mpk} \gets (v, v^\rho, g, g^b, \vec{R}, T, e(g, h)^\beta, h, h^{\vec{r}_1}, h^{\vec{r}_2}, h^{t_1}, h^{t_2}, g^{\tau\beta}, h^{\tau\beta_1}, h^{\tau\beta_2}, h^{1/\tau}, H_0, H_1, H_2, H_3)$
		self.__msk = (h ** beta1, h ** beta2, alpha, rho) # $\textit{msk} \gets (h^{\beta_1}, h^{\beta_2}, \alpha, \rho)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, _idStar:bytes) -> Element: # $\textbf{EKGen}(\textit{id}^*) \rightarrow \textit{ek}_{\textit{id}^*}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
		if isinstance(_idStar, bytes): # type check
			idStar = _idStar
		else:
			idStar = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")
			print("EKGen: The variable $\textit{id}^*$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[17]
		alpha = self.__msk[2]
		
		# Scheme #
		ek_idStar = H1(idStar) ** alpha # $\textit{ek}_{\textit{id}^*} \gets H_1(\textit{id}^*)^\alpha$
		
		# Return #
		return ek_idStar # \textbf{return} $\textit{ek}_{\textit{id}^*}$
	def DKGen(self:object, _identity:bytes) -> Element: # $\textbf{DKGen}(\textit{id}) \rightarrow \textit{dk}_\textit{id}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
		if isinstance(_identity, bytes): # type check
			identity = _identity
		else:
			identity = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")
			print("DKGen: The variable $\textit{id}$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		h, hToThePowerOfR1, hToThePowerOfR2, hToThePowerOfT1, hToThePowerOfT2, H0, H2 = self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[16], self.__mpk[18]
		hToThePowerOfBeta1, hToThePowerOfBeta2, alpha, rho = self.__msk
		
		# Scheme #
		z = self.__group.random(ZR) # generate $z \in \mathbb{Z}_r$ randomly
		rtags = tuple(self.__group.random(ZR) for _ in range(self.__l)) # generate $\textit{rtags} = (\textit{rtag}_1, \textit{rtag}_2, \cdots, \textit{rtag}_l) \in \mathbb{Z}_r^l$ randomly
		dk1 = H0(identity) ** rho # $\textit{dk}_1 \gets H_0(\textit{id})^\rho$
		dk2 = H0(identity) ** alpha # $\textit{dk}_2 \gets H_0(\textit{id})^\alpha$
		dk3 = H0(identity) # $\textit{dk}_3 \gets H_0(\textit{id})$
		dk4 = hToThePowerOfBeta1 * hToThePowerOfT1 ** z # $\textit{dk}_4 \gets h^{\beta_1}(h^{t_1})^z$
		dk5 = hToThePowerOfBeta2 * hToThePowerOfT2 ** z # $\textit{dk}_5 \gets h^{\beta_2}(h^{t_2})^z$
		dk6 = h ** z # $\textit{dk}_6 \gets h^z$
		dk7 = tuple(																												\
			(hToThePowerOfT1 ** rtags[j - 1] * hToThePowerOfR1[j] / hToThePowerOfR1[0] ** (H2(identity) ** j)) ** z for j in range(1, self.__l + 1)		\
		) # $\textit{dk}_{7, j} \gets ((h^{t_1})^{\textit{rtag}_j}h^{r_{1, j}} / (h^{r_{1, 0}})^{H_2(\textit{id})^j})^z, \forall j \in \{1, 2, \cdots, l\}$
		dk8 = tuple(																												\
			(hToThePowerOfT2 ** rtags[j - 1] * hToThePowerOfR2[j] / hToThePowerOfR2[0] ** (H2(identity) ** j)) ** z for j in range(1, self.__l + 1)		\
		) # $\textit{dk}_{8, j} \gets ((h^{t_2})^{\textit{rtag}_j}h^{r_{2, j}} / (h^{r_{2, 0}})^{H_2(\textit{id})^j})^z, \forall j \in \{1, 2, \cdots, l\}$
		dk_id = (dk1, dk2, dk3, dk4, dk5, dk6, dk7, dk8, rtags) # $\textit{dk}_\textit{id} \gets (\textit{dk}_1, \textit{dk}_2, \cdots, \textit{dk}_8, \textit{rtags})$
		
		# Return #
		return dk_id # \textbf{return} $\textit{dk}_\textit{id}$
	def Enc(self:object, _S:tuple, ekidStar:Element, message:Element) -> tuple: # $\textbf{Enc}(S, \textit{ek}_{\textit{id}^*}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
		if isinstance(_S, tuple) and _S and all(isinstance(ele, bytes) for ele in _S): # hybrid check
			S = _S
		else:
			S = tuple(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big") for _ in range(self.__l))
			print("Enc: The variable $S$ should be a tuple containing $n = \\|S\\|$ ``bytes`` objects where the integer $n \\in [1, {0}]$ but it is not, which has been generated randomly with a length of $l = {0}$. ".format(self.__l))
		if isinstance(ekidStar, Element) and ekidStar.type == G1: # type check
			ek_idStar = ekidStar
		else:
			ek_idStar = self.EKGen(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big"))
			print("Enc: The variable $\textit{ek}_{\textit{id}^*}$ should be an element of $\\mathbb{G}_1$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $m$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		v, vToThePowerOfRho, g, gToThePowerOfB, R, T, eGHToThePowerOfBeta, H0, H2, H3 = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[16], self.__mpk[18], self.__mpk[19]
		n = len(S)
		
		# Scheme #
		y = self.__computeCoefficients(tuple(H2(ele) for ele in S)) # Compute $y_0, y_1, y_2, \cdots y_n$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $F(x) = \prod\limits_{\textit{id}_j \in S} (x - H_2(\textit{id}_j)) = y_0 + \sum\limits_{i = 1}^n y_i x^i$
		yVec = y + (self.__group.init(ZR, 0), ) * (self.__l - n) # $\vec{y} \gets (y_0, y_1, \cdots, y_n, y_{n + 1}, y_{n + 2}, \cdots, y_l) = (y_0, y_1, \cdots, y_n, 0, 0, \cdots, 0)$
		del y
		s, d2, ctag = self.__group.random(ZR, 3) # generate $s, d_2, \textit{ctag} \in \mathbb{Z}_r$ randomly
		C0 = m * eGHToThePowerOfBeta ** s # $C_0 \gets m \cdot e(g, h)^{\beta s}$
		C1 = g ** s # $C_1 \gets g^s$
		C2 = gToThePowerOfB ** s # $C_2 \gets g^{bs}$
		C3 = (T ** ctag * self.__product(tuple(R[i] ** yVec[i] for i in range(n + 1)))) ** (d2 * s) # $C_3 \gets \left(T^{\textit{ctag}}\prod\limits_{i = 0}^n (g^{r_i})^{y_i}\right)^{d_2 s}$
		C4 = v ** s # $C_4 \gets v^s$
		V_id = tuple(H3(pair(H0(S[i]), ek_idStar * gToThePowerOfB ** s * vToThePowerOfRho ** s)) for i in range(n)) # $V_{\textit{id}_i} \gets H_3(e(H_0(\textit{id}_i), \textit{ek}_{\textit{id}^*} \cdot g^{bs} \cdot v^{\rho s})), \forall \textit{id}_i \in S$
		bVec = self.__computeCoefficients(	\
			V_id, k = d2					\
		) # Compute $\vec{b} \gets (b_0, b_1, b_2, \cdots b_n)$ that satisfy $\forall y \in \mathbb{Z}_r$, we have $g(y) = \prod\limits_{V_{\textit{id}_k} \in V_{\textit{id}}} (y - V_{\textit{id}_k}) + d_2 = b_0 + \sum\limits_{k = 1}^n b_k y^k$
		ct = (C0, C1, C2, C3, C4, ctag, yVec, bVec) # $\textit{ct} \gets (C_0, C_1, C_2, C_3, C_4, \textit{ctag}, \vec{y}, \vec{b})$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def Dec(self:object, _S:tuple, dkidi:tuple, _idStar:bytes, cipherText:tuple) -> Element|bool: # $\textbf{Dec}(S, \textit{dk}_{\textit{id}_i}, \textit{id}^*, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
		if isinstance(_S, tuple) and _S and all(isinstance(ele, bytes) for ele in _S): # hybrid check
			S = _S
		else:
			S = tuple(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big") for _ in range(self.__l))
			print("Dec: The variable $S$ should be a tuple containing $n = \\|S\\|$ ``bytes`` objects where the integer $n \\in [1, {0}]$ but it is not, which has been generated randomly with a length of $l = {0}$. ".format(self.__l))
		if isinstance(dkidi, tuple) and len(dkidi) == 9 and all(isinstance(ele, Element) for ele in dkidi[:6]) and all(isinstance(ele, tuple) for ele in dkidi[6:]): # hybrid check
			dk_id_i = dkidi
		else:
			dk_id_i = self.DKGen(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big"))
			print("Dec: The variable $\\textit{dk}_{\textit{id}_i}$ should be a tuple containing 6 elements and 3 tuples but it is not, which has been generated randomly. ")
		if isinstance(_idStar, bytes): # type check
			idStar = _idStar
		else:
			idStar = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")
			print("Dec: The variable $\textit{id}^*$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 8 and all(isinstance(ele, Element) for ele in cipherText[:6]) and isinstance(cipherText[-2], tuple) and isinstance(cipherText[-1], tuple): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(S, self.EKGen(idStar), self.__group.random(GT))
			print("Dec: The variable $\\textit{ct}$ should be a tuple containing 6 elements and 2 tuples but it is not, which has been generated randomly. ")
		
		# Unpack #
		H0, H1, H3 = self.__mpk[16], self.__mpk[17], self.__mpk[19]
		n = len(S)
		dki1, dki2, dki3, dki4, dki5, dki6, dki7, dki8, rtags = dk_id_i
		C0, C1, C2, C3, C4, ctag, yVec, bVec = ct
		
		# Scheme #
		V_id_i = H3(pair(dki3, C2) * pair(dki2, H1(idStar)) * pair(dki1, C4)) # $V(\textit{id}_i) \gets H_3(e(\textit{dk}_{i, 3}, C_2)e(\textit{dk}_{i, 2}, H_1(\textit{id}^*))e(\textit{dk}_{i, 1}, C_4))$
		d2 = self.__computePolynomial(V_id_i, bVec) # $d_2 \gets g(V_{\textit{id}_i}) = b_0 + \sum\limits_{j = 1}^n b_j V_{\textit{id}_i}^j$
		rtag = sum((yVec[i + 1] * rtags[i] for i in range(1, self.__l)), start = yVec[1] * rtags[0]) # $\textit{rtag} \gets \sum\limits_{i = 1}^l y_i \textit{rtags}_i$
		if rtag == ctag: # \textbf{if} $\textit{rtag} = \textit{ctag}$ \textbf{then}
			m = False # \quad$m \gets \perp$
		else: # \textbf{else}
			A = (																																					\
				pair(C1, self.__product(tuple(dki7[j] ** yVec[j + 1] for j in range(self.__l)))) * pair(C2, self.__product(tuple(dki8[j] ** yVec[j + 1] for j in range(self.__l)))) / pair(C3 ** (1 / d2), dki6)	\
			) # \quad$A \gets e\left(C_1, \prod\limits_{j = 1}^l \textit{dk}_{7, j}^{y_j}\right)e\left(C_2, \prod\limits_{j = 1}^l \textit{dk}_{8, j}^{y_j}\right) / e(C_3^{1 / d_2}, \textit{dk}_6)$
			B = pair(C1, dki4) * pair(C2, dki5) # \quad$B \gets e(C_1, \textit{dk}_4) \cdot e(C_2, \textit{dk}_5)$
			m = C0 * A ** (1 / (rtag - ctag)) * B ** (-1) # \quad$m \gets C_0 \cdot A^{1 / (\textit{rtag} - \textit{ctag})} \cdot B^{-1}$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def getLengthOf(self:object, obj:Element|tuple|list|set|bytes|int) -> int:
		if isinstance(obj, Element):
			return len(self.__group.serialize(obj))
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(o) for o in obj)
			return -1 if -1 in sizes else sum(sizes)
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, int) or callable(obj):
			return (self.__group.secparam + 7) >> 3
		else:
			return -1


def conductScheme(curveType:tuple|list|str, l:int = 30, n:int = 10, _seed:int|None = None, run:int|None = None) -> list:
	# Begin #
	if isinstance(l, int) and isinstance(n, int) and 0 < n <= l: # no need to check the parameters for curve types here
		try:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				if curveType[1] >= 1:
					group = PairingGroup(curveType[0], secparam = curveType[1])
				else:
					group = PairingGroup(curveType[0])
			else:
				group = PairingGroup(curveType)
		except BaseException as e:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				print("curveType =", curveType[0])
				if curveType[1] >= 1:
					print("secparam =", curveType[1])
			elif isinstance(curveType, str):
				print("curveType =", curveType)
			else:
				print("curveType = Unknown")
			print("l =", l)
			print("n =", n)
			if isinstance(run, int) and run >= 1:
				print("run =", run)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
				+ [l if isinstance(l, int) else None, n if isinstance(n, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 2 + ["N/A"] * 14																					\
			)
		seed = _seed if isinstance(_seed, int) and 0 <= _seed < n else randbelow(n)
	else:
		print("Is the system valid? No. The parameter $l$ and $n$ should be two positive integers satisfying $1 \\leqslant n \\leqslant l$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [l if isinstance(l, int) else None, n if isinstance(n, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 2 + ["N/A"] * 14																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("l =", l)
	print("n =", n)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBBME = SchemeIBBME(group)
	timeRecords = []

	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBBME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	idStar = randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big")
	ek_idStar = schemeIBBME.EKGen(idStar)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	identity = randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big")
	dk_id = schemeIBBME.DKGen(identity)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	S = (																												\
		tuple(randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big") for _ in range(seed)) + (identity, )		\
		+ tuple(randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big") for _ in range(n - seed - 1))			\
	)
	message = group.random(GT)
	ct = schemeIBBME.Enc(S, ek_idStar, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	m = schemeIBBME.Dec(S, dk_id, idStar, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == m]
	spaceRecords = [																																							\
		schemeIBBME.getLengthOf(group.random(ZR)), schemeIBBME.getLengthOf(group.random(G1)), schemeIBBME.getLengthOf(group.random(G2)), schemeIBBME.getLengthOf(group.random(GT)), 	\
		schemeIBBME.getLengthOf(mpk), schemeIBBME.getLengthOf(msk), schemeIBBME.getLengthOf(ek_idStar), schemeIBBME.getLengthOf(dk_id), schemeIBBME.getLengthOf(ct)					\
	]
	del schemeIBBME
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, l, n, run if isinstance(run, int) and run >= 1 else None] + booleans + timeRecords + spaceRecords


def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "l", "n", "runCount")
		validators = ("isSystemValid", "isSchemeCorrect")
		metrics = (																			\
			"Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", 					\
			"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 	\
			"mpk (B)", "msk (B)", "ek_idStar (B)", "dk_id (B)", "ct (B)"					\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
		try:
			for curveType in curveTypes:
				for l in range(5, 31, 5):
					for n in range(5, l + 1, 5):
						averages = conductScheme(curveType, l = l, n = n, run = 1)
						for run in range(2, runCount + 1):
							result = conductScheme(curveType, l = l, n = n, run = run)
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
		except KeyboardInterrupt:
			print("\nThe experiments were interrupted by users. Saved results are retained. ")
		except BaseException as e:
			print("The experiments were interrupted by the following exceptions. Saved results are retained. \n\t{0}".format(e))
		errorLevel = EXIT_SUCCESS if results and all(all(																								\
			tuple(r == runCount for r in result[qLength:qvLength]) + tuple(isinstance(r, (float, int)) and r > 0 for r in result[qvLength:length])	\
		) for result in results) else EXIT_FAILURE
	elif EXIT_SUCCESS == flag:
		errorLevel = flag
	else:
		errorLevel = EOF
	try:
		if 0 == waitingTime:
			print("The execution of the Python script has finished ({0}). ".format(errorLevel))
		elif isinstance(waitingTime, (float, int)) and 0 < waitingTime < float("inf"):
			print("Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \"Ctrl + C\" ({1}). ".format(waitingTime, errorLevel))
			sleep(waitingTime)
		else:
			print("Please press the enter key to exit ({0}). ".format(errorLevel))
			input()
	except:
		print()
	print()
	return errorLevel



if "__main__" == __name__:
	exit(main())