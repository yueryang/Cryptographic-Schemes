import importlib.util
import io
import os
import sys
import types
import unittest
from contextlib import redirect_stdout


SOURCE_PATH = os.path.join(
	os.path.dirname(__file__), "SchemeCoefficientComputation", "SchemeCoefficientComputation.py"
)


class FakeElement:
	def __init__(self:object, elementType:object, value:int) -> object:
		self.type = elementType
		self.value = value
	def __add__(self:object, other:object) -> object:
		return FakeElement(self.type, self.value + self.__value(other))
	def __eq__(self:object, other:object) -> bool:
		return isinstance(other, FakeElement) and self.type == other.type and self.value == other.value
	def __mul__(self:object, other:object) -> object:
		return FakeElement(self.type, self.value * self.__value(other))
	def __neg__(self:object) -> object:
		return FakeElement(self.type, -self.value)
	def __repr__(self:object) -> str:
		return "FakeElement({0}, {1})".format(repr(self.type), self.value)
	def __radd__(self:object, other:object) -> object:
		return self + other
	def __rmul__(self:object, other:object) -> object:
		return self * other
	@staticmethod
	def __value(value:object) -> int:
		return value.value if isinstance(value, FakeElement) else value


class FakePairingGroup:
	def __init__(self:object, curveType:str) -> object:
		self.curveType = curveType
		self.__randomValue = 100
	def init(self:object, elementType:object, value:int) -> FakeElement:
		return FakeElement(elementType, value)
	def random(self:object, elementType:object) -> FakeElement:
		self.__randomValue += 1
		return FakeElement(elementType, self.__randomValue)


def loadModule() -> object:
	charm = types.ModuleType("charm")
	toolbox = types.ModuleType("charm.toolbox")
	pairingGroup = types.ModuleType("charm.toolbox.pairinggroup")
	pairingGroup.PairingGroup = FakePairingGroup
	pairingGroup.ZR = "ZR"
	pairingGroup.pc_element = FakeElement
	modules = {
		"charm":charm,
		"charm.toolbox":toolbox,
		"charm.toolbox.pairinggroup":pairingGroup
	}
	originalModules = {name:sys.modules.get(name) for name in modules}
	originalDirectory = os.getcwd()
	try:
		sys.modules.update(modules)
		specification = importlib.util.spec_from_file_location("scheme_coefficient_computation_test", SOURCE_PATH)
		module = importlib.util.module_from_spec(specification)
		specification.loader.exec_module(module)
		return module
	finally:
		os.chdir(originalDirectory)
		for name, originalModule in originalModules.items():
			if originalModule is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = originalModule


class RuntimeOutputTests(unittest.TestCase):
	def testVerboseResultsArePrintedBeforeDevicePhaseFinishes(self:object) -> None:
		module = loadModule()
		comparator = module.SchemeCoefficientComputation()
		def interruptDevicePhase(**kwargs:dict) -> list:
			raise RuntimeError("stop after the basic phase")
		setattr(comparator, "_SchemeCoefficientComputation__conductDeviceScheme", interruptDevicePhase)
		output = io.StringIO()
		with self.assertRaisesRegex(RuntimeError, "stop after the basic phase"), redirect_stdout(output):
			comparator.conductScheme(r = 1, isVerbose = True)
		text = output.getvalue()
		self.assertIn("Target: Dry run\n", text)
		self.assertIn("Curve: MNT201\n", text)
		self.assertIn("Is ``group.init(type, 1)`` reliable? Yes.\n", text)
		self.assertIn("Is ``group.init(type, 1)`` reliable? No.\n", text)
		self.assertIn("Scheme: Constant2Highest.", text)
		self.assertIn("run: 1\n", text)
		self.assertIn("Correctness: 1 / 1\n", text)
		self.assertIn("Time: ", text)
		expectedResultCount = (
			len(module.Solutions.Constant2Highest.getAllSolutions()) + len(module.Solutions.Highest2Constant.getAllSolutions())
		) * 2 * 3
		self.assertEqual(expectedResultCount, text.count("Target: "))
		self.assertNotIn("\t".join(module.TABLE_HEADER), text)
	def testQuietModeSuppressesResultOutput(self:object) -> None:
		module = loadModule()
		comparator = module.SchemeCoefficientComputation()
		output = io.StringIO()
		with redirect_stdout(output):
			results = comparator._SchemeCoefficientComputation__conductBasicScheme(r = 1, isVerbose = False)
		expectedResultCount = (
			len(module.Solutions.Constant2Highest.getAllSolutions()) + len(module.Solutions.Highest2Constant.getAllSolutions())
		) * 2 * 3
		self.assertEqual(expectedResultCount, len(results))
		self.assertTrue(all(len(result) == len(module.TABLE_HEADER) for result in results))
		self.assertEqual("", output.getvalue())
		self.assertFalse(module.Parser.parse(("SchemeCoefficientComputation.py", "/q"))[4])


if __name__ == "__main__":
	unittest.main()
