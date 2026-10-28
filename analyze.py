from os import chdir, linesep, makedirs, name, walk
from os.path import abspath, dirname, isdir, isfile, islink, join, split, splitdrive, splitext
from sys import argv, exit
from ast import literal_eval
from codecs import lookup
from getpass import getpass
from importlib import import_module
try:
	from inflection import pluralize as pluralizeWord, singularize as singularizeWord
except Exception:
	def pluralizeWord(word:str) -> str:
		return word + "es" if word.lower().endswith(("s", "x", "z", "ch", "sh")) else word + "s"
	def singularizeWord(word:str) -> str:
		return word[:-1] if len(word) >= 2 and word.endswith(("S", "s")) else word
from io import BytesIO
from math import isclose, log as ln
from time import sleep
from zipfile import ZipFile
try:
	chdir(abspath(dirname(__file__)))
except Exception:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Parser:
	__OptionDelimiter = ("//", "--")
	__OptionEncoding = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
	__DefaultEncoding = "utf-8"
	__OptionHelp = ("h", "/h", "-h", "help", "/help", "--help")
	__OptionOutput = ("o", "/o", "-o", "output", "/output", "--output")
	__DefaultOutput = "%p/%n"
	__OptionPlace = ("p", "/p", "-p", "place", "/place", "--place")
	__DefaultPlace = 3
	__PlaceTranslations = {"s":0, "second":0, "ms":3, "millisecond":3, "microsecond":6, "ns":9, "nanosecond":9, "ps":12, "picosecond":12, "fs":15, "femtosecond":15}
	__OptionTime = ("t", "/t", "-t", "time", "/time", "--time")
	__OptionUnit = ("u", "/u", "-u", "unit", "/unit", "--unit")
	__DefaultTime = float("inf")
	__tcgetattr = None
	__OriginalConsoleAttributes = None
	__ECHOLESSNESS = None
	__EcholessConsoleAttributes = None
	__tcsetattr = None
	@staticmethod
	def __formatOption(option:tuple|list, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, (tuple, list)) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	@staticmethod
	def __printHelp() -> None:
		print("This is the official cryptographic scheme performance analyzer. ")
		print()
		print("Options (case-insensitive): ")
		print("\t{0}\t\tIndicate that all the following arguments are independent input paths. ".format(Parser.__formatOption(Parser.__OptionDelimiter)))
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for input files. The default value is {1}. ".format(
			Parser.__formatOption(Parser.__OptionEncoding), Parser.__DefaultEncoding
		))
		print("\t{0}\t\tPrint this help document. ".format(Parser.__formatOption(Parser.__OptionHelp)))
		print((
			"\t{0} <output>\t\tSpecify the output file path without an extension, which can be a format string, "
			+ "where %%, %d, %n, %p, %x stand for the %, Drive letter (if applicable), main file Name, directory Path, and eXtension, respectively. The default value is {1}. "
		).format(Parser.__formatOption(Parser.__OptionOutput), repr(Parser.__DefaultOutput)))
		print("\t{0} [s|ms|microsecond|ns|ps|0|3|6|9|12|...]\t\tSpecify the decimal place, which should be a non-negative integer. The default value is {1}. ".format(
			Parser.__formatOption(Parser.__OptionPlace), Parser.__DefaultPlace
		))
		print(
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(Parser.__formatOption(Parser.__OptionTime))
			+ "Passing inf requires users to manually press the Enter key before exiting. The default value is {0}. ".format(Parser.__DefaultTime)
		)
		print((
			"\t{0}\t\tSpecify a processing unit using a Python dictionary containing the keys \"i\" and \"o\", "
			+ "in which the value for \"i\" can be a string, a tuple, or a list, and the value for \"o\" should be a string. "
		).format(Parser.__formatOption(Parser.__OptionUnit)))
		print()
	@staticmethod
	def __parseRealNumber(string:str) -> int|float|None:
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
					if isinstance(realNumber, float) and realNumber.is_integer():
						realNumber = int(realNumber)
				if minusSign:
					realNumber = -realNumber
				return realNumber
		except Exception:
			return None
	@staticmethod
	def parse(args:tuple|list) -> tuple:
		arguments = tuple(argument for argument in args if isinstance(argument, str)) if isinstance(args, (tuple, list)) else ()
		flag, encoding, outputPathWithoutAnExtension, decimalPlace, waitingTime, units = (
			max(EXIT_SUCCESS, EOF) + 1, Parser.__DefaultEncoding, Parser.__DefaultOutput, Parser.__DefaultPlace, Parser.__DefaultTime, []
		)
		index, argumentCount, nonOptionMode, buffers = 1, len(arguments), False, []
		while index < argumentCount:
			argument = arguments[index].lower()
			if nonOptionMode:
				units.append(arguments[index])
			elif argument in Parser.__OptionDelimiter:
				nonOptionMode = True
			elif argument in Parser.__OptionEncoding:
				index += 1
				if index < argumentCount:
					try:
						lookup(arguments[index])
						encoding = arguments[index]
					except Exception:
						flag = EOF
						buffers.append("Parser: The value [{0}] = {1} for the encoding option is invalid. ".format(index, repr(arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the encoding option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionHelp:
				Parser.__printHelp()
				flag = EXIT_SUCCESS
				break
			elif argument in Parser.__OptionOutput:
				index += 1
				if index < argumentCount:
					outputPathWithoutAnExtension = arguments[index]
				else:
					flag = EOF
					buffers.append("Parser: The value for the output path without an extension option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionPlace:
				index += 1
				if index < argumentCount:
					decimalPlaceLower = arguments[index].lower()
					if decimalPlaceLower in Parser.__PlaceTranslations:
						decimalPlace = Parser.__PlaceTranslations[decimalPlaceLower]
					else:
						p = Parser.__parseRealNumber(arguments[index])
						if p is None:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option cannot be recognized. ".format(index, repr(arguments[index])))
						elif isinstance(p, int) and p >= 0:
							decimalPlace = p
						else:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the decimal place option should be a non-negative integer. ".format(index, p))
						del p
				else:
					flag = EOF
					buffers.append("Parser: The value for the decimal place option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionTime:
				index += 1
				if index < argumentCount:
					t = Parser.__parseRealNumber(arguments[index])
					if t is None:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = {1} for the waiting time option is invalid. ".format(index, repr(arguments[index])))
					elif t >= 0:
						waitingTime = t
					else:
						flag = EOF
						buffers.append("Parser: The value [{0}] = {1} for the waiting time option should be a non-negative value. ".format(index, t))
					del t
				else:
					flag = EOF
					buffers.append("Parser: The value for the waiting time option is missing at [{0}]. ".format(index))
			elif argument in Parser.__OptionUnit:
				index += 1
				if index < argumentCount:
					try:
						unit = literal_eval(arguments[index])
						if isinstance(unit, dict) and "i" in unit and "o" in unit:
							units.append(unit)
						else:
							buffers.append("Parser: The value [{0}] = {1} for the unit option should be a Python dictionary containing the keys \"i\" and \"o\". ".format(
								index, repr(arguments[index])
							))
					except Exception as e:
						buffers.append("Parser: The value [{0}] = {1} for the unit option cannot be literally evaluated due to {2}. ".format(index, repr(arguments[index]), repr(e)))
				else:
					flag = EOF
					buffers.append("Parser: The value for the unit option is missing at [{0}]. ".format(index))
			else:
				units.append(arguments[index])
			index += 1
		if EOF == flag:
			for buffer in buffers:
				print(buffer)
		return (flag, encoding, outputPathWithoutAnExtension, decimalPlace, waitingTime, units)
	@staticmethod
	def disableConsoleEchoes() -> bool:
		if "posix" == name:
			try:
				if Parser.__tcgetattr is None:
					Parser.__tcgetattr = __import__("termios").tcgetattr
				if Parser.__OriginalConsoleAttributes is None:
					Parser.__OriginalConsoleAttributes = Parser.__tcgetattr(0)
				if Parser.__ECHOLESSNESS is None:
					Parser.__ECHOLESSNESS = ~__import__("termios").ECHO
				if Parser.__EcholessConsoleAttributes is None:
					Parser.__EcholessConsoleAttributes = Parser.__tcgetattr(0)
					Parser.__EcholessConsoleAttributes[3] &= Parser.__ECHOLESSNESS
				if Parser.__tcsetattr is None:
					Parser.__tcsetattr = __import__("termios").tcsetattr
				Parser.__tcsetattr(0, 0, Parser.__EcholessConsoleAttributes)
			except Exception:
				return False
		return True
	@staticmethod
	def getDefaultOutput() -> str:
		return Parser.__DefaultOutput
	@staticmethod
	def getDefaultEncoding() -> str:
		return Parser.__DefaultEncoding
	@staticmethod
	def getDefaultPlace() -> str:
		return Parser.__DefaultPlace
	@staticmethod
	def restoreConsoleEchoes() -> bool:
		if "posix" == name:
			try:
				Parser.__tcsetattr(0, 0, Parser.__OriginalConsoleAttributes)
				Parser.__OriginalConsoleAttributes = None
			except Exception:
				return False
		return True

class Loader:
	__reader = None # CSV/TSV
	__loadJSON = None # JSON
	__TableParser = None # HTM/HTML
	__open_workbook = None # XLS
	__load_workbook = None # XLSX
	__ElementTree = None # XML
	@staticmethod
	def __coerceValue(value:object) -> object:
		try:
			if isinstance(value, str):
				strippedValue = value.strip().lower()
				if "true" == strippedValue:
					return True
				elif "false" == strippedValue:
					return False
				else:
					try:
						return int(strippedValue)
					except ValueError:
						try:
							return float(strippedValue)
						except ValueError:
							return value
			elif isinstance(value, (int, float)):
				return value
		except Exception:
			return ""
	@staticmethod
	def __rowsToMappings(rows:tuple|list) -> dict|Exception: # [["x", "y"], [1, 1], [2, 4], [3.0, 9.0], [4]] -> {"x": [1, 2, 3.0, 4], "y": [1, 4, 9.0, ""]}
		if isinstance(rows, (tuple, list)) and rows and isinstance(rows[0], (tuple, list)):
			columns = tuple("" if cell is None else str(cell) for cell in rows[0])
			mappings = {column:[] for column in columns}
			columnLength = len(columns)
			if len(mappings) == columnLength:
				for row in rows[1:]:
					if isinstance(row, (tuple, list)):
						index, rowLength = 0, min(len(row), columnLength)
						while index < rowLength:
							mappings[columns[index]].append(Loader.__coerceValue(row[index]))
							index += 1
						while index < columnLength:
							mappings[columns[index]].append("")
							index += 1
				return mappings
			else:
				return KeyError("Repeated column names were found in the input file. ")
		else:
			return TypeError("The rows loaded should be a tuple or a list containing one or more tuples or lists. ")
	@staticmethod
	def __loadDelimited(inputFilePath:str, delimiter:str = ',', encoding:str = "utf-8") -> dict|Exception: # CSV/TSV
		try:
			if Loader.__reader is None:
				Loader.__reader = __import__("csv").reader
			with open(inputFilePath, "r", newline = "", encoding = encoding) as f:
				return Loader.__rowsToMappings(list(Loader.__reader(f, delimiter = delimiter)))
		except Exception as e:
			return e
	@staticmethod
	def __loadHTML(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # HTM/HTML
		try:
			if Loader.__TableParser is None:
				class TableParser(__import__("html.parser", fromlist = ["HTMLParser"]).HTMLParser):
					def __init__(self:object) -> object:
						super().__init__(convert_charrefs = True)
						self.rows, self.__row, self.__cell = [], None, None
					def handle_starttag(self:object, tag:str, attrs:list) -> None:
						if "tr" == tag:
							self.__row = []
						elif tag in ("th", "td") and self.__row is not None:
							self.__cell = []
					def handle_data(self:object, data:str) -> None:
						if self.__cell is not None:
							self.__cell.append(data)
					def handle_endtag(self:object, tag:str) -> None:
						if tag in ("th", "td") and self.__cell is not None and self.__row is not None:
							self.__row.append("".join(self.__cell))
							self.__cell = None
						elif "tr" == tag and self.__row is not None:
							self.rows.append(self.__row)
							self.__row = None
				Loader.__TableParser = TableParser
			tableParser = Loader.__TableParser()
			with open(inputFilePath, "r", encoding = encoding) as f:
				tableParser.feed(f.read())
			tableParser.close() # different from ``with TableParser(...) as ...``
			return Loader.__rowsToMappings(tableParser.rows)
		except Exception as e:
			return e
	@staticmethod
	def __structuredDataToMappings(data:object) -> dict|Exception: # {"columns":["x", "y"], "results":[[1, 1], [2, 4], [3, 9]]} -> {"x":[1, 2, 3], "y":[1, 4, 9]}
		if isinstance(data, dict) and "columns" in data and "results" in data and isinstance(data["columns"], (tuple, list)) and isinstance(data["results"], (tuple, list)):
			return Loader.__rowsToMappings([list(data["columns"])] + [list(result) for result in data["results"] if isinstance(result, (tuple, list))])
		else:
			return ValueError("The structured data should be a dictionary containing the keys \"columns\" and \"results\". ")
	@staticmethod
	def __loadJSON(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # JSON
		try:
			if Loader.__loadJSON is None:
				Loader.__loadJSON = __import__("json").load
			with open(inputFilePath, "r", encoding = encoding) as f:
				return Loader.__structuredDataToMappings(Loader.__loadJSON(f))
		except Exception as e:
			return e
	@staticmethod
	def __loadTXT(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # TXT
		try:
			with open(inputFilePath, "r", encoding = encoding) as f:
				return Loader.__structuredDataToMappings(literal_eval(f.read()))
		except Exception as e:
			return e
	@staticmethod
	def __unescapeTEX(text:object) -> str: # the inverse of the ``escapeTEX`` used by the savers
		if isinstance(text, str):
			text = text.strip()
			if text.startswith("\\textbf{") and text.endswith("}"): # column header or padded header cell
				text = text[len("\\textbf{"):-1]
			if len(text) >= 2 and text.startswith("$") and text.endswith("$"): # numeric cell
				text = text[1:-1]
			if "~" == text: # padded cell
				return ""
			text = text.replace("\\textbackslash{}", "\0")
			for escaped, original in (
				("\\#", "#"), ("\\$", "$"), ("\\%", "%"), ("\\&", "&"), ("\\_", "_"), ("\\{", "{"), ("\\}", "}"),
				("\\textless{}", "<"), ("\\textgreater{}", ">"), ("\\textasciicircum{}", "^"), ("\\textasciitilde{}", "~")
			):
				text = text.replace(escaped, original)
			return text.replace("\0", "\\")
		else:
			return ""
	@staticmethod
	def __loadTEX(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # TEX
		try:
			rows, inTable = [], False
			with open(inputFilePath, "r", encoding = encoding) as f:
				for line in f:
					strippedLine = line.strip()
					if "\\toprule" in strippedLine:
						inTable = True
					elif "\\bottomrule" in strippedLine:
						break
					elif inTable and " & " in strippedLine:
						if strippedLine.endswith("\\\\"):
							strippedLine = strippedLine[:-2].rstrip()
						rows.append([Loader.__unescapeTEX(cell) for cell in strippedLine.split(" & ")])
			return Loader.__rowsToMappings(rows)
		except Exception as e:
			return e
	@staticmethod
	def __loadXLS(inputFilePath:str) -> dict|Exception: # XLS
		try:
			if Loader.__open_workbook is None:
				Loader.__open_workbook = __import__("xlrd").open_workbook
			workbook = Loader.__open_workbook(inputFilePath)
			worksheet = workbook.sheet_by_index(0)
			return Loader.__rowsToMappings([worksheet.row_values(rowIndex) for rowIndex in range(worksheet.nrows)])
		except Exception as e:
			return e
	@staticmethod
	def __loadXLSX(inputFilePath:str) -> dict|Exception: # XLSX
		try:
			if Loader.__load_workbook is None:
				Loader.__load_workbook = __import__("openpyxl").load_workbook
			workbook = Loader.__load_workbook(inputFilePath, read_only = True, data_only = True)
			try:
				return Loader.__rowsToMappings([tuple(row) for row in workbook.active.iter_rows(values_only = True)])
			finally:
				workbook.close()
		except Exception as e:
			return e
	@staticmethod
	def __loadXML(inputFilePath:str) -> dict|Exception: # XML
		try:
			if Loader.__ElementTree is None:
				Loader.__ElementTree = __import__("xml.etree.ElementTree", fromlist = ["ElementTree"])
			root = Loader.__ElementTree.parse(inputFilePath).getroot()
			rows = [[element.text or "" for element in root.iter("column")]]
			for result in root.iter("result"):
				rows.append([element.text or "" for element in result.iter("r")])
			return Loader.__rowsToMappings(rows)
		except Exception as e:
			return e
	@staticmethod
	def __loadYAML(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # YAML/YML
		try:
			if Loader.__loadJSON is None:
				Loader.__loadJSON = __import__("json").load
			rows, section = [], None
			with open(inputFilePath, "r", encoding = encoding) as f:
				for line in f:
					line = line.rstrip("\r\n")
					if line.startswith("columns:"):
						section = None if line.rstrip().endswith("[]") else "columns"
					elif line.startswith("results:"):
						section = None if line.rstrip().endswith("[]") else "results"
					elif "columns" == section and line.startswith("  - "):
						if rows:
							rows[0].append(Loader.__loadJSON(line[4:]))
						else:
							rows.append([Loader.__loadJSON(line[4:])])
					elif "results" == section:
						if line.startswith("  - - "):
							rows.append([Loader.__loadJSON(line[6:])])
						elif line.startswith("    - ") and rows:
							rows[-1].append(Loader.__loadJSON(line[6:]))
						elif line.startswith("  - []"):
							rows.append([])
			return Loader.__rowsToMappings(rows)
		except Exception as e:
			return e
	@staticmethod
	def load(inputFilePath:str, encoding:str = "utf-8") -> dict|Exception: # {"x":[1, 2, 3], "y":[1, 4, 9]}
		try:
			lowercaseExtension = splitext(inputFilePath)[1].lower()
			if ".csv" == lowercaseExtension:
				mappings = Loader.__loadDelimited(inputFilePath, delimiter = ",", encoding = encoding)
			elif lowercaseExtension in (".htm", ".html"):
				mappings = Loader.__loadHTML(inputFilePath, encoding = encoding)
			elif ".json" == lowercaseExtension:
				mappings = Loader.__loadJSON(inputFilePath, encoding = encoding)
			elif ".tex" == lowercaseExtension:
				mappings = Loader.__loadTEX(inputFilePath, encoding = encoding)
			elif ".tsv" == lowercaseExtension:
				mappings = Loader.__loadDelimited(inputFilePath, delimiter = '\t', encoding = encoding)
			elif ".xls" == lowercaseExtension:
				mappings = Loader.__loadXLS(inputFilePath)
			elif ".xlsx" == lowercaseExtension:
				mappings = Loader.__loadXLSX(inputFilePath)
			elif ".xml" == lowercaseExtension:
				mappings = Loader.__loadXML(inputFilePath)
			elif lowercaseExtension in (".yaml", ".yml"):
				mappings = Loader.__loadYAML(inputFilePath, encoding = encoding)
			else:
				return Loader.__loadTXT(inputFilePath, encoding = encoding)
			if isinstance(mappings, dict):
				return mappings
			else:
				currentMappings = Loader.__loadTXT(inputFilePath, encoding = encoding)
				if isinstance(currentMappings, dict):
					return currentMappings
				else:
					return mappings
		except Exception as e:
			return e

class TEX:
	@staticmethod
	def __splitUnit(string:str) -> tuple:
		if isinstance(string, str):
			strippedString = " ".join(string.split())
			lowercaseStrippedString = strippedString.lower()
			if lowercaseStrippedString.endswith("(ns)"):
				return (strippedString[:-4].rstrip(), "(ns)")
			elif lowercaseStrippedString.endswith("(\\textmu s)"):
				return (strippedString[:-11].rstrip(), "(\\textmu{}s)")
			elif lowercaseStrippedString.endswith("(\\textmu{}s)"):
				return (strippedString[:-12].rstrip(), "(\\textmu{}s)")
			elif lowercaseStrippedString.endswith("(ms)"):
				return (strippedString[:-4].rstrip(), "(ms)")
			elif lowercaseStrippedString.endswith("(s)"):
				return (strippedString[:-3].rstrip(), "(s)")
			elif lowercaseStrippedString.endswith("(min)"):
				return (strippedString[:-5].rstrip(), "(min)")
			elif lowercaseStrippedString.endswith("(h)"):
				return (strippedString[:-3].rstrip(), "(h)")
			elif lowercaseStrippedString.endswith("(bit)"):
				return (strippedString[:-5].rstrip(), "(bit)")
			elif lowercaseStrippedString.endswith("(b)"):
				return (strippedString[:-3].rstrip(), "(B)")
			elif lowercaseStrippedString.endswith("(byte)"):
				return (strippedString[:-6].rstrip(), "(Byte)")
			elif lowercaseStrippedString.endswith("(kb)"):
				return (strippedString[:-4].rstrip(), "(kB)")
			elif lowercaseStrippedString.endswith("(mb)"):
				return (strippedString[:-4].rstrip(), "(MB)")
			elif lowercaseStrippedString.endswith("(gb)"):
				return (strippedString[:-4].rstrip(), "(GB)")
			elif lowercaseStrippedString.endswith("(tb)"):
				return (strippedString[:-4].rstrip(), "(TB)")
			elif lowercaseStrippedString.endswith("(pb)"):
				return (strippedString[:-4].rstrip(), "(PB)")
			elif lowercaseStrippedString.endswith("(kib)"):
				return (strippedString[:-5].rstrip(), "(KiB)")
			elif lowercaseStrippedString.endswith("(mib)"):
				return (strippedString[:-5].rstrip(), "(MiB)")
			elif lowercaseStrippedString.endswith("(gib)"):
				return (strippedString[:-5].rstrip(), "(GiB)")
			elif lowercaseStrippedString.endswith("(tib)"):
				return (strippedString[:-5].rstrip(), "(TiB)")
			elif lowercaseStrippedString.endswith("(pib)"):
				return (strippedString[:-5].rstrip(), "(PiB)")
			else:
				return (strippedString, "")
		else:
			return (None, None)
	@staticmethod
	def __splitInlineMathematicalMode(variableName:str) -> list|None:
		if isinstance(variableName, str):
			index, length, delimiter, buffers, startingIndex = 0, len(variableName), None, [], 0
			while index < length:
				if '\\' == variableName[index]:
					index += 1
					if index >= length:
						break
					elif '(' == variableName[index]:
						if delimiter:
							break # treat the all remaining characters as plain text due to the illegal syntax
						else:
							if startingIndex < index - 1:
								buffers.append((variableName[startingIndex:index - 1], False))
							delimiter = '('
							startingIndex = index - 1
					elif ')' == variableName[index]:
						if '(' == delimiter:
							if startingIndex < index + 1:
								buffers.append((variableName[startingIndex:index + 1], True))
							delimiter = None
							startingIndex = index + 1
						else:
							break # treat the all remaining characters as plain text due to the illegal syntax
				elif '$' == variableName[index]:
					if delimiter is None:
						if startingIndex < index:
							buffers.append((variableName[startingIndex:index], False))
						delimiter = '$'
						startingIndex = index
					elif '$' == delimiter:
						if startingIndex < index:
							buffers.append((variableName[startingIndex:index + 1], True))
						delimiter = None
						startingIndex = index + 1
					else:
						break # treat the all remaining characters as plain text due to the illegal syntax
				index += 1
			if startingIndex < length:
				buffers.append((variableName[startingIndex:], False))
			return buffers
		else:
			return None
	@staticmethod
	def __sanitize(string:str) -> tuple:
		variableName, variableUnit = TEX.__splitUnit(string)
		if isinstance(variableName, str) and variableName and isinstance(variableUnit, str):
			variableNameSegments = TEX.__splitInlineMathematicalMode(variableName)
			if isinstance(variableNameSegments, list):
				return (tuple((" ".join("".join(character for character in variableNameSegment[0] if ' ' <= character <= '~').split()) if variableNameSegment[1] else " ".join("".join(
					character for character in variableNameSegment[0] if character in (' ', '(', ')', '-') or '0' <= character <= '9' or 'A' <= character <= 'Z' or 'a' <= character <= 'z'
				).split()).lstrip(" )-0123456789").rstrip(" (-"), variableNameSegment[1]) for variableNameSegment in variableNameSegments), variableUnit)
			else:
				return (None, None)
		else:
			return (None, None)
	@staticmethod
	def sanitize(string:str) -> str|None:
		sanitizedVariableNameSegments, variableUnit = TEX.__sanitize(string)
		if isinstance(sanitizedVariableNameSegments, tuple) and sanitizedVariableNameSegments and isinstance(variableUnit, str):
			sanitizedVariableName = " ".join(sanitizedVariableNameSegment[0] for sanitizedVariableNameSegment in sanitizedVariableNameSegments)
			return "{0} {1}".format(sanitizedVariableName, variableUnit) if variableUnit else sanitizedVariableName
		else:
			return None
	@staticmethod
	def __lowercase(string:str) -> tuple:
		sanitizedVariableNameSegments, variableUnit = TEX.__sanitize(string)
		if isinstance(sanitizedVariableNameSegments, tuple) and sanitizedVariableNameSegments and isinstance(variableUnit, str):
			lowercaseSanitizedVariableNameSegments = []
			for sanitizedVariableNameSegment in sanitizedVariableNameSegments:
				if sanitizedVariableNameSegment[1]:
					lowercaseSanitizedVariableNameSegments.append(sanitizedVariableNameSegment)
				else:
					currentWord = []
					buffer = []
					for character in sanitizedVariableNameSegment[0]:
						if '0' <= character <= '9' or 'A' <= character <= 'Z' or 'a' <= character <= 'z':
							currentWord.append(character)
						else:
							if currentWord:
								if (
									len(currentWord) >= 2 and ('0' <= currentWord[0] <= '9' or 'A' <= currentWord[0] <= 'Z')
									and ('0' <= currentWord[1] <= '9' or 'A' <= currentWord[1] <= 'Z')
								):
									buffer.extend(currentWord)
									currentWord.clear()
								else:
									buffer.extend(currentCharacter.lower() for currentCharacter in currentWord)
									currentWord.clear()
							buffer.append(character)
					if currentWord:
						if len(currentWord) >= 2 and ('0' <= currentWord[0] <= '9' or 'A' <= currentWord[0] <= 'Z') and ('0' <= currentWord[1] <= '9' or 'A' <= currentWord[1] <= 'Z'):
							buffer.extend(currentWord)
						else:
							buffer.extend(currentCharacter.lower() for currentCharacter in currentWord)
					lowercaseSanitizedVariableNameSegments.append(("".join(buffer), sanitizedVariableNameSegment[1]))
			return (tuple(lowercaseSanitizedVariableNameSegments), variableUnit)
		else:
			return (None, None)
	@staticmethod
	def lowercase(string:str) -> str|None:
		lowercaseSanitizedVariableNameSegments, variableUnit = TEX.__lowercase(string)
		if isinstance(lowercaseSanitizedVariableNameSegments, tuple) and lowercaseSanitizedVariableNameSegments and isinstance(variableUnit, str):
			lowercaseSanitizedVariableName = " ".join(lowercaseSanitizedVariableNameSegment[0] for lowercaseSanitizedVariableNameSegment in lowercaseSanitizedVariableNameSegments)
			return "{0} {1}".format(lowercaseSanitizedVariableName, variableUnit) if variableUnit else lowercaseSanitizedVariableName
		else:
			return None
	@staticmethod
	def checkMathematicalLikeString(string:str) -> bool|None:
		sanitizedVariableNameSegments, variableUnit = TEX.__sanitize(string)
		if isinstance(sanitizedVariableNameSegments, tuple) and sanitizedVariableNameSegments and isinstance(variableUnit, str):
			return len(sanitizedVariableNameSegments) == 1 and sanitizedVariableNameSegments[0][1]
		else:
			return None
	@staticmethod
	def checkConsumptionLikeString(string:str) -> bool|None:
		lowercaseSanitizedVariableNameSegments, variableUnit = TEX.__lowercase(string)
		if isinstance(lowercaseSanitizedVariableNameSegments, tuple) and lowercaseSanitizedVariableNameSegments and isinstance(variableUnit, str):
			return any("consumption" in lowercaseSanitizedVariableNameSegment[0] for lowercaseSanitizedVariableNameSegment in lowercaseSanitizedVariableNameSegments) or variableUnit in (
				"(ns)", "(\\textmu{}s)", "(ms)", "(s)", "(min)", "(h)", "(bit)", "(B)", "(Byte)", "(kB)", "(MB)", "(GB)", "(TB)", "(PB)", "(KiB)", "(MiB)", "(GiB)", "(TiB)", "(PiB)"
			)
		else:
			return None
	@staticmethod
	def pluralize(string:str) -> str|None:
		sanitizedVariableNameSegments, variableUnit = TEX.__sanitize(string)
		if isinstance(sanitizedVariableNameSegments, tuple) and sanitizedVariableNameSegments and isinstance(variableUnit, str):
			if sanitizedVariableNameSegments[-1][1]:
				sanitizedVariableName = " ".join(sanitizedVariableNameSegment[0] for sanitizedVariableNameSegment in sanitizedVariableNameSegments)
				return "{0} values {1}".format(sanitizedVariableName, variableUnit) if variableUnit else "{0} values".format(sanitizedVariableName)
			else:
				pluralizedSanitizedVariableName = " ".join(
					sanitizedVariableNameSegment[0] for sanitizedVariableNameSegment in sanitizedVariableNameSegments[:-1]
				) + pluralizeWord(sanitizedVariableNameSegments[-1][0])
				return "{0} {1}".format(pluralizedSanitizedVariableName, variableUnit) if variableUnit else pluralizedSanitizedVariableName
		else:
			return None
	@staticmethod
	def singularize(string:str) -> str|None:
		sanitizedVariableNameSegments, variableUnit = TEX.__sanitize(string)
		if isinstance(sanitizedVariableNameSegments, tuple) and sanitizedVariableNameSegments and isinstance(variableUnit, str):
			if sanitizedVariableNameSegments[-1][1]:
				sanitizedVariableName = " ".join(sanitizedVariableNameSegment[0] for sanitizedVariableNameSegment in sanitizedVariableNameSegments)
				return "{0} value {1}".format(sanitizedVariableName, variableUnit) if variableUnit else "{0} value".format(sanitizedVariableName)
			else:
				singularizedSanitizedVariableName = " ".join(
					sanitizedVariableNameSegment[0] for sanitizedVariableNameSegment in sanitizedVariableNameSegments[:-1]
				) + singularizeWord(sanitizedVariableNameSegments[-1][0])
				return "{0} {1}".format(singularizedSanitizedVariableName, variableUnit) if variableUnit else singularizedSanitizedVariableName
		else:
			return None
	@staticmethod
	def addArticle(string:str, capitalized:bool = False) -> str|None:
		lowercaseSanitizedString = TEX.lowercase(string)
		if isinstance(lowercaseSanitizedString, str) and lowercaseSanitizedString:
			return ("The " if capitalized is True else "the ") + lowercaseSanitizedString
		else:
			return None
	@staticmethod
	def capitalize(string:str) -> str|None:
		sanitizedString = TEX.sanitize(string)
		if isinstance(sanitizedString, str) and sanitizedString:
			return sanitizedString[0].upper() + sanitizedString[1:] if 'a' <= sanitizedString[0] <= 'z' else sanitizedString
		else:
			return None

class Drawer:
	__Colors = ("red", "orange", "purple", "blue", "cyan", "green", "brown", "gray", "black", "magenta", "pink", "lime", "navy", "teal", "aqua", "maroon", "olive", "gold", "silver")
	__ColorLength = len(__Colors)
	__Markers = ("x", "o", "s", "^", "D", "+", ".", "p", "v", "d", "*", "|", "h", "<", "_", ">", "1", "2", "3", "4")
	__MarkerLength = len(__Markers) # try to make ``gcd(__ColorLength, __MarkerLength)`` equal to 1, or as small a positive integer as possible
	__plt = None
	__LabelFontSize = 14
	__LegendFontSize = 12
	__escapeTEX = lambda x:"\\textbackslash{}".join(
		string.replace("#", "\\#").replace("$", "\\$").replace("%", "\\%").replace("&", "\\&").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}")
		.replace("<", "\\textless{}").replace(">", "\\textgreater{}").replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")
		for string in "".join(character for character in str(x) if ' ' <= character <= '~').split("\\")
	)
	@staticmethod
	def checkValues(values:tuple|list) -> bool:
		return isinstance(values, (tuple, list)) and values and all(isinstance(value, (int, float, str)) for value in values)
	@staticmethod
	def __getVariableString(variable:str|int, variables:tuple|list) -> str|None:
		if isinstance(variables, (tuple, list)):
			variableLength = len(variables)
			if isinstance(variable, str):
				if variable in variables:
					return variable
			elif isinstance(variable, int):
				if -variableLength <= variable and variable < variableLength:
					return variables[variable]
		return None
	@staticmethod
	def configure() -> bool|Exception:
		try:
			if Drawer.__plt is None:
				Drawer.__plt = import_module("matplotlib.pyplot")
				Drawer.__plt.rcParams["font.family"] = "Times New Roman"
				Drawer.__plt.rcParams["font.size"] = 12
				Drawer.__plt.rcParams["mathtext.fontset"] = "custom"
				Drawer.__plt.rcParams["mathtext.rm"] = "Times New Roman"
				Drawer.__plt.rcParams["mathtext.bf"] = "Times New Roman:bold"
				Drawer.__plt.rcParams["mathtext.it"] = "Times New Roman:italic"
				Drawer.__plt.rcParams["mathtext.bfit"] = "Times New Roman:bold:italic"
			return True
		except Exception as e:
			return e
	@staticmethod
	def __checkNumbers(numbers:tuple|list) -> bool:
		return isinstance(numbers, (tuple, list)) and numbers and all(isinstance(number, (int, float)) for number in numbers)
	@staticmethod
	def __checkLogarithmicSpacing(xValues:tuple|list|set) -> bool:
		if isinstance(xValues, (tuple, list, set)) and xValues and all(isinstance(xValue, (int, float)) for xValue in xValues):
			uniqueValues = sorted(set(xValues))
			if len(uniqueValues) >= 3 and uniqueValues[0] > 0:
				differences = tuple(b - a for a, b in zip(uniqueValues, uniqueValues[1:]))
				if min(differences) > 0:
					linearSpread = max(differences) / min(differences)
					if linearSpread >= 10: # clearly non-uniform in the linear domain
						logarithms = tuple(ln(uniqueValue) for uniqueValue in uniqueValues)
						logarithmicDifferences = tuple(b - a for a, b in zip(logarithms, logarithms[1:]))
						return min(logarithmicDifferences) > 0 and max(logarithmicDifferences) / min(logarithmicDifferences) < linearSpread
		return False
	@staticmethod
	def draw(curves:tuple|list, xLabel:str|None = None, yLabel:str|None = None) -> bytes|Exception:
		if Drawer.__plt is None:
			configurationStatus = Drawer.configure()
			if configurationStatus is not True:
				return configurationStatus
		if isinstance(curves, (tuple, list)) and curves: # curves = ({"x":(1, 2, 3), "y":(1, 4, 9), "label":"$y = x^2$"}, {"x":(1, 2, 3), "y":(1, 8, 27), "label":"$y = x^3$"})
			try:
				xValues = set()
				for curve in curves:
					if (
						isinstance(curve, dict) and "x" in curve and Drawer.__checkNumbers(curve["x"]) and len(set(curve["x"])) == len(curve["x"])
						and "y" in curve and Drawer.__checkNumbers(curve["y"]) and len(curve["x"]) == len(curve["y"])
					):
						xValues.update(curve["x"])
						x, y = zip(*sorted(zip(curve["x"], curve["y"]))) # sort $x$ and $y$ by ascending $x$ values
						keywordArguments = {key:value for key, value in curve.items() if key in ("color", "marker", "label")}
						try:
							if "label" in keywordArguments:
								keywordArguments["label"] = TEX.sanitize(keywordArguments["label"])
								if not keywordArguments["label"]:
									del keywordArguments["label"]
							if "label" in keywordArguments:
								try:
									Drawer.__plt.plot(x, y, **keywordArguments)
								except Exception:
									Drawer.__plt.plot(x, y, label = keywordArguments["label"])
							else:
								Drawer.__plt.plot(x, y, **keywordArguments)
						except Exception:
							Drawer.__plt.plot(x, y)
				logarithmicSpacing = Drawer.__checkLogarithmicSpacing(xValues)
				if logarithmicSpacing:
					Drawer.__plt.xscale("log")
				if isinstance(xLabel, str):
					Drawer.__plt.xlabel(TEX.sanitize(xLabel) + " (logarithmic scale)" if logarithmicSpacing else xLabel.strip(), fontsize = Drawer.__LabelFontSize)
				if isinstance(yLabel, str):
					Drawer.__plt.ylabel(TEX.sanitize(yLabel), fontsize = Drawer.__LabelFontSize)
				_, labels = Drawer.__plt.gca().get_legend_handles_labels()
				if labels:
					Drawer.__plt.legend(loc = "best", frameon = True, fontsize = Drawer.__LegendFontSize)
				Drawer.__plt.tight_layout()
				with BytesIO() as buffer:
					Drawer.__plt.savefig(buffer, format = "pdf")
					Drawer.__plt.close()
					return buffer.getvalue()
			except Exception as e:
				return e
		else:
			return TypeError("The curves should be a tuple or a list containing at least one dictionary. ")
	@staticmethod
	def __sequence2str(items:tuple|list|str, itemPrefix:str = "", itemSuffix:str = "", decimalPlace:int|None = None) -> str|None:
		try:
			if len(items) >= 3:
				return (
					", ".join("{0}{1}{2}".format(itemPrefix, item, itemSuffix) for item in items[:-1])
					+ ", and " + "{0}{1}{2}".format(itemPrefix, items[-1], itemSuffix)
				)
			elif len(items) >= 2:
				return "{0}{1}{2} and {0}{3}{2}".format(itemPrefix, items[0], itemSuffix, items[1])
			elif len(items) == 1:
				return "{0}{1}{2}".format(itemPrefix, items[0], itemSuffix)
			else:
				return ""
		except Exception:
			return None
	@staticmethod
	def __getFigureLabelWithoutPrefix(figureFilePath:str) -> str|None:
		if isinstance(figureFilePath, str):
			buffer = []
			for character in figureFilePath:
				if '-' == character or '0' <= character <= '9' or 'A' <= character <= 'Z' or '_' == character or 'a' <= character <= 'z':
					buffer.append(character)
				else:
					break
			return "".join(buffer) if buffer else None
		else:
			return None
	@staticmethod
	def summarizeCurves(
		curves:tuple|list, figureFilePath:str, independentVariableString:str, dependentVariableString:str, groupingVariableString:str, 
		controlledVariableStrings:tuple|list, controlledVariableValues:tuple|list, decimalPlace:int = Parser.getDefaultPlace()
	) -> str:
		if (
			isinstance(curves, (tuple, list)) and curves and isinstance(figureFilePath, str)
			and all('-' <= character <= '9' or 'A' <= character <= 'Z' or '_' == character or 'a' <= character <= 'z' for character in figureFilePath)
		): # curves = ({"x":(1, 2, 3), "y":(1, 4, 9), "label":"$y = x^2$"}, {"x":(1, 2, 3), "y":(1, 8, 27), "label":"$y = x^3$"})
			countOfCurvesDrawn = 0
			labelMappings = {}
			xValues = set()
			curveMappings = [] # for the table: [(label, {x:y}), ...]
			tableXValues = set()
			for curve in curves: # gather the mappings from a sanitized label to a sum of valid curves
				if (
					isinstance(curve, dict) and "x" in curve and Drawer.__checkNumbers(curve["x"]) and len(set(curve["x"])) == len(curve["x"])
					and "y" in curve and Drawer.__checkNumbers(curve["y"]) and len(curve["x"]) == len(curve["y"])
				):
					countOfCurvesDrawn += 1
					sortedX, sortedY = zip(*sorted(zip(curve["x"], curve["y"]))) # sort $x$ and $y$ by ascending $x$ values
					tableXValues.update(sortedX)
					if "label" in curve and isinstance(curve["label"], str):
						sanitizedLabel = TEX.sanitize(curve["label"])
						if not sanitizedLabel or sanitizedLabel in labelMappings: # the sanitized label is empty or repeated
							labelMappings.clear() # disable statements related to labels
							curveMappings.append(("Curve {0}".format(len(curveMappings) + 1), dict(zip(sortedX, sortedY))))
							break
						else:
							labelMappings[sanitizedLabel] = sum(curve["y"]) # gather information for statements related to relative performance
							xValues.update(curve["x"]) # gather information for statements related to $x$ values
							curveMappings.append((sanitizedLabel, dict(zip(sortedX, sortedY))))
					else: # exists a valid curve without a label
						labelMappings.clear() # disable statements related to labels
						curveMappings.append(("Curve {0}".format(len(curveMappings) + 1), dict(zip(sortedX, sortedY))))
						break
			if countOfCurvesDrawn < 1:
				return ""
			pluralLowercaseGroupingVariableString = TEX.pluralize(TEX.lowercase(groupingVariableString)) # will be used again in relative performance statements
			singularLowercaseGroupingVariableString = TEX.singularize(TEX.lowercase(groupingVariableString)) # will be used again in relative performance statements
			if labelMappings: # avoid "\"\", \"\" and \"\""
				if len(labelMappings) >= 2:
					caption = "Comparison of the {0}{1}".format(
						Drawer.__sequence2str(tuple(labelMappings.keys())), " " + pluralLowercaseGroupingVariableString if pluralLowercaseGroupingVariableString else ""
					)
				else:
					caption = "Plot of the {0}{1}".format(
						Drawer.__sequence2str(tuple(labelMappings.keys())), " " + singularLowercaseGroupingVariableString if singularLowercaseGroupingVariableString else ""
					)
			else:
				if countOfCurvesDrawn >= 2:
					caption = "Comparison of different {0}".format(pluralLowercaseGroupingVariableString) if pluralLowercaseGroupingVariableString else "Comparison"
				else:
					caption = "Plot of the {0}".format(singularLowercaseGroupingVariableString) if singularLowercaseGroupingVariableString else "Plot"
			dependentVariableStringWithArticle = TEX.addArticle(dependentVariableString)
			if dependentVariableStringWithArticle:
				caption += " in terms of {0}".format(dependentVariableStringWithArticle)
			if len(xValues) >= 2:
				pluralIndependentVariableString = TEX.pluralize(independentVariableString)
				if pluralIndependentVariableString:
					caption += ", evaluated at different {0}".format(pluralIndependentVariableString)
			elif len(xValues) == 1:
				singularIndependentVariableString = TEX.singularize(independentVariableString)
				sanitizedIndependentVariableValue = TEX.sanitize(next(iter(xValues)))
				if singularIndependentVariableString and sanitizedIndependentVariableValue:
					if (
						len(singularIndependentVariableString) >= 3 and singularIndependentVariableString.startswith("$") and singularIndependentVariableString.endswith("$")
						and len(sanitizedIndependentVariableValue) >= 3 and sanitizedIndependentVariableValue.startswith("$") and sanitizedIndependentVariableValue.endswith("$")
					):
						caption += ", evaluated at {0} = {1}".format(singularIndependentVariableString[:-1], sanitizedIndependentVariableValue[1:])
					else:
						caption += ", evaluated when {0} is {1}".format(singularIndependentVariableString, sanitizedIndependentVariableValue)
			if isinstance(controlledVariableStrings, (tuple, list)) and isinstance(controlledVariableValues, (tuple, list)):
				sanitizedControlledVariableStrings = []
				sanitizedControlledVariableValues = []
				for controlledVariableString, controlledVariableValue in zip(controlledVariableStrings, controlledVariableValues):
					sanitizedControlledVariableString = TEX.sanitize(controlledVariableString)
					sanitizedControlledVariableValue = TEX.sanitize(controlledVariableValue)
					if sanitizedControlledVariableString and sanitizedControlledVariableValue:
						sanitizedControlledVariableStrings.append(sanitizedControlledVariableString)
						sanitizedControlledVariableValues.append(sanitizedControlledVariableValue)
				if len(sanitizedControlledVariableStrings) >= 2:
					caption += ", with {0} set to {1}, respectively".format(Drawer.__sequence2str(
						tuple(TEX.addArticle(sanitizedControlledVariableString) for sanitizedControlledVariableString in sanitizedControlledVariableStrings)
					), Drawer.__sequence2str(sanitizedControlledVariableValues))
				elif len(sanitizedControlledVariableStrings) == 1:
					caption += ", with {0} set to {1}".format(TEX.addArticle(sanitizedControlledVariableStrings[0]), sanitizedControlledVariableValues[0])
			caption += ". "
			if labelMappings:
				consumptionLikeVariable = TEX.checkConsumptionLikeString(dependentVariableString)
				optimalValue = min(labelMappings.values()) if consumptionLikeVariable else max(labelMappings.values())
				optimalKeys = tuple(key for key, value in labelMappings.items() if isclose(value, optimalValue))
				optimalKeyLength = len(optimalKeys)
				if len(labelMappings) == optimalKeyLength: # no ${groupingVariableString}s are suboptimal
					if optimalKeyLength >= 3:
						caption += "All the {0} are optimal. ".format(pluralLowercaseGroupingVariableString)
					elif 2 == optimalKeyLength:
						caption += "Both {0} are optimal. ".format(pluralLowercaseGroupingVariableString)
				elif optimalKeyLength >= 2:
					if consumptionLikeVariable:
						relativePerformanceMappings = {label:(labelMappings[label] - optimalValue) / labelMappings[label] for label in labelMappings.keys() if label not in optimalKeys}
					else:
						relativePerformanceMappings = {label:(optimalValue - labelMappings[label]) / labelMappings[label] for label in labelMappings.keys() if label not in optimalKeys}
					relativePerformanceMappings = {key:"{{0:.{0}f}}\\%".format(decimalPlace).format(relativePerformanceMappings[key] * 100) for key in relativePerformanceMappings.keys()}
					caption += "The {0}{1} outperform {2} by {3}{4}. ".format(
						Drawer.__sequence2str(optimalKeys), " " + pluralLowercaseGroupingVariableString if pluralLowercaseGroupingVariableString else "", 
						Drawer.__sequence2str(tuple(relativePerformanceMappings.keys())), Drawer.__sequence2str(tuple(relativePerformanceMappings.values())), 
						", respectively" if len(relativePerformanceMappings) >= 2 else ""
					)
				elif 1 == optimalKeyLength:
					if consumptionLikeVariable:
						relativePerformanceMappings = {label:(labelMappings[label] - optimalValue) / labelMappings[label] for label in labelMappings.keys() if label not in optimalKeys}
					else:
						relativePerformanceMappings = {label:(optimalValue - labelMappings[label]) / labelMappings[label] for label in labelMappings.keys() if label not in optimalKeys}
					relativePerformanceMappings = {key:"{{0:.{0}f}}\\%".format(decimalPlace).format(relativePerformanceMappings[key] * 100) for key in relativePerformanceMappings.keys()}
					caption += "The {0}{1} outperforms {2} by {3}{4}. ".format(
						Drawer.__sequence2str(optimalKeys), " " + singularLowercaseGroupingVariableString if singularLowercaseGroupingVariableString else "", 
						Drawer.__sequence2str(tuple(relativePerformanceMappings.keys())), Drawer.__sequence2str(tuple(relativePerformanceMappings.values())), 
						", respectively" if len(relativePerformanceMappings) >= 2 else ""
					)
			figureTEXLines = [
				"\\begin{figure}[htbp]", 
				"\t\\centerline{{\\includegraphics[width=\\columnwidth]{{{0}}}}}".format(figureFilePath), 
				"\t\\caption{{{0}}}".format(caption), 
				"\t\\label{{fig:{0}}}".format(Drawer.__getFigureLabelWithoutPrefix(figureFilePath)), 
				"\\end{figure}"
			]
			capitalizedGroupingVariableString = TEX.capitalize(groupingVariableString)
			tableTEXLines = []
			if curveMappings:
				tableTEXLines.extend((
					"\\begin{table}[htbp]", "\t\\centering", "\t\\caption{{{0}}}".format(caption), #####
					"\t\\begin{{tabular}}{{{0}}}".format("c" * (len(curveMappings) + 1)), "\t\t\\toprule", 
					"\t\t{0} \\\\".format(" & ".join((
						"\\textbf{{{0}}}".format(capitalizedGroupingVariableString if capitalizedGroupingVariableString else "~"), 
						*("\\textbf{{{0}}}".format(label) for label, _ in curveMappings)
					))), "\t\t\\midrule"
				))
				for xValue in sorted(tableXValues):
					tableTEXLines.append("\t\t{0} \\\\".format(" & ".join((
						Drawer.__escapeTEX(xValue), *(Drawer.__escapeTEX(curveMapping[xValue]) if xValue in curveMapping else "" for _, curveMapping in curveMappings)
					))))
				tableTEXLines.extend(("\t\t\\bottomrule", "\t\\end{tabular}%", "\\end{table}"))
			if tableTEXLines:
				figureTEXLines.append("")
				figureTEXLines.extend(tableTEXLines)
			return linesep.join(figureTEXLines)
		else:
			return ""
	@staticmethod
	def tabulateMappings(mappings:dict) -> str|None:
		if not (
			isinstance(mappings, dict) and mappings
			and all(isinstance(key, str) and key and Drawer.checkValues(value) for key, value in mappings.items())
			and len(set(len(value) for value in mappings.values())) == 1
		):
			return None
		variables = tuple(mappings.keys())
		maximumValueLength = max(len(values) for values in mappings.values())
		sanitizedHeaders = tuple("\\textbf{{{0}}}".format(TEX.sanitize(variable) or "~") for variable in variables)
		sanitizedBodyMatrix = []
		for variable in variables:
			tp = tuple(TEX.sanitize(value) or "~" for value in mappings[variable])
			tpLength = len(tp)
			if tpLength < maximumValueLength:
				tp += ("~", ) * (maximumValueLength - tpLength)
			sanitizedBodyMatrix.append(tp)
		variableLength = len(variables)
		sanitizedBodyMatrix = tuple(tuple(sanitizedBodyMatrix[rowIndex][columnIndex] for rowIndex in range(variableLength)) for columnIndex in range(maximumValueLength))
		tableTEXLines = [
			"\\begin{table}[htbp]", 
			"\t\\centering", 
			"\t\\caption{Complete experimental results. }", 
			"\t\\label{tab:mappgins}", 
			"\t\\resizebox{\\columnwidth}{!}{%", 
			"\t\t\\begin{tabular}{{{0}}}".format("c" * variableLength), 
			"\t\t\t\\toprule", 
			"\t\t\t{0} \\\\".format(" & ".join(sanitizedHeaders)), 
			"\t\t\t\\midrule", 
		]
		for sanitizedBodyRow in sanitizedBodyMatrix:
			tableTEXLines.append("\t\t\t{0} \\\\".format(" & ".join(sanitizedBodyRow)))
		tableTEXLines.extend(("\t\t\t\\bottomrule", "\t\t\\end{tabular}%", "\t}", "\\end{table}"))
		return linesep.join(tableTEXLines)
	@staticmethod
	def drawMappings(
		mappings:dict, independentVariables:tuple|list, dependentVariables:tuple|list, groupingVariables:tuple|list, 
		encoding:str = Parser.getDefaultEncoding(), decimalPlace:int = Parser.getDefaultPlace(), appendFullTable:bool = False
	) -> dict|Exception:
		if isinstance(mappings, dict) and all(isinstance(key, str) and Drawer.checkValues(value) for key, value in mappings.items()) and len(set(len(value) for value in mappings.values())) == 1:
			variables = tuple(mappings.keys())
			
			# Fetch independent variable strings #
			independentVariableStrings = []
			if isinstance(independentVariables, (tuple, list)):
				for independentVariable in independentVariables:
					variableString = Drawer.__getVariableString(independentVariable, variables)
					if isinstance(variableString, str):
						independentVariableStrings.append(variableString)
			else:
				variableString = Drawer.__getVariableString(independentVariables, variables)
				if isinstance(variableString, str):
					independentVariableStrings.append(variableString)
			
			# Fetch dependent variable strings #
			dependentVariableStrings = []
			if isinstance(dependentVariables, (tuple, list)):
				for dependentVariable in dependentVariables:
					variableString = Drawer.__getVariableString(dependentVariable, variables)
					if isinstance(variableString, str):
						dependentVariableStrings.append(variableString)
			else:
				variableString = Drawer.__getVariableString(dependentVariables, variables)
				if isinstance(variableString, str):
					dependentVariableStrings.append(variableString)
			
			# Fetch grouping variable strings #
			groupingVariableStrings = []
			if isinstance(groupingVariables, (tuple, list)):
				for groupingVariable in groupingVariables:
					variableString = Drawer.__getVariableString(groupingVariable, variables)
					if isinstance(variableString, str):
						groupingVariableStrings.append(variableString)
			else:
				variableString = Drawer.__getVariableString(groupingVariables, variables)
				if isinstance(variableString, str):
					groupingVariableStrings.append(variableString)
			
			# Check variable strings #
			if not (independentVariableStrings and dependentVariableStrings and groupingVariableStrings):
				return ValueError("Independent, dependent, and grouping variables should not be empty. ")
			seenVariableStrings = set()
			for independentVariableString in independentVariableStrings:
				if independentVariableString in seenVariableStrings:
					return ValueError("The independent variable {0} is repeated. ".format(repr(independentVariableString)))
				else:
					seenVariableStrings.add(independentVariableString)
			for dependentVariableString in dependentVariableStrings:
				if dependentVariableString in seenVariableStrings:
					return ValueError("The dependent variable {0} is repeated. ".format(repr(dependentVariableString)))
				else:
					seenVariableStrings.add(dependentVariableString)
			for groupingVariableString in groupingVariableStrings:
				if groupingVariableString in seenVariableStrings:
					return ValueError("The grouping variable {0} is repeated. ".format(repr(groupingVariableString)))
				else:
					seenVariableStrings.add(groupingVariableString)
			del seenVariableStrings
			
			# Initialize the ``pyplot`` #
			if Drawer.__plt is None:
				configurationStatus = Drawer.configure()
				if configurationStatus is not True:
					return configurationStatus
			
			# Call the single drawing schema #
			valueLength = len(next(iter(mappings.values())))
			byteMappings = {"main.tex":linesep.join((
				"\\documentclass[a4paper]{article}", "\\setlength{\\parindent}{0pt}", "\\usepackage{amsmath,amssymb}", 
				"\\usepackage{bm}", "\\usepackage{graphicx}", "\\usepackage{booktabs}", "", "\\begin{document}", ""
			))}
			validFigureTEXCount = 0
			for groupingVariableString in groupingVariableStrings:
				groupingVariableIndex = variables.index(groupingVariableString) # for naming purposes
				groupingVariableValues = []
				for valueIndex in range(valueLength): # start to make the color and the marker for the same group variable value the same across different figures
					if mappings[groupingVariableString][valueIndex] not in groupingVariableValues:
						groupingVariableValues.append(mappings[groupingVariableString][valueIndex])
				colors = {groupingVariableValue:Drawer.__Colors[enumerationIndex % Drawer.__ColorLength] for (
					enumerationIndex, groupingVariableValue
				) in enumerate(groupingVariableValues)}
				markers = {groupingVariableValue:Drawer.__Markers[enumerationIndex % Drawer.__MarkerLength] for (
					enumerationIndex, groupingVariableValue
				) in enumerate(groupingVariableValues)} # finish
				for independentVariableString in independentVariableStrings:
					if not Drawer.__checkNumbers(mappings[independentVariableString]):
						continue
					independentVariableIndex = variables.index(independentVariableString) # for naming purposes
					controlledVariableStrings = tuple(
						controlledVariableString for controlledVariableString in independentVariableStrings if controlledVariableString != independentVariableString
					)
					controlledVariableIndexes = tuple(variables.index(controlledVariableString) for controlledVariableString in controlledVariableStrings) # for naming purposes
					valueIndexGroups = {} # start to find out all the value index groups to reduce the time complexity
					for valueIndex in range(valueLength):
						valueIndexGroups.setdefault(
							tuple(mappings[controlledVariableString][valueIndex] for controlledVariableString in controlledVariableStrings), []
						).append(valueIndex) # finish
					for dependentVariableString in dependentVariableStrings:
						if not Drawer.__checkNumbers(mappings[dependentVariableString]):
							continue
						dependentVariableIndex = variables.index(dependentVariableString) # for naming purposes
						for curveGroupIndex, (controlledVariableValues, valueIndexGroup) in enumerate(valueIndexGroups.items()):
							curveMappings = {}
							for valueIndex in valueIndexGroup:
								groupingVariableValue = mappings[groupingVariableString][valueIndex]
								curveMappings.setdefault(groupingVariableValue, {})
								curveMappings[groupingVariableValue].setdefault(
									mappings[independentVariableString][valueIndex], []
								).append(mappings[dependentVariableString][valueIndex]) # to avoid multiple ``y`` values
							curves = []
							for outerKey, outerValue in curveMappings.items(): # convert {groupingVariableValue -> {x -> y(s)}} to [{"x":[], "y":[], ...}, ...]
								curves.append({"color":colors[outerKey], "marker":markers[outerKey], "label":outerKey})
								for innerKey, innerValue in outerValue.items(): # x -> y(s)
									if Drawer.__checkNumbers(innerValue):
										innerValueLength = len(innerValue)
										if innerValueLength >= 2:
											curves[-1].setdefault("x", []).append(innerKey)
											curves[-1].setdefault("y", []).append(sum(innerValue) / innerValueLength)
											if curves[-1]["y"][-1].is_integer():
												curves[-1]["y"][-1] = int(curves[-1]["y"][-1])
										elif 1 == innerValueLength:
											curves[-1].setdefault("x", []).append(innerKey)
											curves[-1].setdefault("y", []).append(innerValue[0])
								if not ("x" in curves[-1] and curves[-1]["x"] and "y" in curves[-1] and curves[-1]["y"]):
									del curves[-1]
							figureFilePath = "x{0}y{1}{2}g{3}.pdf".format(independentVariableIndex, dependentVariableIndex, "".join(
								"c{0}".format(controlledVariableIndex) for controlledVariableIndex in controlledVariableIndexes
							), curveGroupIndex)
							byteMappings[figureFilePath] = Drawer.draw(curves, xLabel = independentVariableString, yLabel = dependentVariableString)
							if isinstance(byteMappings[figureFilePath], bytes):
								figureTEX = Drawer.summarizeCurves(
									curves, figureFilePath, independentVariableString, dependentVariableString, groupingVariableString, 
									controlledVariableStrings, controlledVariableValues, decimalPlace = decimalPlace
								)
								if isinstance(figureTEX, str):
									strippedFigureTEX = figureTEX.strip()
									if strippedFigureTEX:
										byteMappings["main.tex"] += strippedFigureTEX + linesep * 2
										validFigureTEXCount += 1
										if validFigureTEXCount % 10 == 0:
											byteMappings["main.tex"] += "\\clearpage" + linesep * 2
			if appendFullTable is True:
				fullTableTEX = Drawer.tabulateMappings(mappings, independentVariableStrings, dependentVariableStrings, groupingVariableStrings)
				if isinstance(fullTableTEX, str):
					strippedFullTableTEX = fullTableTEX.strip()
					byteMappings["main.tex"] += strippedFullTableTEX + linesep * 2
			byteMappings["main.tex"] += "\\end{document}"
			try:
				try:
					lookup(encoding)
					try:
						byteMappings["main.tex"] = byteMappings["main.tex"].encode(encoding)
					except Exception:
						byteMappings["main.tex"] = byteMappings["main.tex"].encode(encoding, errors = "ignore")
				except Exception:
					byteMappings["main.tex"] = byteMappings["main.tex"].encode(Parser.getDefaultEncoding())
			except Exception:
				byteMappings["main.tex"] = byteMappings["main.tex"].encode(Parser.getDefaultEncoding(), errors = "ignore")
			return byteMappings
		else:
			return TypeError("The mappings should be a dictionary containing several mappings from a string to a tuple or a list of numbers. ")

class Analyzer:
	def __init__(self:object, inputFilePaths:tuple|list|str, outputFilePath:str, encoding:str = Parser.getDefaultEncoding(), decimalPlace:int = Parser.getDefaultPlace()) -> object:
		self.__inputFilePaths = inputFilePaths
		self.__outputFilePath = outputFilePath
		self.__encoding = encoding if isinstance(encoding, str) else Parser.getDefaultEncoding()
		self.__decimalPlace = decimalPlace if isinstance(decimalPlace, int) and decimalPlace >= 0 else Parser.getDefaultPlace()
	def load(self:tuple|list|str) -> dict|Exception:
		if isinstance(self.__inputFilePaths, (tuple, list)):
			index, length = 0, len(self.__inputFilePaths)
			while index < length:
				if isinstance(self.__inputFilePaths[index], str):
					mappings = Loader.load(self.__inputFilePaths[index], encoding = self.__encoding)
					if (
						isinstance(mappings, dict) and all(isinstance(key, str) and key and Drawer.checkValues(value) for key, value in mappings.items())
						and len(set(len(value) for value in mappings.values())) == 1
					):
						keys = tuple(mappings.keys())
						sanitizedKeys = tuple(TEX.sanitize(key) for key in keys)
						if None in sanitizedKeys or "" in sanitizedKeys:
							return KeyError("Failed to load the input file(s) due to empty sanitized keys detected in {0}. ".format(repr(self.__inputFilePaths[index])))
						duplicateKeys = {}
						for sanitizedKey in set(sanitizedKeys):
							keyIndexes = tuple(sanitizedKeyIndex for sanitizedKeyIndex, sanitizedKeyValue in enumerate(sanitizedKeys) if sanitizedKeyValue == sanitizedKey)
							if len(keyIndexes) > 1:
								duplicateKeys[sanitizedKey] = {keyIndex:keys[keyIndex] for keyIndex in keyIndexes}
						duplicateKeyCount = len(duplicateKeys)
						if duplicateKeyCount >= 2:
							return KeyError("Failed to load the input file(s) due to the {0} duplicate sanitized keys {1} in {2}. ".format(
								duplicateKeyCount, duplicateKeys, repr(self.__inputFilePaths[index])
							))
						elif 1 == duplicateKeyCount:
							return KeyError("Failed to load the input file(s) due to the duplicate sanitized key {0} in {1}. ".format(
								duplicateKeys, repr(self.__inputFilePaths[index])
							))
						else:
							mappings = {key:value for key, value in zip(sanitizedKeys, mappings.values())}
							sanitizedKeys = set(sanitizedKeys)
							index += 1
							while index < length: # for (++index; index < length; ++index)
								if isinstance(self.__inputFilePaths[index], str):
									currentMappings = Loader.load(self.__inputFilePaths[index], encoding = self.__encoding)
									if (
										isinstance(currentMappings, dict)
										and all(isinstance(key, str) and key and Drawer.checkValues(value) for key, value in currentMappings.items())
										and len(set(len(value) for value in currentMappings.values())) == 1
									):
										currentKeys = tuple(currentMappings.keys())
										sanitizedCurrentKeys = tuple(TEX.sanitize(currentKey) for currentKey in currentKeys)
										if None in sanitizedCurrentKeys or "" in sanitizedCurrentKeys:
											return KeyError("Failed to load the input file(s) due to empty sanitized keys detected in {0}. ".format(
												repr(self.__inputFilePaths[index])
											))
										duplicateCurrentKeys = {}
										for sanitizedCurrentKey in set(sanitizedCurrentKeys):
											currentKeyIndexes = tuple(
												sanitizedCurrentKeyIndex
												for sanitizedCurrentKeyIndex, sanitizedCurrentKeyValue in enumerate(sanitizedCurrentKeys)
												if sanitizedCurrentKeyValue == sanitizedCurrentKey
											)
											if len(currentKeyIndexes) > 1:
												duplicateCurrentKeys[sanitizedCurrentKey] = {
													currentKeyIndex:currentKeys[currentKeyIndex] for currentKeyIndex in currentKeyIndexes
												}
										duplicateCurrentKeyCount = len(duplicateCurrentKeys)
										if duplicateCurrentKeyCount >= 2:
											return KeyError("Failed to load the input file(s) due to the {0} duplicate sanitized keys {1} in {2}. ".format(
												duplicateCurrentKeyCount, duplicateCurrentKeys, repr(self.__inputFilePaths[index])
											))
										elif 1 == duplicateCurrentKeyCount:
											return KeyError("Failed to load the input file(s) due to the duplicate sanitized key {0} in {1}. ".format(
												duplicateCurrentKeys, repr(self.__inputFilePaths[index])
											))
										else:
											currentMappings = {
												currentKey:currentValue for currentKey, currentValue in zip(sanitizedCurrentKeys, currentMappings.values())
											}
											if set(sanitizedCurrentKeys) == sanitizedKeys:
												for key,value in mappings.items():
													value.extend(currentMappings[key])
											else:
												return KeyError(
													(
														"Failed to load the input file(s) since the current sanitized keys {0} from the file {1} "
														+ "mismatched the sanitized keys {2} from the first file {3}. "
													).format(
														sanitizedCurrentKeys, repr(self.__inputFilePaths[index]),
														sanitizedKeys, repr(self.__inputFilePaths[0])
													)
												)
									elif isinstance(currentMappings, Exception):
										return type(currentMappings)("Failed to load the input file(s) due to {0} while loading {1}. ".format(
											repr(currentMappings), repr(self.__inputFilePaths[index])
										))
									else:
										return ValueError("Failed to load the input file(s) due to invalid keys or values detected in {0}. ".format(
											repr(self.__inputFilePaths[index])
										))
								index += 1
							return mappings
					elif isinstance(mappings, Exception):
						return type(mappings)("Failed to load the input file(s) due to {0} while loading {1}. ".format(repr(mappings), repr(self.__inputFilePaths[index])))
					else:
						return ValueError("Failed to load the input file(s) due to invalid keys or values detected in {0}. ".format(repr(self.__inputFilePaths[index])))
				index += 1
			return ValueError("No strings were found in the unit of the input file path(s). ")
		elif isinstance(self.__inputFilePaths, str):
			mappings = Loader.load(self.__inputFilePaths, encoding = self.__encoding)
			if isinstance(mappings, dict) and all(isinstance(key, str) and isinstance(value, (tuple, list)) for key, value in mappings.items()):
				keys = tuple(mappings.keys())
				sanitizedKeys = tuple(TEX.sanitize(key) for key in keys)
				if None in sanitizedKeys or "" in sanitizedKeys:
					return KeyError("Failed to load the input file {0} due to empty sanitized keys detected. ".format(repr(self.__inputFilePaths)))
				duplicateKeys = {}
				for sanitizedKey in set(sanitizedKeys):
					keyIndexes = tuple(sanitizedKeyIndex for sanitizedKeyIndex, sanitizedKeyValue in enumerate(sanitizedKeys) if sanitizedKeyValue == sanitizedKey)
					if len(keyIndexes) > 1:
						duplicateKeys[sanitizedKey] = {keyIndex:keys[keyIndex] for keyIndex in keyIndexes}
				duplicateKeyCount = len(duplicateKeys)
				if duplicateKeyCount >= 2:
					return KeyError("Failed to load the input file {0} due to the {1} duplicate sanitized keys {2}. ".format(
						repr(self.__inputFilePaths), duplicateKeyCount, duplicateKeys
					))
				elif 1 == duplicateKeyCount:
					return KeyError("Failed to load the input file {0} due to the duplicate sanitized key {1}. ".format(repr(self.__inputFilePaths), duplicateKeys))
				else:
					return {key:value for key, value in zip(sanitizedKeys, mappings.values())}
			else:
				return Exception("Failed to load the input file {0} due to {1}. ".format(repr(self.__inputFilePaths), repr(mappings)))
		else:
			return TypeError("The unit of the input file path(s) should be a tuple, a list, or a string. ")
	def analyze(self:object, specifiedGroupingVariable:str|int|None = None, specifiedRunCountVariable:str|int|None = None) -> bool|dict|Exception:
		mappings = self.load()
		if isinstance(mappings, Exception):
			return mappings
		elif (
			isinstance(mappings, dict) and bool(mappings)
			and all(isinstance(key, str) and key and Drawer.checkValues(value) for key, value in mappings.items())
			and len(set(len(value) for value in mappings.values())) == 1
		):
			variables = tuple(mappings.keys())
			lowercaseVariables = tuple(TEX.lowercase(variable) for variable in variables)
			lowercaseVariableLength = len(lowercaseVariables)
			
			# Locate the index of the grouping variable #
			if isinstance(specifiedGroupingVariable, str):
				try:
					groupingVariableIndex = lowercaseVariables.index(TEX.lowercase(specifiedGroupingVariable))
				except Exception as e:
					return e
			elif isinstance(specifiedGroupingVariable, int) and -lowercaseVariableLength <= specifiedGroupingVariable < lowercaseVariableLength:
				groupingVariableIndex = specifiedGroupingVariable if specifiedGroupingVariable >= 0 else lowercaseVariableLength + specifiedGroupingVariable
			else:
				for possibleGroupingVariableString in ("solution", "scheme", "schema", "algorithm"):
					if possibleGroupingVariableString in lowercaseVariables:
						groupingVariableIndex = lowercaseVariables.index(possibleGroupingVariableString)
						break
				else:
					return ValueError("Failed to find a suitable grouping variable in the mappings. ")
			
			# Locate the index of the run count variable #
			if isinstance(specifiedRunCountVariable, str):
				try:
					runCountVariableIndex = lowercaseVariables.index(TEX.lowercase(specifiedRunCountVariable))
				except Exception as e:
					return e
			elif isinstance(specifiedRunCountVariable, int) and -lowercaseVariableLength <= specifiedRunCountVariable < lowercaseVariableLength:
				runCountVariableIndex = specifiedRunCountVariable if specifiedRunCountVariable >= 0 else lowercaseVariableLength + specifiedRunCountVariable
			else:
				for possibleRunCountVariableString in ("run", "run count", "runcount"):
					if possibleRunCountVariableString in lowercaseVariables:
						runCountVariableIndex = lowercaseVariables.index(possibleRunCountVariableString)
						break
				else:
					return ValueError("Failed to find a suitable run count variable in the mappings. ")
			if groupingVariableIndex >= runCountVariableIndex:
				return IndexError("The index of the grouping variable ({0}) must be smaller than the run count variable ({1}). ".format(groupingVariableIndex, runCountVariableIndex))
			
			# Locate the indexes of the dependent variables #
			dependentVariableIndexes = tuple(variableIndex for variableIndex, variableString in enumerate(variables[runCountVariableIndex + 1:], start = runCountVariableIndex + 1) if (
				TEX.checkMathematicalLikeString(variableString) or TEX.checkConsumptionLikeString(variableString)
			))
			if not dependentVariableIndexes:
				return ValueError("Data loaded do not contain metric variables after the run count variable. ")
			
			# Locate the indexes of the validation variables #
			validationVariableIndexes = tuple(variableIndex for variableIndex in range(runCountVariableIndex, dependentVariableIndexes[0]))
			validationVariableStrings = tuple(variables[variableIndex] for variableIndex in validationVariableIndexes)
			dependentVariableIndexes = tuple(dependentVariableIndex for dependentVariableIndex in dependentVariableIndexes if (
				not lowercaseVariables[dependentVariableIndex].startswith(("element of", "elementof"))
			))
			if not dependentVariableIndexes:
				return ValueError("Data loaded do not contain suitable metric variables. ")
			
			# Locate the indexes of the independent variables #
			containingSecurityLevel = any((
				lowercaseVariable in ("security length", "security lengths", "security level", "security levels")
				or lowercaseVariable.startswith(("security length ", "security lengths ", "security level ", "security levels "))
			) for lowercaseVariable in lowercaseVariables)
			independentVariableIndexes = tuple(variableIndex for variableIndex in range(runCountVariableIndex) if variableIndex != groupingVariableIndex and not (
				containingSecurityLevel and lowercaseVariables[variableIndex] in ("$\\lambda$", "curve name", "curvename")
			))
			
			# Remove failed experiments #
			for valueIndex in range(len(next(iter(mappings.values()))) - 1, -1, -1):
				runCountVariableValue = mappings[variables[runCountVariableIndex]][valueIndex]
				for validationVariableString in validationVariableStrings[1:]:
					if mappings[validationVariableString][valueIndex] != runCountVariableValue:
						for value in mappings.values():
							value.pop(valueIndex)
						break
			
			# Call the mapping drawing schema #
			try:
				outputDirectoryPath = dirname(self.__outputFilePath)
				if outputDirectoryPath:
					makedirs(outputDirectoryPath, exist_ok = True)
				byteMappings = Drawer.drawMappings(mappings, independentVariableIndexes, dependentVariableIndexes, groupingVariableIndex)
				if isinstance(byteMappings, dict):
					compressionMappings = {}
					while True: # try our best to avoid ``KeyboardInterrupt`` when writing the output file
						try:
							with ZipFile(self.__outputFilePath if ".zip" == splitext(self.__outputFilePath)[1].lower() else self.__outputFilePath + ".zip", "w") as zf:
								for key, value in byteMappings.items():
									if isinstance(key, str) and isinstance(value, bytes):
										zf.writestr(key, value)
									else:
										compressionMappings[key] = value
							break
						except KeyboardInterrupt:
							continue
					return compressionMappings if compressionMappings else True
				else:
					return byteMappings
			except Exception as e:
				return e
		else:
			return ValueError("The mappings loaded are invalid. ")

class Analyzers:
	def __init__(self:object, *units:tuple, formatString:str = Parser.getDefaultOutput(), encoding:str = Parser.getDefaultEncoding(), decimalPlace:int = Parser.getDefaultPlace()) -> object:
		self.__units = []
		self.__analyzers = []
		self.__formatString = formatString if isinstance(formatString, str) else Parser.getDefaultOutput()
		self.__encoding = encoding if isinstance(encoding, str) else Parser.getDefaultEncoding()
		self.__decimalPlace = decimalPlace if isinstance(decimalPlace, int) and decimalPlace >= 0 else Parser.getDefaultPlace()
		self.__targetCount = 0
		self.__successCount = 0
		self.__failureCount = 0
		self.updateUnits(*units if units else ".")
	@staticmethod
	def __getUnitInputFilePaths(*paths:tuple) -> tuple:
		inputFilePaths, stack = [], list(reversed(paths))
		while stack:
			element = stack.pop()
			if isinstance(element, (tuple, list)):
				stack.extend(reversed(element))
			elif isinstance(element, set):
				stack.extend(sorted(element, reverse = True))
			elif isinstance(element, str):
				if not islink(element):
					if isdir(element):
						filePaths = []
						for root, directoryNames, fileNames in walk(element):
							for fileName in fileNames:
								absoluteFilePath = abspath(join(root, fileName))
								if not islink(absoluteFilePath) and isfile(absoluteFilePath) and absoluteFilePath not in inputFilePaths:
									filePaths.append(absoluteFilePath)
						filePaths.sort()
						inputFilePaths.extend(filePaths)
						del filePaths
					elif isfile(element):
						absoluteFilePath = abspath(element)
						if absoluteFilePath not in inputFilePaths:
							inputFilePaths.append(absoluteFilePath)
		return tuple(inputFilePaths)
	def __format(self:object, _d:str = "", _n:str = "", _p:str = "", _x:str = "") -> str:
		d, n, p, x = _d if isinstance(_d, str) else "", _n if isinstance(_n, str) else "", _p if isinstance(_p, str) else "", _x if isinstance(_x, str) else ""
		buffer, index, length = [], 0, len(self.__formatString)
		while index < length:
			if '%' == self.__formatString[index]:
				index += 1
				if index < length:
					if '%' == self.__formatString[index]:
						buffer.append("%")
					elif 'd' == self.__formatString[index]:
						buffer.append(d)
					elif 'n' == self.__formatString[index]:
						buffer.append(n)
					elif 'p' == self.__formatString[index]:
						buffer.append(p)
					elif 'x' == self.__formatString[index]:
						buffer.append(x)
					else:
						buffer.append("%" + self.__formatString[index])
					index += 1
				else:
					buffer.append("%")
					break
			else:
				buffer.append(self.__formatString[index])
				index += 1
		return "".join(buffer)
	def updateUnits(self:object, *units:tuple) -> int:
		originalLength, stack = len(self.__analyzers), list(reversed(units))
		while stack:
			element = stack.pop()
			if isinstance(element, (tuple, list)):
				stack.extend(reversed(element))
			elif isinstance(element, set):
				stack.extend(sorted(element, reverse = True))
			elif isinstance(element, str):
				try:
					if not islink(element):
						if isdir(element):
							filePaths = []
							for root, directoryNames, fileNames in walk(element):
								for fileName in fileNames:
									absoluteFilePath = abspath(join(root, fileName))
									if not islink(absoluteFilePath) and isfile(absoluteFilePath) and absoluteFilePath not in self.__units:
										filePaths.append(absoluteFilePath)
							filePaths.sort()
							self.__units.extend(filePaths)
							del filePaths
						elif isfile(element):
							absoluteFilePath = abspath(element)
							if absoluteFilePath not in self.__units:
								self.__units.append(absoluteFilePath)
				except Exception as e:
					print("Analyzers: Some or all of {0} were not added to the units due to {1}. ".format(repr(element), repr(e)))
			elif isinstance(element, dict) and "i" in element and isinstance(element["i"], (tuple, list, str)) and "o" in element and isinstance(element["o"], str):
				try:
					inputFilePaths = Analyzers.__getUnitInputFilePaths(element["i"])
					outputFilePath = abspath(element["o"])
					if inputFilePaths and next((
						unit for unit in self.__units if isinstance(unit, dict) and "i" in unit and inputFilePaths == unit["i"] and "o" in unit and outputFilePath == unit["o"]
					), None) is None:
						self.__units.append({
							"i":inputFilePaths, "o":outputFilePath, "e":element["e"] if "e" in element and isinstance(element["e"], str) else self.__encoding, 
							"p":element["p"] if "p" in element and isinstance(element["p"], int) and element["p"] >= 0 else self.__decimalPlace
						})
				except Exception as e:
					print("Analyzers: Failed to add the unit {0} to the units due to {1}. ".format(repr(element), repr(e)))
		index, length = originalLength, len(self.__units)
		while index < length:
			if isinstance(self.__units[index], str):
				dp, nx = split(self.__units[index])
				d, p = splitdrive(dp)
				n, x = splitext(nx)
				self.__analyzers.append(Analyzer(self.__units[index], self.__format(_d = d, _n = n, _p = p, _x = x), encoding = self.__encoding, decimalPlace = self.__decimalPlace))
				index += 1
			elif (
				isinstance(self.__units[index], dict) and "i" in self.__units[index] and isinstance(self.__units[index]["i"], tuple)
				and "o" in self.__units[index] and isinstance(self.__units[index]["o"], str)
			):
				self.__analyzers.append(Analyzer(
					self.__units[index]["i"], self.__units[index]["o"], 
					encoding = self.__units[index]["e"] if "e" in self.__units[index] and isinstance(self.__units[index]["e"], str) else self.__encoding, 
					decimalPlace = self.__units[index]["p"] if (
						"p" in self.__units[index] and isinstance(self.__units[index]["p"], int) and self.__units[index]["p"] >= 0
					) else self.__decimalPlace
				))
				index += 1
			else:
				del self.__units[index]
		currentLength = len(self.__analyzers)
		return currentLength - originalLength
	def analyze(self:object, leftClosing:int|None = None, rightOpening:int|None = None) -> None:
		self.__targetCount = 0
		self.__successCount = 0
		self.__failureCount = 0
		leftClosingIndex = leftClosing if isinstance(leftClosing, int) else 0
		rightOpeningIndex = rightOpening if isinstance(rightOpening, int) else None
		for index, (unit, analyzer) in enumerate(tuple(zip(self.__units, self.__analyzers))[leftClosingIndex:rightOpeningIndex], start = leftClosingIndex):
			self.__targetCount += 1
			result = analyzer.analyze()
			if result is True:
				self.__successCount += 1
			else:
				self.__failureCount += 1
			print("Analyzers: [{0}] {1} -> {2}".format(index, repr(unit), repr(result) if isinstance(result, Exception) else result))
	def getTargetCount(self:object) -> int:
		return self.__targetCount
	def getSuccessCount(self:object) -> int:
		return self.__successCount
	def getFailureCount(self:object) -> int:
		return self.__failureCount
	def __len__(self:object) -> int:
		return len(self.__analyzers)


def main() -> int:
	flag, encoding, outputPathWithoutAnExtension, decimalPlace, waitingTime, units = Parser.parse(argv)
	Parser.disableConsoleEchoes()
	if flag > EXIT_SUCCESS and flag > EOF:
		analyzers = None
		try:
			analyzers = Analyzers(units, formatString = outputPathWithoutAnExtension, encoding = encoding, decimalPlace = decimalPlace)
			totalCount = len(analyzers)
			if totalCount >= 1:
				print("Gathered {0} to be analyzed. ".format(("{0} unit" if 1 == totalCount else "{0} units").format(totalCount)))
				print()
				analyzers.analyze()
				print()
			else:
				print("Nothing to be analyzed, please check the inputs. ")
		except KeyboardInterrupt:
			print()
			print("The analysis was interrupted by users. Saved archives are retained. ")
		except BaseException as e:
			print()
			print("The analysis was interrupted by {0}. Saved archives are retained. ".format(repr(e)))
		errorLevel = EXIT_SUCCESS if isinstance(analyzers, Analyzers) and analyzers.getTargetCount() >= 1 and analyzers.getSuccessCount() >= 1 and analyzers.getFailureCount() == 0 else EXIT_FAILURE
	elif EXIT_SUCCESS == flag:
		errorLevel = flag
	else:
		errorLevel = EOF
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
		print("Please press the Enter key to exit ({0}). ".format(errorLevel))
		try:
			getpass("")
		except:
			print()
	Parser.restoreConsoleEchoes()
	return errorLevel



if "__main__" == __name__:
	exit(main())