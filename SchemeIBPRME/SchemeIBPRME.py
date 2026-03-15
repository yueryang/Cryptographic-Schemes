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
from math import ceil, log
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
	__SchemeName = "SchemeIBPRME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the IBPRME cryptographic scheme in Python programming language based on the Python charm library. \n")
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

class SchemeIBPRME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		try:
			pair(self.__group.random(G1), self.__group.random(G1))
		except:
			self.__group = PairingGroup("SS512", secparam = self.__group.secparam)
			print("Init: This scheme is only applicable to symmetric groups of prime orders. The curve type has been defaulted to \"SS512\". ")
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		h = self.__group.random(G1) # generate $h \in \mathbb{G}_1$ randomly
		x, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $x, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(x, G1) # $H_4: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H7 = lambda x:self.__group.hash(x, G1) # $H_7: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		y = g ** x # $y \gets g^x$
		self.__mpk = (g, h, H1, H2, H3, H4, H5, H6, H7, y) # $ \textit{mpk} \gets (G, G_T, q, g, e, h, H_1, H_2, H_3, H_4, H_5, H_6, H_7, y)$
		self.__msk = (x, alpha) # $\textit{msk} \gets (x, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def DKGen(self:object, idR:bytes) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("DKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		x, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H1(id_R) ** x # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^x$
		dk_id_R2 = H1(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 2} \gets H_1(\textit{id}_R)^\alpha$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def EKGen(self:object, idS:bytes) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("EKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[3]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H2(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_2(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def ReEKGen(self:object, ekid2:Element, dkid2:tuple, id1:bytes, id2:bytes, id3:bytes) -> tuple: # $\textbf{ReEKGen}(\textit{ek}_{\textit{id}_2}, \textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{id}_2, \textit{id}_3) \rightarrow \textit{rk}$
		# Check #
		if not self.__flag:
			print("ReEKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEKGen`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(ekid2, Element): # type check
				ek_id_2 = ekid2
			else:
				ek_id_2 = self.EKGen(id_2)
				print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element but it is not, which has been generated accordingly. ")
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.DKGen(id_2)
				print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("ReEKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			ek_id_2 = self.EKGen(id_2)
			print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.DKGen(id_2)
			print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("ReEKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("ReEKGen: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, h, H1, H2, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		
		# Scheme #
		N = self.__group.random(ZR) # generate $N \in \{0, 1\}^\lambda$ randomly
		xBar = self.__group.random(ZR) # generate $\bar{x} \in \mathbb{Z}_r$ randomly
		rk1 = g ** xBar # $\textit{rk}_1 \gets g^{\bar{x}}$
		rk2 = dk_id_2[0] * h ** xBar * H6(pair(y, H1(id_3)) ** xBar) # $\textit{rk}_2 \gets \textit{dk}_{\textit{id}_2, 1} h^{\bar{x}} H_6(e(y, H_1(\textit{id}_3))^{\bar{x}})$
		K = pair(ek_id_2, H1(id_3)) # $K \gets e(\textit{ek}_{\textit{id}_2}, H_1(\textit{id}_3))$
		rk3 = pair( # $\textit{rk}_3 \gets e(
			H2(id_1), # H_2(\textit{id}_1), 
			H7(self.__group.serialize(K) + id_2 + id_3 + self.__group.serialize(N)) * dk_id_2[1] # H_7(K || \textit{id}_2 || \textit{id}_3 || N) \cdot \textit{dk}_{\textit{id}_2, 2}
		) # )$
		rk = (N, rk1, rk2, rk3) # $\textit{rk} \gets (N, \textit{rk}_1, \textit{rk}_2, \textit{rk}_3)$
		
		# Return #
		return rk # \textbf{return} $\textit{rk}$
	def Enc(self:object, ekid1:Element, id2:Element, message:int|bytes) -> object: # $\textbf{Enc}(\textit{ek}_{\textit{id}_1}, \textit{id}_2, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element): # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_1}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBPRME", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBPRME\". ")
		
		# Unpack #
		g, h, H1, H3, H4, H5, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[-1]
		
		# Scheme #
		sigma = self.__group.random(G1) # generate $\sigma \in \mathbb{G}_1$ randomly
		eta = self.__group.random(GT) # generate $\eta \in \mathbb{G}_T$ randomly
		r = H3(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") + self.__group.serialize(sigma) + self.__group.serialize(eta)) # $r \gets H_3(m || \sigma || \eta)$
		ct1 = h ** r # $\textit{ct}_1 \gets h^r$
		ct2 = g ** r # $\textit{ct}_2 \gets g^r$
		ct3 = (
			int.from_bytes(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") + self.__group.serialize(sigma), byteorder = "big")
			^ int.from_bytes(self.__group.serialize(H4(pair(y, H1(id_2)) ** r)), byteorder = "big")
			^ int.from_bytes(self.__group.serialize(H4(eta)), byteorder = "big")
		) # $\textit{ct}_3 \gets (m || \sigma) \oplus H_4(e(y, H_1(\textit{id}_2))^r) \oplus H_4(\eta)$
		ct4 = eta * pair(ek_id_1, H1(id_2)) # $\textit{ct}_4 \gets \eta \cdot e(\textit{ek}_{\textit{id}_1}, H_1(\textit{id}_2))$
		ct5 = (																																												\
			H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4)) ** r		\
		) # $\textit{ct}_5 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)^r$
		ct = (ct1, ct2, ct3, ct4, ct5) # $\textit{ct} \gets (\textit{ct}_1, \textit{ct}_2, \textit{ct}_3, \textit{ct}_4, \textit{ct}_5)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def ReEnc(self:object, cipherText:tuple, reKey:tuple) -> tuple|bool: # $\textbf{ReEnc}(\textit{ct}, \textit{rk}) \rightarrow \textit{ct}'$
		# Check #
		if not self.__flag:
			print("ReEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEnc`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:2]) and isinstance(cipherText[2], int) and all(isinstance(ele, Element) for ele in cipherText[3:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemeIBPRME", byteorder = "big"))
			print("ReEnc: The variable $\\textit{ct}$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all(isinstance(ele, Element) for ele in reKey): # hybrid check
			rk = reKey
		else:
			rk = self.ReEKGen(																														\
				self.EKGen(id2Generated), self.DKGen(id2Generated), randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), 	\
				id2Generated, randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")										\
			)
			print("ReEnc: The variable $\\textit{rk}$ should be a tuple containing 4 elements but it is not, which has been generated randomly. ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H5, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		N, rk1, rk2, rk3 = rk
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																																																	\
			pair(ct1, g) == pair(h, ct2)																																											\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4))) == pair(h, ct5)	\
		): # \textbf{if} $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$ \textbf{then}
			ct4Prime = ct4 / rk3 # \quad$\textit{ct}_4' \gets \frac{\textit{ct}_4}{\textit{rk}_3}$
			ct6 = rk1 # \quad$\textit{ct}_6 \gets \textit{rk}_1$
			ct7 = pair(rk2, ct2) / pair(ct1, rk1) # \quad$\textit{ct}_7 \gets \frac{e(\textit{rk}_2, \textit{ct}_2)}{e(\textit{ct}_1, \textit{rk}_1)}$
			ctPrime = (ct2, ct3, ct4Prime, ct6, ct7, N) # \quad$\textit{ct}' \gets (\textit{ct}_2, \textit{ct}_3, \textit{ct}_4', \textit{ct}_6, \textit{ct}_7, N)$
		else: # \textbf{else}
			ctPrime = False # \quad$\textit{ct}' \gets \perp$
		# \textbf{end if}
		
		# Return #
		return ctPrime # \textbf{return} $\textit{ct}'$
	def Dec1(self:object, dkid2:tuple, id1:Element, cipherText:tuple) -> int|bool: # $\textbf{Dec}_1(\textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
			dk_id_2 = dkid2
		else:
			dk_id_2 = self.DKGen(id2Generated)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:2]) and isinstance(cipherText[2], int) and all(isinstance(ele, Element) for ele in cipherText[3:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemeIBPRME", byteorder = "big"))
			print("Dec1: The variable $\\textit{ct}$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H3, H4, H5, H6, H7, y = self.__mpk
		x = self.__msk[0]
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																																																		\
			pair(ct1, g) == pair(h, ct2)																																												\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4))) == pair(h, ct5)		\
		): # \textbf{if} $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$ \textbf{then}
			V = pair(dk_id_2[1], H2(id_1)) # \quad$V \gets e(\textit{dk}_{\textit{id}_2, 2}, H_2(\textit{id}_1))$
			etaPrime = ct4 / V # \quad$\eta' \gets \frac{\textit{ct}_4}{V}$
			ct3_H4_H4 = (																													\
				int.from_bytes(ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big"), byteorder = "big")	\
				^ int.from_bytes(self.__group.serialize(H4(pair(dk_id_2[0], ct2))), byteorder = "big")															\
				^ int.from_bytes(self.__group.serialize(H4(etaPrime)), byteorder = "big")																	\
			) # $\quad m || \sigma \gets \textit{ct}_3 \oplus H_4(e(\textit{dk}_{\textit{id}_2, 1}, \textit{ct}_2)) \oplus H_4(\eta')$
			token1, token2 = ceil(self.__group.secparam / 8), len(self.__group.serialize(self.__group.random(G1)))
			ct3_H4_H4 = ct3_H4_H4.to_bytes(token1 + token2, byteorder = "big")
			r = H3(ct3_H4_H4 + self.__group.serialize(etaPrime)) # \quad$r \gets H_3((\textit{ct}_3 \oplus H_4(e(\textit{dk}_{\textit{id}_2, 1})) \oplus H_4(\eta')) || \eta')$
			if g ** r != ct2: # \quad\textbf{if} $g^r = \textit{ct}_2$ \textbf{then}
				m = False # \quad\quad$m \gets \perp$
			else:
				m = int.from_bytes(ct3_H4_H4[:token1], byteorder = "big")
			# \quad\textbf{end if}
		else: # \textbf{else}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkid3:tuple, id1:Element, id2:Element, id3:Element, cipherTextPrime:tuple|bool) -> int|bool: # $\textbf{Dec}_2(\textit{dk}_{\textit{id}_3}, \textit{id}_1, \textit{id}_2, \textit{id}_3, \textit{ct}') \rightarrow m'$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all(isinstance(ele, Element) for ele in dkid3): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.DKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_3 = self.DKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherTextPrime, tuple) and len(cipherTextPrime) == 6 and isinstance(cipherTextPrime[0], Element) and isinstance(cipherTextPrime[1], int) and all(isinstance(ele, Element) for ele in cipherTextPrime[2:]): # hybrid check
			ctPrime = cipherTextPrime
		elif isinstance(cipherTextPrime, bool):
			return False
		else:
			ctPrime = self.ReEnc(self.Enc(self.EKGen(id_1), id_2, int.from_bytes(b"SchemeIBPRME", byteorder = "big")), self.ReEKGen(self.EKGen(id_2), self.DKGen(id_2), id_1, id_2, id_3))
			print("Dec2: The variable $\\textit{ct}'$ should be a tuple containing 5 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		
		# Unpack #
		g, h, H1, H2, H3, H4, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		ct2, ct3, ct4Prime, ct6, ct7, N = ctPrime
		
		# Scheme #
		V = pair(dk_id_3[1], H2(id_2)) # $V \gets e(\textit{dk}_{\textit{id}_3, 2}, H_2(\textit{id}_2))$
		etaPrime = ct4Prime * pair(H2(id_1), H7(self.__group.serialize(V) + id2 + id3 + self.__group.serialize(N))) # $\eta' \gets \textit{ct}_4' \cdot e(H_2(\textit{id}_1), H_7(V || \textit{id}_2 || \textit{id}_3 || N))$
		R = ct7 / pair(H6(pair(dk_id_3[0], ct6)), ct2) # $R \gets \frac{\textit{ct}_7}{e(H_6(e(\textit{dk}_{\textit{id}_3, 1}, \textit{ct}_6), \textit{ct}_2)}$
		ct3_H4_H4 = (																													\
			int.from_bytes(ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big"), byteorder = "big")	\
			^ int.from_bytes(self.__group.serialize(H4(R)), byteorder = "big")																		\
			^ int.from_bytes(self.__group.serialize(H4(etaPrime)), byteorder = "big")																	\
		) # $m || \sigma \gets \textit{ct}_3 \oplus H_4(R) \oplus H_4(\eta')$
		token1, token2 = ceil(self.__group.secparam / 8), len(self.__group.serialize(self.__group.random(G1)))
		ct3_H4_H4 = ct3_H4_H4.to_bytes(token1 + token2, byteorder = "big")
		r = H3(ct3_H4_H4 + self.__group.serialize(etaPrime)) # $r \gets H_3((\textit{ct}_3 \oplus H_4(R) \oplus H_4(\eta')) || \eta')$
		if g ** r != ct2: # \textbf{if} $g^r \neq \textit{ct}_2$ \textbf{then}
			m = False # \quad$m \gets \perp$
		else:
			m = ct3_H4_H4[:token1]
		# \textbf{end if}
		m = int.from_bytes(m, byteorder = "big")
		
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


def conductScheme(curveType:tuple|list|str, run:int|None = None) -> list:
	# Begin #
	try:
		if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
			if curveType[1] >= 1:
				group = PairingGroup(curveType[0], secparam = curveType[1])
			else:
				group = PairingGroup(curveType[0])
		else:
			group = PairingGroup(curveType)
		pair(group.random(G1), group.random(G1))
	except BaseException as e:
		if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
			print("curveType =", curveType[0])
			if curveType[1] >= 1:
				print("secparam =", curveType[1])
		elif isinstance(curveType, str):
			print("curveType =", curveType)
		else:
			print("curveType = Unknown")
		if isinstance(run, int) and run >= 1:
			print("run =", run)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																													\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])	\
			+ [run if isinstance(run, int) and run >= 1 else None] + [False] * 4 + ["N/A"] * 20																																\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBPRME = SchemeIBPRME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPRME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	id_2 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	id_3 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_id_2 = schemeIBPRME.DKGen(id_2)
	dk_id_3 = schemeIBPRME.DKGen(id_3)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# EKGen #
	startTime = perf_counter()
	id_1 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_id_1 = schemeIBPRME.EKGen(id_1)
	ek_id_2 = schemeIBPRME.EKGen(id_2)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# ReEKGen #
	startTime = perf_counter()
	rk = schemeIBPRME.ReEKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBPRME", byteorder = "big")
	ct = schemeIBPRME.Enc(ek_id_1, id_2, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ReEnc #
	startTime = perf_counter()
	ctPrime = schemeIBPRME.ReEnc(ct, rk)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemeIBPRME.Dec1(dk_id_2, id_1, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemeIBPRME.Dec2(dk_id_3, id_1, id_2, id_3, ctPrime)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(ctPrime, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																																					\
		schemeIBPRME.getLengthOf(group.random(ZR)), schemeIBPRME.getLengthOf(group.random(G1)), schemeIBPRME.getLengthOf(group.random(GT)), 								\
		schemeIBPRME.getLengthOf(mpk), schemeIBPRME.getLengthOf(msk), schemeIBPRME.getLengthOf(ek_id_1), schemeIBPRME.getLengthOf(ek_id_2), 								\
		schemeIBPRME.getLengthOf(dk_id_2), schemeIBPRME.getLengthOf(dk_id_3), schemeIBPRME.getLengthOf(rk), schemeIBPRME.getLengthOf(ct), schemeIBPRME.getLengthOf(ctPrime)	\
	]
	del schemeIBPRME
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ReEnc`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is ``Dec1`` passed (m == message)? {0}. ".format("Yes" if booleans[2] else "No"))
	print("Is ``Dec2`` passed (m\' == message)? {0}. ".format("Yes" if booleans[3] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, run if isinstance(run, int) and run >= 1 else None] + booleans + timeRecords + spaceRecords


def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "runCount")
		validators = ("isSystemValid", "isReEKGenPassed", "isDec1Passed", "isDec2Passed")
		metrics = (																												\
			"Setup (s)", "DKGen (s)", "EKGen (s)", "ReEKGen (s)", "Enc (s)", "ReEnc (s)", "Dec1 (s)", "Dec2 (s)", 				\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 															\
			"mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "rk (B)", "ct (B)", "ct\' (B)"	\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
		try:
			for curveType in curveTypes:
				averages = conductScheme(curveType, run = 1)
				for run in range(2, runCount + 1):
					result = conductScheme(curveType, run = run)
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