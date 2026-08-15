from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from libcst import Attribute, CSTNode, Call, ClassDef, FunctionDef, Name, SimpleString, parse_module

from buildSchemeLaTeXPDFs import Builder, Parser


class BuildSchemeLaTeXPDFsTest(TestCase):
	def testHelpOptionExitsSuccessfully(self:object) -> None:
		output = StringIO()
		with redirect_stdout(output):
			flag, _, _, paths = Parser.parse(("buildSchemeLaTeXPDFs.py", "-h"))
		self.assertEqual(0, flag)
		self.assertEqual([], paths)
		self.assertIn("Print this help document.", output.getvalue())

	def testConditionalPrintStringIsCollected(self:object) -> None:
		with TemporaryDirectory() as directoryPath:
			directory = Path(directoryPath)
			source = directory / "SchemeConditional.py"
			source.write_text(
				"def check(flag:bool, value:object) -> None:\n"
				"\tprint(\"value:\", \"N/A\" if flag else value)\n",
				encoding = "utf-8"
			)
			builder = Builder(str(source), str(directory / "SchemeConditional"), True)
			builder.generate()
			self.assertIn("N/A", Builder.getGenerationDiagnostics()[""])

	def testConditionalPrintStringsCanBeCombined(self:object) -> None:
		with TemporaryDirectory() as directoryPath:
			directory = Path(directoryPath)
			source = directory / "SchemeConditional.py"
			source.write_text(
				"def check(flag:bool) -> None:\n"
				"\tprint((\"A\" if flag else \"B\") + \"C\")\n",
				encoding = "utf-8"
			)
			builder = Builder(str(source), str(directory / "SchemeConditional"), True)
			builder.generate()
			self.assertIn("AC", Builder.getGenerationDiagnostics()[""])
			self.assertIn("BC", Builder.getGenerationDiagnostics()[""])

	def testBufferedPrintStringIsCollected(self:object) -> None:
		with TemporaryDirectory() as directoryPath:
			directory = Path(directoryPath)
			source = directory / "SchemeBuffered.py"
			source.write_text(
				"def check() -> None:\n"
				"\tbuffers = []\n"
				"\tbuffers.append(\"Parser: buffered statement. \".format(1))\n"
				"\tfor buffer in buffers:\n"
				"\t\tprint(buffer)\n",
				encoding = "utf-8"
			)
			builder = Builder(str(source), str(directory / "SchemeBuffered"), True)
			builder.generate()
			self.assertIn("Parser: buffered statement. ", Builder.getGenerationDiagnostics()[""])

	def testPathCaseIsPreserved(self:object) -> None:
		_, _, _, paths = Parser.parse(("buildSchemeLaTeXPDFs.py", "SchemeMixedCase/SchemeMixedCase.py"))
		self.assertEqual(["SchemeMixedCase/SchemeMixedCase.py"], paths)

	def testUndocumentedPublicProcedureIsRejected(self:object) -> None:
		with TemporaryDirectory() as directoryPath:
			directory = Path(directoryPath)
			source = directory / "SchemeFallback.py"
			source.write_text(
				"class SchemeFallback:\n"
				"\tdef Setup(self:object) -> tuple:\n"
				"\t\treturn (1, )\n",
				encoding = "utf-8"
			)
			target = directory / "SchemeFallback"
			builder = Builder(str(source), str(target))
			with self.assertRaisesRegex(ValueError, "SchemeFallback.Setup"):
				builder.generate()

	def testEveryPrintStringCanBeEvaluated(self:object) -> None:
		root = Path(__file__).resolve().parent
		for source in self.__getSchemeSources(root):
			tree = parse_module(source.read_bytes())
			builder = Builder(str(source), str(root / source.stem), True)
			bufferedPrintCount, bufferedStringCount, stack = 0, 0, [tree]
			while stack:
				element = stack.pop()
				if isinstance(element, Call) and isinstance(element.func, Name) and "print" == element.func.value:
					for argument in element.args:
						if self.__containsString(argument.value):
							self.assertTrue(builder._Builder__evaluateStrings(argument.value), (source, argument.value))
						elif isinstance(argument.value, Name) and "buffer" == argument.value.value:
							bufferedPrintCount += 1
				elif (
					isinstance(element, Call) and isinstance(element.func, Attribute) and "append" == element.func.attr.value
					and isinstance(element.func.value, Name) and "buffers" == element.func.value.value
				):
					for argument in element.args:
						strings = builder._Builder__evaluateStrings(argument.value)
						self.assertTrue(strings, (source, argument.value))
						bufferedStringCount += len(strings)
				elif isinstance(element, CSTNode):
					stack.extend(reversed(list(element.children)))
			self.assertEqual(1, bufferedPrintCount, source)
			self.assertGreater(bufferedStringCount, 0, source)

	def testEverySchemeProducesEveryPublicProcedure(self:object) -> None:
		root = Path(__file__).resolve().parent
		sources = self.__getSchemeSources(root)
		self.assertTrue(sources)
		with TemporaryDirectory() as directoryPath:
			for source in sources:
				tree = parse_module(source.read_bytes())
				publicProcedureCount = 0
				for element in tree.body:
					if isinstance(element, ClassDef) and element.name.value.startswith("Scheme"):
						publicProcedureCount += sum(
							1 for item in element.body.body
							if isinstance(item, FunctionDef) and not item.name.value.startswith("_") and "getLengthOf" != item.name.value
						)
				target = Path(directoryPath) / source.stem / source.stem
				builder = Builder(str(source), str(target))
				builder.generate()
				self.assertGreaterEqual(builder.getFlag(), 2, source)
				latex = target.with_suffix(".tex").read_text(encoding = "utf-8")
				self.assertGreater(publicProcedureCount, 0, source)
				self.assertEqual(publicProcedureCount, latex.count("\\subsection{"), source)

	@staticmethod
	def __containsString(element:CSTNode) -> bool:
		stack = [element]
		while stack:
			item = stack.pop()
			if isinstance(item, SimpleString):
				return True
			elif isinstance(item, CSTNode):
				stack.extend(reversed(list(item.children)))
		return False

	@staticmethod
	def __getSchemeSources(root:Path) -> tuple:
		return tuple(
			path for path in sorted(root.glob("Scheme*/Scheme*.py"))
			if not path.is_symlink()
		)


if "__main__" == __name__:
	main()
