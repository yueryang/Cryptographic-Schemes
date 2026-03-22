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
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
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
	__SchemeName = "SchemePBAC" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the PBAC cryptographic scheme in Python programming language based on the Python charm library. ")
		print()
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for text-based outputs. The default value is {1}. ".format(self.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding))
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
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \to (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		s, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $s, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \to \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \to \mathbb{G}_1$
		H3 = lambda x1, x2, x3:self.__group.hash(																	\
			self.__group.serialize(x1) + self.__group.serialize(x2) + (self.__group.serialize(x3) if isinstance(x3, Element) else (		\
				x3.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") if isinstance(x3, int) else bytes(x3)				\
			)), ZR																							\
		) # $H_3: \mathbb{G}_T^2 \times \{0, 1\}^\lambda \to \mathbb{Z}_r$
		if 512 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H4 = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * ceil(self.__group.secparam / 512), byteorder = "big") & self.__operand # $H_4: \{0, 1\}^* \to \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \to \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \to \mathbb{G}_1$
		gHat = g ** s # $\hat{g} \gets g^s$
		self.__mpk = (g, gHat, H1, H2, H3, H4, H5, H6) # $ \textit{mpk} \gets (g, \hat{g}, H_1, H_2, H_3, H_4, H_5, H_6)$
		self.__msk = (s, alpha) # $\textit{msk} \gets (s, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, idS:bytes) -> Element: # $\textbf{SKGen}(\textit{id}_S) \to \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("SKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def RKGen(self:object, idR:bytes) -> tuple: # $\textbf{RKGen}(\textit{id}_R) \to \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("RKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
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
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element): # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
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
			m = int.from_bytes(b"SchemePBAC", byteorder = "big") & self.__operand
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemePBAC\". ")
		
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
		# Check #
		if not self.__flag:
			print("PKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``PKGen`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(ekid2, Element): # type check
				ek_id_2 = ekid2
			else:
				ek_id_2 = self.SKGen(id_2)
				print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element but it is not, which has been generated accordingly. ")
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			ek_id_2 = self.SKGen(id_2)
			print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.RKGen(id_2)
			print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
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
		# Check #
		if not self.__flag:
			print("ProxyEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ProxyEnc`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all(isinstance(ele, bytes) for ele in reKey[:2]) and all(isinstance(ele, tuple) for ele in reKey[-2:]): # hybrid check
			rk, id2Generated = reKey, reKey[1]
		else:
			rk = self.PKGen(																														\
				self.SKGen(id2Generated), self.RKGen(id2Generated), randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), 	\
				id2Generated, randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")										\
			)
			print("ProxyEnc: The variable $\\textit{rk}$ should be a tuple containing 2 ``bytes`` object and 2 tuples but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("ProxyEnc: The variable $C$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
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
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_2 = self.RKGen(id_2)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id_2, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("Dec1: The variable $C$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
		
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
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all(isinstance(ele, Element) for ele in dkid3): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.RKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_3 = self.RKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if (																																\
			isinstance(cipherText, tuple) and len(cipherText) == 7 and isinstance(cipherText[0], bytes) and all(isinstance(ele, Element) for ele in cipherText[1:4])		\
			and isinstance(cipherText[4], int) and isinstance(cipherText[5], bytes) and isinstance(cipherText[6], bytes)										\
		): # hybrid check
			CT = cipherText
		elif isinstance(cipherText, bool):
			return False
		else:
			CT = self.ProxyEnc(self.PKGen(self.SKGen(id_2), self.RKGen(id_2), id_1, id_2, id_3), self.Enc(self.SKGen(id_1), id_2, b"SchemePBAC"))
			print("Dec2: The variable $\\textit{CT}$ should be a tuple containing 7 objects but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
		
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


def conductScheme(curveParameter:tuple|list|str, run:int|None = None) -> list:
	# Begin #
	try:
		if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int):
			if curveParameter[1] >= 1:
				group = PairingGroup(curveParameter[0], secparam = curveParameter[1])
			else:
				group = PairingGroup(curveParameter[0])
		else:
			group = PairingGroup(curveParameter)
		pair(group.random(G1), group.random(G1))
	except BaseException as e:
		if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int):
			print("curveParameter =", curveParameter[0])
			if curveParameter[1] >= 1:
				print("secparam =", curveParameter[1])
		elif isinstance(curveParameter, str):
			print("curveParameter =", curveParameter)
		else:
			print("curveParameter = Unknown")
		if isinstance(run, int) and run >= 1:
			print("run =", run)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveParameter[0], curveParameter[1]] if isinstance(curveParameter, (tuple, list)) and len(curveParameter) == 2 and isinstance(curveParameter[0], str) and isinstance(curveParameter[1], int) else [curveParameter if isinstance(curveParameter, str) else None, None])		\
			+ [run if isinstance(run, int) and run >= 1 else None] + [False] * 4 + ["N/A"] * 20																																	\
		)
	print("curveParameter =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemePBAC = SchemePBAC(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemePBAC.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	id_1 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	id_2 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_id_1 = schemePBAC.SKGen(id_1)
	ek_id_2 = schemePBAC.SKGen(id_2)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# RKGen #
	startTime = perf_counter()
	id_3 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_id_2 = schemePBAC.RKGen(id_2)
	dk_id_3 = schemePBAC.RKGen(id_3)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemePBAC", byteorder = "big")
	C = schemePBAC.Enc(ek_id_1, id_2, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# PKGen #
	startTime = perf_counter()
	rk = schemePBAC.PKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ProxyEnc #
	startTime = perf_counter()
	CT = schemePBAC.ProxyEnc(rk, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemePBAC.Dec1(dk_id_2, id_2, id_1, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemePBAC.Dec2(dk_id_3, id_3, id_2, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(CT, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																																	\
		schemePBAC.getLengthOf(group.random(ZR)), schemePBAC.getLengthOf(group.random(G1)), schemePBAC.getLengthOf(group.random(GT)), 						\
		schemePBAC.getLengthOf(mpk), schemePBAC.getLengthOf(msk), schemePBAC.getLengthOf(ek_id_1), schemePBAC.getLengthOf(ek_id_2), 						\
		schemePBAC.getLengthOf(dk_id_2), schemePBAC.getLengthOf(dk_id_3), schemePBAC.getLengthOf(C), schemePBAC.getLengthOf(rk), schemePBAC.getLengthOf(CT)	\
	]
	del schemePBAC
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ProxyEnc`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
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
		curveParameters = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveParameter", "secparam", "runCount")
		validators = ("isSystemValid", "isProxyEncPassed", "isDec1Passed", "isDec2Passed")
		metrics = (																											\
			"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "PKGen (s)", "ProxyEnc (s)", "Dec1 (s)", "Dec2 (s)", 			\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 														\
			"mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "C (B)", "rk (B)", "CT (B)"	\
		)
	
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
		try:
			for curveParameter in curveParameters:
				averages = conductScheme(curveParameter, run = 1)
				for run in range(2, runCount + 1):
					result = conductScheme(curveParameter, run = run)
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
			print(os.linesep + "The experiments were interrupted by users. Saved results are retained. ")
		except BaseException as e:
			print("The experiments were interrupted by {0}. Saved results are retained. ".format(repr(e)))
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