from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from buildSchemeLaTeXPDFs import Builder, Parser


class BuildSchemeLaTeXPDFsTest(TestCase):
	def testHelpOptionExitsSuccessfully(self:object) -> None:
		output = StringIO()
		with redirect_stdout(output):
			flag, _, _, paths = Parser(("buildSchemeLaTeXPDFs.py", "-h")).parse()
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

	def testEverySchemeProducesDocumentedProcedures(self:object) -> None:
		root = Path(__file__).resolve().parent
		sources = tuple(
			path for path in sorted(root.glob("Scheme*/Scheme*.py"))
			if not path.is_symlink()
		)
		self.assertEqual(21, len(sources))
		with TemporaryDirectory() as directoryPath:
			for source in sources:
				target = Path(directoryPath) / source.stem / source.stem
				builder = Builder(str(source), str(target))
				builder.generate()
				self.assertGreaterEqual(builder.getFlag(), 2, source)
				latex = target.with_suffix(".tex").read_text(encoding = "utf-8")
				self.assertIn("\\subsection{", latex, source)


if "__main__" == __name__:
	main()
