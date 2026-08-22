from ast import Assign, Attribute, Call, ClassDef, Constant, FunctionDef, List, Name, Return, Tuple, parse, walk
from os import chdir, getcwd
from pathlib import Path
from runpy import run_path
from unittest import TestCase, main


ROOT = Path(__file__).resolve().parent
STATIC_SAVER_MEMBERS = (
	"__Writer",
	"__escapeHTML",
	"__dumpsJSON",
	"__escapeTEX",
	"__columnsTEX",
	"__WorkbookXLS",
	"__styleXLSColumns",
	"__styleXLSValues",
	"__WorkbookXLSX",
	"__alignmentXLSX",
	"__fontXLSXColumns",
	"__fontXLSXValues",
	"__escapeXLSX",
	"__escapeXML",
)


def schemeFilePaths() -> tuple:
	return tuple(sorted(ROOT.glob("Scheme*/Scheme*.py")))


def findDefinition(tree:object, definitionType:type, name:str) -> object:
	definitions = tuple(node for node in walk(tree) if isinstance(node, definitionType) and node.name == name)
	if len(definitions) != 1:
		raise AssertionError("Expected one {0} definition, found {1}. ".format(name, len(definitions)))
	return definitions[0]


class SchemePythonContractTests(TestCase):
	def test_saver_construction_does_not_reset_static_dependencies(self:object) -> None:
		originalDirectory = getcwd()
		try:
			for path in schemeFilePaths():
				with self.subTest(path = str(path.relative_to(ROOT))):
					namespace = run_path(str(path))
					saverClass = namespace["Saver"]
					sentinel = object()
					setattr(saverClass, "_Saver__Writer", sentinel)
					firstSaver = saverClass("")
					secondSaver = saverClass("")
					self.assertIs(sentinel, getattr(saverClass, "_Saver__Writer"))
					self.assertNotIn("_Saver__Writer", vars(firstSaver))
					self.assertNotIn("_Saver__Writer", vars(secondSaver))
					chdir(originalDirectory)
		finally:
			chdir(originalDirectory)

	def test_saver_dependencies_are_private_static_members(self:object) -> None:
		for path in schemeFilePaths():
			with self.subTest(path = str(path.relative_to(ROOT))):
				tree = parse(path.read_text(encoding = "utf-8"), filename = str(path))
				saver = findDefinition(tree, ClassDef, "Saver")
				staticMembers = {
					target.id
					for statement in saver.body
					if isinstance(statement, Assign) and isinstance(statement.value, Constant) and statement.value.value is None
					for target in statement.targets
					if isinstance(target, Name)
				}
				self.assertTrue(set(STATIC_SAVER_MEMBERS).issubset(staticMembers))
				for node in walk(saver):
					if isinstance(node, Attribute) and node.attr in STATIC_SAVER_MEMBERS:
						self.assertIsInstance(node.value, Name)
						self.assertEqual("Saver", node.value.id)

	def test_pairing_schemes_include_the_scheme_name_in_results(self:object) -> None:
		coefficientPath = ROOT / "SchemeCoefficientComputation" / "SchemeCoefficientComputation.py"
		for path in schemeFilePaths():
			content = path.read_text(encoding = "utf-8")
			if path == coefficientPath or "PairingGroup" not in content:
				continue
			with self.subTest(path = str(path.relative_to(ROOT))):
				tree = parse(content, filename = str(path))
				conductScheme = findDefinition(tree, FunctionDef, "conductScheme")
				returns = tuple(node for node in walk(conductScheme) if isinstance(node, Return))
				self.assertEqual(1, len(returns))
				self.assertIsInstance(returns[0].value, List)
				firstResult = returns[0].value.elts[0]
				self.assertIsInstance(firstResult, Call)
				self.assertIsInstance(firstResult.func, Attribute)
				self.assertIsInstance(firstResult.func.value, Name)
				self.assertEqual("Parser", firstResult.func.value.id)
				self.assertEqual("getSchemeName", firstResult.func.attr)

	def test_pairing_scheme_queries_begin_with_scheme(self:object) -> None:
		coefficientPath = ROOT / "SchemeCoefficientComputation" / "SchemeCoefficientComputation.py"
		for path in schemeFilePaths():
			content = path.read_text(encoding = "utf-8")
			if path == coefficientPath or "PairingGroup" not in content:
				continue
			with self.subTest(path = str(path.relative_to(ROOT))):
				tree = parse(content, filename = str(path))
				mainFunction = findDefinition(tree, FunctionDef, "main")
				assignments = tuple(
					node for node in walk(mainFunction)
					if isinstance(node, Assign)
					and any(isinstance(target, Name) and target.id == "queries" for target in node.targets)
				)
				self.assertEqual(1, len(assignments))
				self.assertIsInstance(assignments[0].value, Tuple)
				self.assertIsInstance(assignments[0].value.elts[0], Constant)
				self.assertEqual("scheme", assignments[0].value.elts[0].value)


if "__main__" == __name__:
	main()
