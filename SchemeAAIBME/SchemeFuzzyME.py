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
	def __formatOption(self:object, option:tuple|list, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, (tuple, list)) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	def __printHelp(self:object) -> None:
		print("This is a possible implementation of the Fuzzy-ME cryptography scheme in Python programming language based on the Python charm library. \n")
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(Parser.__OptionHelp)))
		print("\t{0} [|.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(	\
			self.__formatOption(Parser.__OptionOutput), Parser.__SchemeName, Parser.__DefaultOutputFileName														\
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
		self.__Writer = None
		self.__escape = None
		self.__dumpJSON = None
		self.__WorkbookXLS = None
		self.__styleXLS = None
		self.__WorkbookXLSX = None
		self.__alignmentXLSX = None
		self.__fontXLSX = None
		self.__columnsXML = None
		self.__dumpYAML = None
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
										writer = self.__Writer(f, fieldnames = self.__columns)
										writer.writeheader()
										writer.writerows(results)
								elif "HTML" == self.__extensionName:
									if self.__escape is None:
										self.__escape = __import__("html").escape
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
											f.write("\t\t\t\t\t<th>{0}</th>{1}".format(self.__escape(column, quote = True), os.linesep))
										f.write("\t\t\t\t</tr>{0}\t\t\t</thead>{0}\t\t\t<tbody>{0}".format(os.linesep))
										for result in results:
											f.write("\t\t\t\t<tr>{0}".format(os.linesep))
											for r in result:
												f.write("\t\t\t\t\t<td>{0}</td>{1}".format(self.__escape("{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else str(r), quote = True), os.linesep))
											f.write("\t\t\t\t</tr>{0}".format(os.linesep))
										f.write("\t\t\t</tbody>{0}\t\t</table>{0}\t</body>{0}</html>".format(os.linesep))
								elif "JSON" == self.__extensionName:
									if self.__dumpJSON is None:
										self.__dumpJSON = __import__("json").dump
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										self.__dumpJSON({"columns":self.__columns, "results":results}, f, indent = "\t")
								elif "TEX" == self.__extensionName:
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										maxLength = max(len(self.__columns) if isinstance(self.__columns, (tuple, list)) else 0, max(len(result) for result in results))
										f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{graphicx}\n\\usepackage{booktabs}\n")
										f.write("\\usepackage{rotating}\n\n\\begin{document}\n\n\\begin{sidewaystable}\n\t\\caption{The comparison results. }\n")
										f.write("\t\\centering\n\t\\resizebox{\\textwidth}{!}{%\n\t\t\\begin{tabular}{")
										f.write("c" * maxLength)
										f.write("}\n\t\t\t\\toprule\n\t\t\t\t")
										if isinstance(self.__columns, (tuple, list)) and self.__columns:
											f.write(" & ".join("\\textbf{{{0}}}".format(column) for column in self.__columns))
											if len(self.__columns) < maxLength:
												f.write(" & \\textbf{~}" * (maxLength - len(result)))
										else:
											f.write(" & ".join(("\\textbf{~}", ) * maxLength))
										f.write(" \\\\\n\t\t\t\\midrule\n")
										for result in results:
											if result:
												f.write("\t\t\t\t")
												f.write(" & ".join((																	\
													"${0}$" if isinstance(r, int) else "${{0:.{0}f}}$".format(self.__decimalPlace)	\
												).format(r) if isinstance(r, (float, int)) else str(r) for r in result))
												if len(result) < maxLength:
													f.write(" & ~" * (maxLength - len(result)))
												f.write(" \\\\\n")
										f.write("\t\t\t\\bottomrule\n\t\t\\end{tabular}\n\t}\n\t\\label{tab:comparison}\n\\end{sidewaystable}\n\n\\end{document}")
								elif "TSV" == self.__extensionName:
									if self.__Writer is None:
										self.__Writer = __import__("csv").writer
									with open(self.__outputFilePath, "w", newline = "", encoding = self.__encoding) as f:
										writer = self.__Writer(f, fieldnames = self.__columns, delimiter = '\t')
										writer.writeheader()
										writer.writerows(results)
								elif "XLS" == self.__extensionName:
									if self.__WorkbookXLS is None:
										self.__WorkbookXLS = __import__("xlwt").Workbook
									if self.__styleXLS is None:
										self.__styleXLS = __import__("xlwt").XFStyle()
										self.__styleXLS.font = __import__("xlwt").Font()
										self.__styleXLS.font.name = "Times New Roman"
										self.__styleXLS.font.height = 240 # 12 * 20
										self.__styleXLS.alignment = __import__("xlwt").Alignment()
										self.__styleXLS.alignment.horz = __import__("xlwt").Alignment.HORZ_CENTER
										self.__styleXLS.alignment.vert = __import__("xlwt").Alignment.VERT_CENTER
									workbook = self.__WorkbookXLS(encoding = self.__encoding)
									worksheet = workbook.add_sheet(Parser.getSchemeName())
									self.__styleXLS.font.bold = True
									for columnIndex, columnName in enumerate(self.__columns, start = 1):
										worksheet.write(0, columnIndex, columnName, self.__styleXLS)
									self.__styleXLS.font.bold = False
									for i, result in enumerate(results, start = 1):
										for j, r in enumerate(result):
											worksheet.write(i, j, "{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r, self.__styleXLS)
									workbook.save(self.__outputFilePath)
								elif "XLSX" == self.__extensionName:
									if self.__WorkbookXLSX is None:
										self.__WorkbookXLSX = __import__("openpyxl").Workbook
									if self.__alignmentXLSX is None:
										self.__alignmentXLSX = __import__("openpyxl").styles.Alignment(horizontal = "center", vertical = "center")
									if self.__fontXLSX is None:
										self.__fontXLSX = __import__("openpyxl").styles.Font(name = "Times New Roman", size = 12, bold = True)
									workbook = self.__WorkbookXLSX()
									worksheet = workbook.active
									for columnIndex, columnName in enumerate(self.__columns, start = 1):
										cell = worksheet.cell(row = 1, column = columnIndex, value = columnName)
										cell.alignment = self.__alignmentXLSX
										cell.font = self.__fontXLSX
									for i, result in enumerate(results, start = 2):
										for j, r in enumerate(result, start = 1):
											cell = worksheet.cell(row = i, column = j, value = "{{0:.{0}f}}".format(self.__decimalPlace).format(r) if isinstance(r, float) else r)
											cell.alignment = self.__alignmentXLSX
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
									with open(self.__outputFilePath, "w", encoding = self.__encoding) as f:
										self.__dumpYAML({"columns":self.__columns, "results":results}, f)
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
			print("Init: This scheme is only applicable to symmetric groups of prime orders. The curve type has been defaulted to \"SS512\". ")
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__n = 30
		self.__d = 10
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
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
	def Setup(self:object, n:int = 30, d:int = 10) -> tuple: # $\textbf{Setup}(n, d) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
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
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		self.__mpk = (g1, g2, g3, Y1, Y2, tVec, lVec, eta1, eta2, eta3, eta4, H1) # $ \textit{mpk} \gets (g_1, g_2, g_3, Y_1, Y_2, \vec{t}, \vec{l}, \eta_1, \eta_2, \eta_3, \eta_4, H_1)$
		self.__msk = (alpha, beta, theta1, theta2, theta3, theta4) # $\textit{msk} \gets (\alpha, \beta, \theta_1, \theta_2, \theta_3, \theta_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, SA:tuple) -> tuple: # $\textbf{EKGen}(S_A) \rightarrow \textit{ek}_{S_A}$
		# Check #
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
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		rVec = tuple(self.__group.random(ZR) for _ in S_A) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		EVec = tuple(g3 ** (q(S_A[i]) * theta1 * theta2) * H(S_A[i]) ** rVec[i] for i in range(len(S_A))) # $E_i \gets g_3^{q(a_i) \theta_1 \theta_2} H(a_i)^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		eVec = tuple(g ** rVec[i] for i in range(len(S_A))) # $e_i \gets g^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		ek_S_A = (EVec, eVec) # $\textit{ek}_{S_A} \gets \{E_i, e_i\}_{a_i \in S_A}$
		
		# Return #
		return ek_S_A # \textbf{return} $\textit{ek}_{S_A}$
	def DKGen(self:object, SB:tuple, PA:tuple) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
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
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \rightarrow g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta(i, N, x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
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
		dk_S_B_1 = tuple(																						\
			g2 ** (-f(S_B[i]) * theta2) * G_ID ** (-h(S_B[i]) * theta2) * T(S_B[i]) ** (-k1Vec[i] * theta2) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{1, i}}} \gets g_2^{-f(b_i) \theta_2} (G_{\textit{ID}})^{-h(b_i) \theta_2} [T(b_i)]^{-k_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_2 = tuple(																						\
			g2 ** (-f(S_B[i]) * theta1) * G_ID ** (-h(S_B[i]) * theta1) * T(S_B[i]) ** (-k1Vec[i] * theta1) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{2, i}}} \gets g_2^{-f(b_i) \theta_1} (G_{\textit{ID}})^{-h(b_i) \theta_1} [T(b_i)]^{-k_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_3 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{S_{B_{3, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_4 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{S_{B_{4, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B = (dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4) # $\textit{dk}_{S_B} \gets (\textit{dk}_{S_{B_0}}, \textit{dk}_{S_{B_1}}, \textit{dk}_{S_{B_2}}, \textit{dk}_{S_{B_3}}, \textit{dk}_{S_{B_4}})$
		dk_P_A_0 = tuple(g ** (rPrime1Vec[i] * theta1 * theta2 + rPrime2Vec[i] * theta3 * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{0, i}}} \gets g^{r'_{i, 1} \theta_1 \theta_2 + r'_{i, 2} \theta_3 \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_1 = tuple(																										\
			g2 ** (-2 * qPrime(P_A[i]) * theta2) * G_ID ** (h(P_A[i]) * theta2) * H(P_A[i]) ** (-rPrime1Vec[i] * theta2) for i in range(self.__n)		\
		) # $\textit{dk}_{P_{A_{1, i}}} \gets g_2^{-2q'(a_i) \theta_2} (G_{\textit{ID}})^{h(a_i \theta_2)} H(a_i)^{-r'_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_2 = tuple(																										\
			g2 ** (-2 * qPrime(P_A[i]) * theta1) * G_ID ** (h(P_A[i]) * theta1) * H(P_A[i]) ** (-rPrime1Vec[i] * theta1) for i in range(self.__n)		\
		) # $\textit{dk}_{P_{A_{2, i}}} \gets g_2^{-2q'(a_i) \theta_1} (G_{\textit{ID}})^{h(a_i \theta_1)} H(a_i)^{-r'_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_3 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_4 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A = (dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4) # $\textit{dk}_{P_A} \gets (\textit{dk}_{P_{A_0}}, \textit{dk}_{P_{A_1}}, \textit{dk}_{P_{A_2}}, \textit{dk}_{P_{A_3}}, \textit{dk}_{P_{A_4}})$
		dk_SBPA = (dk_S_B, dk_P_A) # $\textit{dk}_{S_B, P_A} \gets (\textit{dk}_{S_B}, \textit{dk}_{P_A})$
		
		# Return #
		return dk_SBPA # \textbf{return} $\textit{dk}_{S_B, P_A}$
	def Encryption(self:object, ekSA:tuple, SA:tuple, PB:tuple, message:Element) -> tuple: # $\textbf{Encryption}(\textit{ek}_{S_A}, S_A, P_B, M) \rightarrow \textit{CT}$
		# Check #
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
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \rightarrow g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta(i, N, x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
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
		C5Vec = tuple(EVec[i] ** s * g3 ** l(S_A[i]) * H(S_A[i]) ** (s * xiVec[i]) * H1(														\
			self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)		\
			+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
		) for i in range(self.__n)) # $C_{5, i} \gets E_i^s \cdot g_3^{l(a_i)} H(a_i)^{s \cdot \xi_i} \cdot H_1(C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i})^{\chi_i}$
		CT = (C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec) # $\textit{CT} \gets (C_0, C_1, C_2, C_3, C_4, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Decryption(self:object, dkSBPA:tuple, SA:tuple, PA:tuple, SB:tuple, PB:tuple, cipherText:tuple) -> Element|bool: # $\textbf{Decryption}(\textit{dk}_{S_B, P_A}, S_A, P_A, S_B, P_B, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Decryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Decryption`` subsequently. ")
			self.Setup()
		if (																																	\
			isinstance(SA, tuple) and isinstance(PA, tuple) and isinstance(SB, tuple) and isinstance(PB, tuple) and len(SA) == len(PA) == len(SA) == len(SB) == self.__n	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SA) and all(isinstance(ele, Element) and ele.type == ZR for ele in PA)						\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SB) and all(isinstance(ele, Element) and ele.type == ZR for ele in PB)						\
		): # hybrid check
			S_A, P_A, S_B, P_B = SA, PA, SB, PB
			if (																																		\
				isinstance(dkSBPA, tuple) and len(dkSBPA) == 2 and isinstance(dkSBPA[0], tuple) and isinstance(dkSBPA[1], tuple) and len(dkSBPA[0]) == len(dkSBPA[1]) == 5	\
				and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[0]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[1])				\
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
			Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # \quad$\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
			KsPrime = self.__product(tuple(( # \quad$K'_s \gets \prod\limits_{b_i \in W_B} (
				pair(C1Vec[i], dk_S_B_0[i]) * pair(C1, dk_S_B_1[i]) * pair(C2, dk_S_B_2[i]) # \hat{e}(C_{1, i}, \textit{dk}_{S_{B_{0, i}}}) \hat{e}(C_1, \textit{dk}_{S_{B_{1, i}}}) \hat{e}(C_2, \textit{dk}_{S_{B_{2, i}}})
				* pair(C3, dk_S_B_3[i]) * pair(C4, dk_S_B_4[i]) # \hat{e}(C_3, \textit{dk}_{S_{B_{3, i}}}) \hat{e}(C_4, \textit{dk}_{S_{B_{4, i}}})
			) ** Delta(S_B[i], WB, 0) for i in range(self.__n))) # )^{\Delta(b_i, W_B, 0)}$
			CTVec = tuple(																												\
				(																														\
					self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)		\
					+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
				) for i in range(self.__n)																										\
			) # \quad$\textit{CT}_i \gets C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i}, \forall i \in \{1, 2, \cdots, n\}$
			KlPrime = self.__product(tuple( # \quad$K'_l \gets \prod\limits_{a_i \in W_A} 
				( # \left(
					(pair(C1Vec[i], dk_P_A_0[i]) * pair(C1, dk_P_A_1[i]) * pair(C2, dk_P_A_2[i])) # \frac{\hat{e}(C_{1, i}, \textit{dk}_{P_{A_{0, i}}}) \hat{e}(C_1, \textit{dk}_{P_{A_{1, i}}}) \hat{e}(C_2, \textit{dk}_{P_{A_{i, 2}}})}
					/ (pair(H1(CTVec[i]), C4Vec[i]) # {\hat{e}(H_1(\textit{CT}_i), C_{4, i}) \cdot \hat{e}(C_{3, i}, C_{2, i})}
					* pair(C3Vec[i], C2Vec[i])) * pair(C3, dk_P_A_3[i]) * pair(C4, dk_P_A_4[i]) * pair(C5Vec[i], g) # \cdot \hat{e}(C_3, \textit{dk}_{P_{A_{i, 3}}}) \hat{e}(C_4, \textit{dk}_{P_{A_{i, 4}}}) \hat{e}(C_{5, i}, g)
				) ** Delta(S_A[i], WA, 0) for i in range(self.__n) # \right)^{\Delta(a_i, W_A, 0)}
			)) # $
			M = C0 * KsPrime * KlPrime # \quad$M \gets C_0 \cdot K'_s \cdot K'_l$
		else: # \textbf{else}
			M = False # \quad$M \gets \perp$
		# \textbf{end if}
		
		# Return #
		return M # \textbf{return} $M$
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


def conductScheme(curveType:tuple|list|str, n:int = 30, d:int = 10, run:int|None = None) -> list:
	# Begin #
	if isinstance(n, int) and isinstance(d, int) and n >= 1 and d >= 2: # no need to check the parameters for curve types here
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
			print("n =", n)
			print("d =", d)
			if isinstance(run, int) and run >= 1:
				print("run =", run)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																													\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])	\
				+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 2 + [-1] * 13																			\
			)
	else:
		print("Is the system valid? No. The parameter $n$ should be a positive integer, and the parameter $d$ should be a positive integer not smaller than $2$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 2 + [-1] * 13																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("n =", n)
	print("d =", d)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeFuzzyME = SchemeFuzzyME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeFuzzyME.Setup(n = n, d = d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	S_A = tuple(group.random(ZR) for _ in range(n))
	ek_S_A = schemeFuzzyME.EKGen(S_A)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
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
	timeRecords.append(endTime - startTime)
	
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
	timeRecords.append(endTime - startTime)
	
	# Decryption #
	startTime = perf_counter()
	M = schemeFuzzyME.Decryption(dk_SBPA, S_A, P_A, S_B, P_B, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(M, bool) and message == M]
	spaceRecords = [																														\
		schemeFuzzyME.getLengthOf(group.random(ZR)), schemeFuzzyME.getLengthOf(group.random(G1)), schemeFuzzyME.getLengthOf(group.random(GT)), 	\
		schemeFuzzyME.getLengthOf(mpk), schemeFuzzyME.getLengthOf(msk), schemeFuzzyME.getLengthOf(ek_S_A),  									\
		schemeFuzzyME.getLengthOf(dk_SBPA), schemeFuzzyME.getLengthOf(CT)																	\
	]
	del schemeFuzzyME
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, n, d, run if isinstance(run, int) and run >= 1 else None] + booleans + timeRecords + spaceRecords

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, decimalPlace, runCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "n", "d", "runCount")
		validators = ("isSystemValid", "isSchemeCorrect")
		metrics = (															\
			"Setup (s)", "EKGen (s)", "DKGen (s)", "Encryption (s)", "Decryption (s)", 	\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 			\
			"mpk (B)", "msk (B)", "ek_S_A (B)", "dk_SBPA (B)", "CT (B)"			\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns, decimalPlace = decimalPlace, encoding = encoding)
		try:
			for curveType in curveTypes:
				for n in range(10, 31, 5):
					for d in range(5, n, 5):
						averages = conductScheme(curveType, n = n, d = d, run = 1)
						for run in range(2, runCount + 1):
							result = conductScheme(curveType, n = n, d = d, run = run)
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