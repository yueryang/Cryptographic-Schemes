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
	__SchemeName = "SchemeIBPME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is a possible implementation of the IBPME cryptographic scheme in Python programming language based on the Python charm library. \n")
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

class SchemeIBPME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __hash(self:object, *objs:tuple, bitLength:int|None = None) -> bytes:
		# bytes #
		bytesToBeHashed = b""
		for obj in objs:
			bytesToBeHashed += self.__group.serialize(obj) if isinstance(obj, Element) else bytes(obj)
		
		# length #
		length = bitLength if isinstance(bitLength, int) and bitLength >= 1 else self.__group.secparam
		
		# convert #
		if 512 == length:
			return sha512(bytesToBeHashed).digest()
		elif 384 == length:
			return sha384(bytesToBeHashed).digest()
		elif 256 == length:
			return sha256(bytesToBeHashed).digest()
		elif 224 == length:
			return sha224(bytesToBeHashed).digest()
		elif 160 == length:
			return sha1(bytesToBeHashed).digest()
		elif 128 == length:
			return md5(bytesToBeHashed).digest()
		else:
			return (int.from_bytes(sha512(bytesToBeHashed).digest() * ceil(length / 512), byteorder = "big") & ((1 << length) - 1)).to_bytes(ceil(length / 8))
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		gHat = self.__group.init(G2, 1) # $\hat{g} \gets 1_{\mathbb{G}_2}$
		s, alpha, beta_0, beta_1 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, \alpha, \beta_0, \beta_1 \in \mathbb{Z}_r$ randomly
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		f = g ** beta_0 # $f \gets g^{\beta_0}$
		fHat = gHat ** beta_0 # $\hat{f} \gets \hat{g}^{\beta_0}$
		h = g ** beta_1 # $h \gets g^{\beta_1}$
		hHat = gHat ** beta_1 # $\hat{h} \gets \hat{g}^{\beta_1}$
		H = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G2) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_2$
		H3 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_3: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H4 = lambda x1, x2 = b"", x3 = b"":self.__hash(x1, x2, x3, self.__group.secparam) # $H_4: \{0, 1\}^\lambda \times \mathbb{G}_T^2 \times \mathbb{G}_1^2 \rightarrow \{0, 1\}^\lambda$
		if self.__group.secparam not in (128, 160, 224, 256, 384, 512):
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H5 = lambda x1, x2 = b"", x3 = b"", x4 = b"", x5 = b"":self.__hash(x1, x2, x3, x4, x5, self.__group.secparam) # $H_5: \{0, 1\}^\lambda \times \mathbb{G}_T^2 \times \mathbb{G}_1^2 \rightarrow \{0, 1\}^\lambda$
		H6 = lambda x:self.__hash(x, self.__group.secparam * 3) # $H_6: \mathbb{G}_T \rightarrow \{0, 1\}^{3\lambda}$
		H7 = lambda x:self.__hash(x, self.__group.secparam << 1) # $H_7: \mathbb{G}_T \rightarrow \{0, 1\}^{2\lambda}$
		self.__mpk = (g, gHat, g1, f, h, fHat, hHat, H, H1, H2, H3, H4, H5, H6, H7) # $ \textit{mpk} \gets (g, \hat{g}, g_1, f, h, \hat{f}, \hat{h}, H, H_1, H_2, H_3, H_4, H_5, H_6, H_7)$
		self.__msk = (s, alpha) # $\textit{msk} \gets (s, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, snd:bytes) -> Element: # $\textbf{SKGen}(\sigma) \rightarrow \textit{ek}_\sigma$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("SKGen: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[8]
		s, alpha = self.__msk
		
		# Scheme #
		ek_sigma = H1(sigma) ** s # $\textit{ek}_\sigma \gets H_1(\sigma)^s$
		
		# Return #
		return ek_sigma # \textbf{return} $\textit{ek}_\sigma$
	def RKGen(self:object, rcv:bytes) -> tuple: # $\textbf{RKGen}(\rho) \rightarrow \textit{dk}_\rho$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(rcv, bytes): # type check
			rho = rcv
		else:
			rho = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("RKGen: The variable $\\rho$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[9]
		s, alpha = self.__msk
		
		# Scheme #
		d1 = H2(rho) ** s # $d_1 \gets H_2(\rho)^s$
		d2 = H2(rho) ** alpha # $d_2 \gets H_2(\rho)^\alpha$
		dk_rho = (d1, d2) # $\textit{dk}_\rho \gets (d_1, d_2)$
		
		# Return #
		return dk_rho # \textbf{return} $\textit{dk}_\rho$
	def PKGen(self:object, dkrho:Element, snd:bytes) -> tuple: # $\textbf{PKGen}(\textit{dk}_\rho, \sigma) \rightarrow \textit{pdk}_{\rho, \sigma}$
		# Check #
		if not self.__flag:
			print("PKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``PKGen`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("PKGen: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		gHat, fHat, hHat, H, H1, H3 = self.__mpk[1], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[10]
		d1, d2 = dk_rho
		
		# Scheme #
		y = self.__group.random(ZR) # generate $y \gets \mathbb{Z}_r$ randomly
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		y1 = d2 ** H3(eta) * (fHat * hHat ** H(eta)) ** y # $y_1 \gets d_2^{H_3(\eta)}(\hat{f}\hat{h}^{H(\eta)})^y$
		y2 = gHat ** y # $y_2 \gets \hat{g}^y$
		pdk = (y1, y2) # $\textit{pdk}_{(\rho, \sigma)} \gets (y_1, y_2)$
		
		# Return #
		return pdk # \textbf{return} $\textit{pdk}_{(\rho, \sigma)}$
	def Enc(self:object, eksigma:Element, rcv:bytes, message:int|bytes) -> tuple: # $\textbf{Enc}(\textit{ek}_\sigma, \textit{id}_2, m) \rightarrow C$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(eksigma, Element): # type check
			ek_sigma = eksigma
		else:
			ek_sigma = self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_\\sigma$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(rcv, bytes): # type check
			rho = rcv
		else:
			rho = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\rho$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBPME", byteorder = "big") & self.__operand
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBPME\". ")
		
		# Unpack #
		g, g1, f, h, H, H2, H3, H4, H5, H6 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[7], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13]
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		eta = pair(ek_sigma, H2(rho)) # $\eta \gets e(\textit{ek}_\sigma, H_2(\rho))$
		K_R = pair(g1, H2(rho)) ** (r * H3(eta)) # $K_R \gets e(g_1, H_2(\rho))^{r \cdot H_3(\eta)}$
		C1 = g ** r # $C_1 \gets g^r$
		C2 = (f * h ** H(eta)) ** r # $C_2 \gets (fh^{H(\eta)})^r$
		K_C = H4(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), eta, K_R) # $K_C \gets H_4(m, \eta, K_R)$
		Y = H5(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), K_C, K_R, C1, C2) # $Y \gets H_5(m, K_C, K_R, C_1, C_2)$
		C3 = int.from_bytes(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") + K_C + Y, byteorder = "big") ^ int.from_bytes(H6(K_R), byteorder = "big") # $C_3 \gets (m || K_C || Y) \oplus H_6(K_R)$
		C = (C1, C2, C3) # $C \gets (C_1, C_2, C_3)$
		
		# Return #
		return C # \textbf{return} $C$
	def ProxyDec(self:object, _pdk:tuple, cipher:tuple) -> tuple|bool: # $\textbf{ProxyDec}(\textit{pdk}, C) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("ProxyDec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ProxyDec`` subsequently. ")
			self.Setup()
		if isinstance(_pdk, tuple) and len(_pdk) == 2 and all(isinstance(ele, Element) for ele in _pdk): # hybrid check
			pdk = _pdk
		else:
			pdk = self.PKGen(																						\
				self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 		\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")					\
			)
			print("ProxyDec: The variable $\\textit{pdk}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and all(isinstance(ele, Element) for ele in cipher[:2]) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(																								\
				self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
			)
			print("ProxyDec: The variable $C$ should be a tuple containing 2 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H5, H6, H7 = self.__mpk[12], self.__mpk[13], self.__mpk[14]
		y1, y2 = pdk
		C1, C2, C3 = C
		
		# Scheme #
		K_R = pair(C1, y1) / pair(C2, y2) # $K_R \gets e(C_1, y_1) / e(C_2, y_2)$
		m_KC_Y = C3 ^ int.from_bytes(H6(K_R), byteorder = "big") # $m || K_C || Y \gets C_3 \oplus H_6(K_R)$
		token = ceil(self.__group.secparam / 8)
		m_KC_Y = m_KC_Y.to_bytes(token * 3, byteorder = "big")
		m_KC, Y = m_KC_Y[:-token], m_KC_Y[-token:]
		if Y == H5(m_KC, K_R, C1, C2): # \textbf{if} $Y = H_5(m, K_C, K_R, C_1, C_2) $\textbf{then}
			CT1 = C1 # \quad$\textit{CT}_1 \gets C_1$
			CT2 = int.from_bytes(m_KC, byteorder = "big") ^ int.from_bytes(H7(K_R), byteorder = "big") # \quad$\textit{CT}_2 \gets (m || K_C) \oplus H_7(K_R)$
			CT = (CT1, CT2) # \quad$\textit{CT} \gets (\textit{CT}_1, \textit{CT}_2)$
		else: # \textbf{else}
			CT = False # \quad$\textit{CT} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec1(self:object, dkrho:tuple, snd:bytes, cipher:tuple) -> int|bool: # $\textbf{Dec}_1(\textit{dk}_\rho, \sigma, C) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Dec1: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and all(isinstance(ele, Element) for ele in cipher[:2]) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(																								\
				self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
			)
			print("Dec1: The variable $C$ should be a tuple containing 2 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H1, H3, H4, H5, H6 = self.__mpk[8], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13]
		d1, d2 = dk_rho
		C1, C2, C3 = C
		
		# Scheme #
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		K_R = pair(C1, d2 ** H3(eta)) # $K_R \gets e(C_1, d_2^{H_3(\eta)})$
		m_KC_Y = C3 ^ int.from_bytes(H6(K_R), byteorder = "big") # $m || K_C || Y \gets C_3 \oplus H_6(K_R)$
		token = ceil(self.__group.secparam / 8)
		m_KC_Y = m_KC_Y.to_bytes(token * 3, byteorder = "big")
		m, K_C, Y = m_KC_Y[:token], m_KC_Y[token:-token], m_KC_Y[-token:]
		if K_C != H4(m, eta, K_R) or Y != H5(m, K_C, K_R, C1, C2): # \textbf{if} $K_C \neq H_4(m, \eta, K_R) \lor Y \neq H_5(m, K_C, K_R, C_1, C_2) $\textbf{then}
			m = False # \quad$m \gets \perp$
		else:
			m = int.from_bytes(m, byteorder = "big")
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkrho:tuple, snd:bytes, cipherText:tuple) -> int|bool: # $\textbf{Dec}_2(\textit{dk}_\rho, \sigma, \textit{CT}) \rightarrow m'$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Dec2: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 2 and isinstance(cipherText[0], Element) and isinstance(cipherText[1], int): # hybrid check
			CT = cipherText
		elif isinstance(cipherText, bool):
			return False
		else:
			CT = self.ProxyDec(																							\
				self.PKGen(																								\
					self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
					randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")						\
				), self.Enc(																								\
					self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
					randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
				)																										\
			)
			print("Dec2: The variable $\\textit{CT}$ should be a tuple containing an element and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H1, H3, H4, H7 = self.__mpk[8], self.__mpk[10], self.__mpk[11], self.__mpk[14]
		d1, d2 = dk_rho
		CT1, CT2 = CT
		
		# Scheme #
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		K_R = pair(CT1, d2 ** H3(eta)) # $K_R \gets e(C_1, d_2^{H_3(\eta)})$
		m_KC = CT2 ^ int.from_bytes(H7(K_R), byteorder = "big") # $m || K_C \gets \textit{CT}_2 \oplus H_7(K_R)$
		token = ceil(self.__group.secparam / 8)
		m_KC = m_KC.to_bytes(token << 1, byteorder = "big")
		m, K_C = m_KC[:-token], m_KC[-token:]
		if K_C != H4(m, eta, K_R): # \textbf{if} $K_C \neq H_4(m, \eta, K_R) $\textbf{then}
			m = False # \quad$m \gets \perp$
		else:
			m = int.from_bytes(m, byteorder = "big")
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
		elif isinstance(obj, int):
			return ceil(ceil(log(obj + 1, 256)) / (self.__group.secparam >> 3)) * (self.__group.secparam >> 3)
		elif callable(obj):
			if self.__mpk and obj == self.__mpk[13]: # H6
				return (self.__group.secparam >> 3) * 3
			elif self.__mpk and obj == self.__mpk[14]: # H7
				return self.__group.secparam >> 2
			else:
				return self.__group.secparam >> 3
		else:
			return -1


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
			+ [run if isinstance(run, int) and run >= 1 else None] + [False] * 4 + ["N/A"] * 19																																	\
		)
	print("curveParameter =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBPME = SchemeIBPME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	sigma = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_sigma = schemeIBPME.SKGen(sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# RKGen #
	startTime = perf_counter()
	rho = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_rho = schemeIBPME.RKGen(rho)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# PKGen #
	startTime = perf_counter()
	pdk = schemeIBPME.PKGen(dk_rho, sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBPME", byteorder = "big")
	C = schemeIBPME.Enc(ek_sigma, rho, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
		
	# ProxyDec #
	startTime = perf_counter()
	CT = schemeIBPME.ProxyDec(pdk, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemeIBPME.Dec1(dk_rho, sigma, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemeIBPME.Dec2(dk_rho, sigma, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(CT, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																															\
		schemeIBPME.getLengthOf(group.random(ZR)), schemeIBPME.getLengthOf(group.random(G1)), schemeIBPME.getLengthOf(group.random(G2)), 				\
		schemeIBPME.getLengthOf(group.random(GT)), schemeIBPME.getLengthOf(mpk), schemeIBPME.getLengthOf(msk), schemeIBPME.getLengthOf(ek_sigma), 	\
		schemeIBPME.getLengthOf(dk_rho), schemeIBPME.getLengthOf(pdk), schemeIBPME.getLengthOf(C), schemeIBPME.getLengthOf(CT)						\
	]
	del schemeIBPME
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ProxyDec`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
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
		curveParameters = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveParameter", "secparam", "runCount")
		validators = ("isSystemValid", "isProxyDecPassed", "isDec1Passed", "isDec2Passed")
		metrics = (																									\
			"Setup (s)", "SKGen (s)", "RKGen (s)", "PKGen (s)", "Enc (s)", "ProxyDec (s)", "Dec1 (s)", "Dec2 (s)", 	\
			"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 							\
			"mpk (B)", "msk (B)", "ek_sigma (B)", "dk_rho (B)", "pdk (B)", "C (B)", "CT (B)"						\
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