import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.Console;
import java.io.IOException;
import java.io.OutputStream;
import java.math.BigInteger;
import java.net.URISyntaxException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;

import it.unisa.dia.gas.jpbc.Element;
import it.unisa.dia.gas.jpbc.Pairing;
import it.unisa.dia.gas.jpbc.PairingParameters;
import it.unisa.dia.gas.plaf.jpbc.pairing.PairingFactory;
import it.unisa.dia.gas.plaf.jpbc.pairing.a.TypeACurveGenerator;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.HorizontalAlignment;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.VerticalAlignment;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;


final class Parser
{
	private static final String SCHEME_NAME = "SchemeAAIBME";
	private static final Path SCRIPT_DIRECTORY = getScriptDirectory();
	private static final String[] OPTION_ENCODING = { "e", "/e", "-e", "encoding", "/encoding", "--encoding" };
	private static final String DEFAULT_ENCODING = "utf-8";
	private static final String[] OPTION_HELP = { "h", "/h", "-h", "help", "/help", "--help" };
	private static final String[] OPTION_OUTPUT = { "o", "/o", "-o", "output", "/output", "--output" };
	private static final String DEFAULT_EXTENSION = ".xlsx";
	private static final String DEFAULT_OUTPUT_FILE_NAME = SCHEME_NAME + DEFAULT_EXTENSION;
	private static final Set<String> PROTECTED_EXTENSION_NAMES = Set.of(
		"ASM", "BAT", "C", "CMD", "CPP", "CS", "GO", "H", "HPP", "IPYNB", "JAR", "JAVA", "JS", "KT", "LUA", "M", "O", "PHP", "PS1", "PY", "R", "RB", "RS", "S", "SH", "SQL"
	);
	private static final String[] OPTION_PLACE = { "p", "/p", "-p", "place", "/place", "--place" };
	private static final int DEFAULT_PLACE = 9;
	private static final Map<String, Integer> PLACE_TRANSLATIONS = Map.ofEntries(
		Map.entry("s", 0),
		Map.entry("second", 0),
		Map.entry("ms", 3),
		Map.entry("millisecond", 3),
		Map.entry("microsecond", 6),
		Map.entry("ns", 9),
		Map.entry("nanosecond", 9),
		Map.entry("ps", 12),
		Map.entry("picosecond", 12),
		Map.entry("fs", 15),
		Map.entry("femtosecond", 15)
	);
	private static final String[] OPTION_QUIET = { "q", "/q", "-q", "quiet", "/quiet", "--quiet" };
	private static final String[] OPTION_RUN = { "r", "/r", "-r", "run", "/run", "--run" };
	private static final int DEFAULT_RUN = 10;
	private static final String[] OPTION_TIME = { "t", "/t", "-t", "time", "/time", "--time" };
	private static final double DEFAULT_TIME = Double.POSITIVE_INFINITY;
	private static final String[] OPTION_YES = { "y", "/y", "-y", "yes", "/yes", "--yes" };
	private final String[] arguments;

	private static boolean contains(final String[] values, final String target)
	{
		if (values == null || target == null)
			return false;
		for (final String value : values)
			if (target.equalsIgnoreCase(value))
				return true;
		return false;
	}

	private static String formatOption(final String[] options)
	{
		return "[" + String.join("|", options) + "]";
	}

	private static String escapeString(final Object object)
	{
		final StringBuilder builder = new StringBuilder("\"");
		for (final char character : String.valueOf(object).toCharArray())
		{
			switch (character)
			{
			case '\b':
				builder.append("\\b");
				break;
			case '\t':
				builder.append("\\t");
				break;
			case '\n':
				builder.append("\\n");
				break;
			case '\f':
				builder.append("\\f");
				break;
			case '\r':
				builder.append("\\r");
				break;
			case '\"':
			case '\'':
			case '\\':
				builder.append('\\').append(character);
				break;
			default:
				if (character >= 32 && character <= 126)
					builder.append(character);
				else
					builder.append(String.format(Locale.ROOT, "\\u%04x", (int)character));
				break;
			}
		}
		return builder.append('\"').toString();
	}

	private static void printHelp()
	{
		System.out.println("This is the official implementation of the AA-IB-ME cryptographic scheme in Java based on JPBC.");
		System.out.println();
		System.out.println("Options (case-insensitive):");
		System.out.println("\t" + formatOption(OPTION_ENCODING) + " [utf-8|utf-16|...]\tSpecify the encoding mode. The default value is " + DEFAULT_ENCODING + ".");
		System.out.println("\t" + formatOption(OPTION_HELP) + "\tPrint this help document.");
		System.out.println("\t" + formatOption(OPTION_OUTPUT) + " [path]\tSpecify the output path. The default value is " + escapeString(DEFAULT_OUTPUT_FILE_NAME) + ".");
		System.out.println("\t" + formatOption(OPTION_PLACE) + " [s|ms|ns|0|3|9|...]\tSpecify the decimal place. The default value is " + DEFAULT_PLACE + ".");
		System.out.println("\t" + formatOption(OPTION_QUIET) + "\tDisable verbose console output.");
		System.out.println("\t" + formatOption(OPTION_RUN) + " [1|2|5|10|...]\tSpecify the run count. The default value is " + DEFAULT_RUN + ".");
		System.out.println("\t" + formatOption(OPTION_TIME) + " [0|0.1|1|...|inf]\tSpecify the waiting time before exiting. The default value is " + DEFAULT_TIME + ".");
		System.out.println("\t" + formatOption(OPTION_YES) + "\tConfirm overwriting an existing output file.");
		System.out.println();
	}

	private static String handlePath(final String filePath)
	{
		if (filePath == null)
			return handlePath(DEFAULT_OUTPUT_FILE_NAME);
		if (filePath.isEmpty())
			return "";
		try
		{
			final Path requestedPath = Paths.get(filePath);
			final Path path = (requestedPath.isAbsolute() ? requestedPath : SCRIPT_DIRECTORY.resolve(requestedPath)).normalize();
			if (Files.isDirectory(path) || filePath.endsWith("/") || filePath.endsWith("\\"))
			{
				System.out.println("Parser: The output path looks like a directory and will use the default file name " + escapeString(DEFAULT_OUTPUT_FILE_NAME) + ".");
				return handlePath(path.resolve(DEFAULT_OUTPUT_FILE_NAME).toString());
			}
			final Path fileNamePath = path.getFileName();
			final String fileName = fileNamePath == null ? filePath : fileNamePath.toString();
			final int dotIndex = fileName.lastIndexOf('.');
			final String extension = dotIndex >= 1 ? fileName.substring(dotIndex + 1).toUpperCase(Locale.ROOT) : "";
			if (PROTECTED_EXTENSION_NAMES.contains(extension))
			{
				System.out.println("Parser: The protected extension will be reset to " + escapeString(DEFAULT_EXTENSION) + ".");
				final String baseName = dotIndex >= 1 ? fileName.substring(0, dotIndex) : fileName;
				final Path parent = path.getParent();
				return parent == null ? baseName + DEFAULT_EXTENSION : parent.resolve(baseName + DEFAULT_EXTENSION).toString();
			}
			return path.toString();
		}
		catch (final InvalidPathException exception)
		{
			return SCRIPT_DIRECTORY.resolve(DEFAULT_OUTPUT_FILE_NAME).toString();
		}
	}

	private static Path getScriptDirectory()
	{
		final String sourceFilePath = System.getProperty("jdk.launcher.sourcefile");
		if (sourceFilePath != null && !sourceFilePath.isBlank())
			try
			{
				final Path parent = Paths.get(sourceFilePath).toAbsolutePath().normalize().getParent();
				if (parent != null)
					return parent;
			}
			catch (final InvalidPathException exception)
			{
				/* Fall back to locating the source from the working directory. */
			}
		try
		{
			final Path classLocation = Paths.get(Parser.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
			if (Files.isRegularFile(classLocation) && classLocation.getParent() != null)
				return classLocation.getParent();
			if (Files.isDirectory(classLocation))
				return classLocation;
		}
		catch (final RuntimeException | URISyntaxException exception)
		{
			/* Fall back to locating the source from the working directory. */
		}
		final Path workingDirectory = Paths.get("").toAbsolutePath().normalize();
		final Path nestedSource = workingDirectory.resolve(SCHEME_NAME).resolve(SCHEME_NAME + ".java");
		if (Files.isRegularFile(nestedSource))
			return nestedSource.getParent();
		return workingDirectory;
	}

	private static Number parseRealNumber(final String string)
	{
		if (string == null)
			return null;
		try
		{
			String value = string.replaceAll("[^+\\-.0-9A-Za-z]", "").toLowerCase(Locale.ROOT);
			if (!value.contains("x") && value.contains("e") && !value.endsWith("e"))
				return Double.valueOf(value);
			boolean negative = false;
			while (!value.isEmpty() && (value.charAt(0) == '+' || value.charAt(0) == '-'))
			{
				if (value.charAt(0) == '-')
					negative = !negative;
				value = value.substring(1);
			}
			value = value.replaceFirst("^0+", "");
			int radix = 10;
			if (value.startsWith("b"))
			{
				radix = 2;
				value = value.substring(1);
			}
			else if (value.startsWith("q"))
			{
				radix = 4;
				value = value.substring(1);
			}
			else if (value.startsWith("o"))
			{
				radix = 8;
				value = value.substring(1);
			}
			else if (value.startsWith("d") || value.startsWith("l"))
				value = value.substring(1);
			else if (value.startsWith("h") || value.startsWith("x"))
			{
				radix = 16;
				value = value.substring(1);
			}
			else if (!value.isEmpty())
			{
				final char suffix = value.charAt(value.length() - 1);
				if (suffix == 'b' || suffix == 'q' || suffix == 'o' || suffix == 'd' || suffix == 'l' || suffix == 'h' || suffix == 'x')
				{
					radix = suffix == 'b' ? 2 : suffix == 'q' ? 4 : suffix == 'o' ? 8 : suffix == 'h' || suffix == 'x' ? 16 : 10;
					value = value.substring(0, value.length() - 1);
				}
			}
			if ("inf".equals(value))
				return negative ? Double.NEGATIVE_INFINITY : Double.POSITIVE_INFINITY;
			if ("nan".equals(value))
				return Double.NaN;
			if (value.isEmpty() || ".".equals(value))
				return Integer.valueOf(0);
			final String[] parts = value.split("\\.", -1);
			if (parts.length > 2)
				return null;
			final BigInteger integerPart = parts[0].isEmpty() ? BigInteger.ZERO : new BigInteger(parts[0], radix);
			double decimalPart = 0.0;
			if (parts.length == 2)
				for (int index = parts[1].length() - 1; index >= 0; --index)
				{
					final int digit = Character.digit(parts[1].charAt(index), radix);
					if (digit < 0)
						return null;
					decimalPart = (decimalPart + digit) / radix;
				}
			if (decimalPart == 0.0 && integerPart.bitLength() <= 31)
			{
				final int result = integerPart.intValue();
				return Integer.valueOf(negative ? -result : result);
			}
			final double result = integerPart.doubleValue() + decimalPart;
			return Double.valueOf(negative ? -result : result);
		}
		catch (final RuntimeException exception)
		{
			return null;
		}
	}

	public Parser(final String[] arguments)
	{
		this.arguments = arguments == null ? new String[0] : Arrays.stream(arguments).filter(value -> value != null).toArray(String[]::new);
	}

	public Result parse()
	{
		int flag = 1;
		String encoding = DEFAULT_ENCODING;
		String outputFilePath = handlePath(DEFAULT_OUTPUT_FILE_NAME);
		int decimalPlace = DEFAULT_PLACE;
		boolean verbose = true;
		int runCount = DEFAULT_RUN;
		double waitingTime = DEFAULT_TIME;
		boolean overwritingConfirmed = false;
		final List<String> errors = new ArrayList<>();
		int index = 1;
		while (index < this.arguments.length)
		{
			final String argument = this.arguments[index].toLowerCase(Locale.ROOT);
			if (contains(OPTION_ENCODING, argument))
			{
				++index;
				if (index < this.arguments.length && Charset.isSupported(this.arguments[index]))
					encoding = this.arguments[index];
				else
				{
					flag = -1;
					errors.add("Parser: The encoding value is missing or invalid at [" + index + "].");
				}
			}
			else if (contains(OPTION_HELP, argument))
			{
				printHelp();
				flag = 0;
				break;
			}
			else if (contains(OPTION_OUTPUT, argument))
			{
				++index;
				if (index < this.arguments.length)
					outputFilePath = handlePath(this.arguments[index]);
				else
				{
					flag = -1;
					errors.add("Parser: The output path value is missing at [" + index + "].");
				}
			}
			else if (contains(OPTION_PLACE, argument))
			{
				++index;
				if (index < this.arguments.length)
				{
					final String placeValue = this.arguments[index].toLowerCase(Locale.ROOT);
					if (PLACE_TRANSLATIONS.containsKey(placeValue))
						decimalPlace = PLACE_TRANSLATIONS.get(placeValue).intValue();
					else
					{
						final Number number = parseRealNumber(this.arguments[index]);
						if (number instanceof Integer && number.intValue() >= 0)
							decimalPlace = number.intValue();
						else
						{
							flag = -1;
							errors.add("Parser: The decimal place must be a non-negative integer at [" + index + "].");
						}
					}
				}
				else
				{
					flag = -1;
					errors.add("Parser: The decimal place value is missing at [" + index + "].");
				}
			}
			else if (contains(OPTION_QUIET, argument))
				verbose = false;
			else if (contains(OPTION_RUN, argument))
			{
				++index;
				final Number number = index < this.arguments.length ? parseRealNumber(this.arguments[index]) : null;
				if (number instanceof Integer && number.intValue() >= 1)
					runCount = number.intValue();
				else
				{
					flag = -1;
					errors.add("Parser: The run count must be a positive integer at [" + index + "].");
				}
			}
			else if (contains(OPTION_TIME, argument))
			{
				++index;
				final Number number = index < this.arguments.length ? parseRealNumber(this.arguments[index]) : null;
				if (number != null && !Double.isNaN(number.doubleValue()) && number.doubleValue() >= 0.0)
					waitingTime = number.doubleValue();
				else
				{
					flag = -1;
					errors.add("Parser: The waiting time must be non-negative at [" + index + "].");
				}
			}
			else if (contains(OPTION_YES, argument))
				overwritingConfirmed = true;
			else
			{
				flag = -1;
				errors.add("Parser: The option [" + index + "] = " + escapeString(this.arguments[index]) + " is unknown.");
			}
			++index;
		}
		if (flag == -1)
			for (final String error : errors)
				System.out.println(error);
		return new Result(flag, encoding, outputFilePath, decimalPlace, verbose, runCount, waitingTime, overwritingConfirmed);
	}

	public Result checkOverwriting(final Result result)
	{
		if (result == null)
			return null;
		String outputFilePath = result.outputFilePath();
		boolean confirmed = result.overwritingConfirmed();
		while (!outputFilePath.isEmpty() && Files.exists(Paths.get(outputFilePath)))
		{
			if (!Files.isRegularFile(Paths.get(outputFilePath)))
				System.out.println("Parser: The path " + escapeString(outputFilePath) + " is not a regular file.");
			else if (!confirmed)
			{
				final Console console = System.console();
				final String answer = console == null ? "" : console.readLine("The file %s exists. Overwrite [yN]? ", escapeString(outputFilePath));
				confirmed = answer != null && Set.of("Y", "YES", "1", "T", "TRUE").contains(answer.toUpperCase(Locale.ROOT));
			}
			if (confirmed)
				break;
			final Console console = System.console();
			if (console == null)
			{
				outputFilePath = "";
				break;
			}
			final String replacement = console.readLine("Specify a new output path or leave it empty for console output: ");
			outputFilePath = handlePath(replacement == null ? "" : replacement);
		}
		return new Result(result.flag(), result.encoding(), outputFilePath, result.decimalPlace(), result.verbose(), result.runCount(), result.waitingTime(), confirmed);
	}

	public static String getDefaultOutputFilePath()
	{
		return handlePath(DEFAULT_OUTPUT_FILE_NAME);
	}

	public static int getDefaultPlace()
	{
		return DEFAULT_PLACE;
	}

	public static String getDefaultEncoding()
	{
		return DEFAULT_ENCODING;
	}

	public static String getSchemeName()
	{
		return SCHEME_NAME;
	}

	public static Set<String> getProtectedExtensionNames()
	{
		return PROTECTED_EXTENSION_NAMES;
	}

	public record Result(
		int flag,
		String encoding,
		String outputFilePath,
		int decimalPlace,
		boolean verbose,
		int runCount,
		double waitingTime,
		boolean overwritingConfirmed
	)
	{
	}
}


final class Saver
{
	private final String outputFilePath;
	private final List<String> columns;
	private final int decimalPlace;
	private final Charset encoding;
	private final Path directoryPath;
	private final String extensionName;

	private static String escapeCsv(final Object value)
	{
		final String text = String.valueOf(value);
		if (text.indexOf(',') < 0 && text.indexOf('\"') < 0 && text.indexOf('\n') < 0 && text.indexOf('\r') < 0)
			return text;
		return "\"" + text.replace("\"", "\"\"") + "\"";
	}

	private static String escapeHtml(final Object value)
	{
		return String.valueOf(value).replace("&", "&amp;").replace("\"", "&quot;").replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;").replace("\r\n", "<br />").replace("\n", "<br />").replace("\r", "<br />");
	}

	private static String escapeJson(final Object value)
	{
		if (value == null)
			return "null";
		if (value instanceof Boolean || value instanceof Number)
			return String.valueOf(value);
		final StringBuilder builder = new StringBuilder("\"");
		for (final char character : String.valueOf(value).toCharArray())
		{
			switch (character)
			{
			case '\"':
				builder.append("\\\"");
				break;
			case '\\':
				builder.append("\\\\");
				break;
			case '\b':
				builder.append("\\b");
				break;
			case '\f':
				builder.append("\\f");
				break;
			case '\n':
				builder.append("\\n");
				break;
			case '\r':
				builder.append("\\r");
				break;
			case '\t':
				builder.append("\\t");
				break;
			default:
				if (character < 32)
					builder.append(String.format(Locale.ROOT, "\\u%04x", (int)character));
				else
					builder.append(character);
				break;
			}
		}
		return builder.append('\"').toString();
	}

	private static String escapeTex(final Object value)
	{
		return String.valueOf(value).replace("\\", "\\textbackslash{}").replace("#", "\\#").replace("$", "\\$").replace("%", "\\%").replace("&", "\\&").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}").replace("<", "\\textless{}").replace(">", "\\textgreater{}").replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}");
	}

	private static String escapeXml(final Object value)
	{
		return String.valueOf(value).replace("&", "&amp;").replace("\"", "&quot;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;");
	}

	private String formatValue(final Object value)
	{
		if (value instanceof Float || value instanceof Double)
			return String.format(Locale.ROOT, "%." + this.decimalPlace + "f", ((Number)value).doubleValue());
		return String.valueOf(value);
	}

	private static boolean isIntegralNumber(final Object value)
	{
		if (!(value instanceof Float || value instanceof Double))
			return false;
		final double number = ((Number)value).doubleValue();
		return Double.isFinite(number) && number == Math.rint(number);
	}

	private boolean handleDirectory()
	{
		if (this.directoryPath == null)
			return true;
		try
		{
			Files.createDirectories(this.directoryPath);
			return Files.isDirectory(this.directoryPath);
		}
		catch (final IOException exception)
		{
			return false;
		}
	}

	private void saveCsv(final List<? extends List<?>> results, final char separator) throws IOException
	{
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write(joinSeparated(this.columns, separator));
			writer.newLine();
			for (final List<?> result : results)
			{
				final List<String> values = new ArrayList<>(result.size());
				for (final Object value : result)
					values.add(this.formatValue(value));
				writer.write(joinSeparated(values, separator));
				writer.newLine();
			}
		}
	}

	private static String joinSeparated(final Collection<String> values, final char separator)
	{
		final StringBuilder builder = new StringBuilder();
		boolean first = true;
		for (final String value : values)
		{
			if (!first)
				builder.append(separator);
			builder.append(separator == ',' ? escapeCsv(value) : value.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n"));
			first = false;
		}
		return builder.toString();
	}

	private void saveHtml(final List<? extends List<?>> results) throws IOException
	{
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write("<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta charset=\"" + this.encoding.name() + "\" />\n\t\t<title>" + Parser.getSchemeName() + "</title>\n\t</head>\n\t<body>\n\t\t<table>\n\t\t\t<thead><tr>");
			for (final String column : this.columns)
				writer.write("<th>" + escapeHtml(column) + "</th>");
			writer.write("</tr></thead>\n\t\t\t<tbody>\n");
			for (final List<?> result : results)
			{
				writer.write("\t\t\t\t<tr>");
				for (final Object value : result)
					writer.write("<td>" + escapeHtml(this.formatValue(value)) + "</td>");
				writer.write("</tr>\n");
			}
			writer.write("\t\t\t</tbody>\n\t\t</table>\n\t</body>\n</html>");
		}
	}

	private void saveJson(final List<? extends List<?>> results) throws IOException
	{
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write("{\n\t\"columns\": [");
			for (int index = 0; index < this.columns.size(); ++index)
			{
				if (index > 0)
					writer.write(", ");
				writer.write(escapeJson(this.columns.get(index)));
			}
			writer.write("],\n\t\"results\": [\n");
			for (int rowIndex = 0; rowIndex < results.size(); ++rowIndex)
			{
				writer.write("\t\t[");
				final List<?> result = results.get(rowIndex);
				for (int columnIndex = 0; columnIndex < result.size(); ++columnIndex)
				{
					if (columnIndex > 0)
						writer.write(", ");
					final Object value = result.get(columnIndex);
					writer.write(value instanceof Float || value instanceof Double ? this.formatValue(value) : escapeJson(value));
				}
				writer.write("]" + (rowIndex + 1 < results.size() ? "," : "") + "\n");
			}
			writer.write("\t]\n}");
		}
	}

	private void saveTex(final List<? extends List<?>> results) throws IOException
	{
		final int maximumLength = Math.max(this.columns.size(), results.stream().mapToInt(List::size).max().orElse(0));
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write("\\documentclass[a4paper]{article}\n\\usepackage{booktabs}\n\\begin{document}\n\\begin{tabular}{" + "c".repeat(maximumLength) + "}\n\\toprule\n");
			writer.write(String.join(" & ", this.columns.stream().map(Saver::escapeTex).toList()));
			writer.write(" \\\\\n\\midrule\n");
			for (final List<?> result : results)
			{
				writer.write(String.join(" & ", result.stream().map(this::formatValue).map(Saver::escapeTex).toList()));
				writer.write(" \\\\\n");
			}
			writer.write("\\bottomrule\n\\end{tabular}\n\\end{document}");
		}
	}

	private void saveXml(final List<? extends List<?>> results) throws IOException
	{
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write("<?xml version=\"1.0\" encoding=\"" + this.encoding.name() + "\"?>\n<data>\n\t<columns>\n");
			for (final String column : this.columns)
				writer.write("\t\t<column>" + escapeXml(column) + "</column>\n");
			writer.write("\t</columns>\n\t<results>\n");
			for (final List<?> result : results)
			{
				writer.write("\t\t<result>\n");
				for (final Object value : result)
					writer.write("\t\t\t<r>" + escapeXml(this.formatValue(value)) + "</r>\n");
				writer.write("\t\t</result>\n");
			}
			writer.write("\t</results>\n</data>");
		}
	}

	private void saveYaml(final List<? extends List<?>> results) throws IOException
	{
		try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(this.outputFilePath), this.encoding))
		{
			writer.write("columns:\n");
			for (final String column : this.columns)
				writer.write("  - " + escapeJson(column) + "\n");
			writer.write("results:\n");
			for (final List<?> result : results)
			{
				writer.write("  -");
				if (result.isEmpty())
					writer.write(" []\n");
				else
				{
					writer.write("\n");
					for (final Object value : result)
						writer.write("    - " + escapeJson(value instanceof Float || value instanceof Double ? this.formatValue(value) : value) + "\n");
				}
			}
		}
	}

	private void saveWorkbook(final List<? extends List<?>> results, final boolean xlsx) throws IOException
	{
		try (Workbook workbook = xlsx ? new XSSFWorkbook() : new HSSFWorkbook(); OutputStream stream = Files.newOutputStream(Paths.get(this.outputFilePath), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING))
		{
			final Sheet sheet = workbook.createSheet(Parser.getSchemeName());
			final CellStyle headerStyle = workbook.createCellStyle();
			final Font headerFont = workbook.createFont();
			headerFont.setFontName("Times New Roman");
			headerFont.setFontHeightInPoints((short)12);
			headerFont.setBold(true);
			headerStyle.setFont(headerFont);
			headerStyle.setAlignment(HorizontalAlignment.CENTER);
			headerStyle.setVerticalAlignment(VerticalAlignment.CENTER);
			final CellStyle valueStyle = workbook.createCellStyle();
			final Font valueFont = workbook.createFont();
			valueFont.setFontName("Times New Roman");
			valueFont.setFontHeightInPoints((short)12);
			valueStyle.setFont(valueFont);
			valueStyle.setAlignment(HorizontalAlignment.CENTER);
			valueStyle.setVerticalAlignment(VerticalAlignment.CENTER);
			final Row header = sheet.createRow(0);
			for (int index = 0; index < this.columns.size(); ++index)
			{
				final Cell cell = header.createCell(index);
				cell.setCellValue(this.columns.get(index));
				cell.setCellStyle(headerStyle);
			}
			for (int rowIndex = 0; rowIndex < results.size(); ++rowIndex)
			{
				final Row row = sheet.createRow(rowIndex + 1);
				final List<?> result = results.get(rowIndex);
				for (int columnIndex = 0; columnIndex < result.size(); ++columnIndex)
				{
					final Cell cell = row.createCell(columnIndex);
					final Object value = result.get(columnIndex);
					if (value instanceof Integer || value instanceof Long || isIntegralNumber(value))
						cell.setCellValue(((Number)value).doubleValue());
					else if (value instanceof Boolean)
						cell.setCellValue(((Boolean)value).booleanValue());
					else
						cell.setCellValue(this.formatValue(value));
					cell.setCellStyle(valueStyle);
				}
			}
			if (xlsx)
				sheet.createFreezePane(0, 1);
			workbook.write(stream);
		}
	}

	public Saver(final String outputFilePath, final List<String> columns, final int decimalPlace, final String encoding)
	{
		this.outputFilePath = outputFilePath == null ? Parser.getDefaultOutputFilePath() : outputFilePath;
		this.columns = columns == null ? List.of() : List.copyOf(columns);
		this.decimalPlace = decimalPlace >= 0 ? decimalPlace : Parser.getDefaultPlace();
		this.encoding = encoding != null && Charset.isSupported(encoding) ? Charset.forName(encoding) : StandardCharsets.UTF_8;
		final Path outputPath = this.outputFilePath.isEmpty() ? null : Paths.get(this.outputFilePath);
		this.directoryPath = outputPath == null ? null : outputPath.getParent();
		final String fileName = outputPath == null || outputPath.getFileName() == null ? "" : outputPath.getFileName().toString();
		final int dotIndex = fileName.lastIndexOf('.');
		this.extensionName = dotIndex >= 0 ? fileName.substring(dotIndex + 1).toUpperCase(Locale.ROOT) : "TXT";
	}

	public boolean save(final List<? extends List<?>> results)
	{
		if (results == null)
			return false;
		if (this.outputFilePath.isEmpty())
		{
			System.out.println("Saver: " + Map.of("columns", this.columns, "results", results));
			return true;
		}
		if (!this.handleDirectory())
			return false;
		if (Parser.getProtectedExtensionNames().contains(this.extensionName))
			return false;
		try
		{
			switch (this.extensionName)
			{
			case "CSV":
				this.saveCsv(results, ',');
				break;
			case "TSV":
				this.saveCsv(results, '\t');
				break;
			case "HTM":
			case "HTML":
				this.saveHtml(results);
				break;
			case "JSON":
				this.saveJson(results);
				break;
			case "TEX":
				this.saveTex(results);
				break;
			case "XML":
				this.saveXml(results);
				break;
			case "YAML":
			case "YML":
				this.saveYaml(results);
				break;
			case "XLS":
				this.saveWorkbook(results, false);
				break;
			case "XLSX":
				this.saveWorkbook(results, true);
				break;
			case "TXT":
				Files.writeString(Paths.get(this.outputFilePath), String.valueOf(Map.of("columns", this.columns, "results", results)), this.encoding);
				break;
			default:
				throw new IOException("The " + this.extensionName + " format is not supported.");
			}
			System.out.println("Saver: Successfully saved the results to " + this.outputFilePath + " in the " + this.extensionName + " format.");
			return true;
		}
		catch (final IOException | RuntimeException exception)
		{
			System.out.println("Saver: Failed to save the results to " + this.outputFilePath + " due to " + exception + ".");
			return false;
		}
	}
}


public final class SchemeAAIBME
{
	private static final int EXIT_SUCCESS = 0;
	private static final int EXIT_FAILURE = 1;
	private static final int EOF = -1;
	private static final int DEFAULT_N = 30;
	private static final int DEFAULT_K = 20;
	private static final int DEFAULT_D = 10;
	private static final SecureRandom RANDOM = new SecureRandom();
	private final Pairing pairing;
	private final int securityParameter;
	private int n = DEFAULT_N;
	private int k = DEFAULT_K;
	private int d = DEFAULT_D;
	private MasterPublicKey masterPublicKey = null;
	private MasterSecretKey masterSecretKey = null;
	private boolean setUp = false;

	private static Pairing createPairing(final CurveParameter curveParameter)
	{
		if (curveParameter == null || !"SS512".equalsIgnoreCase(curveParameter.curveName()))
			throw new IllegalArgumentException("Only the symmetric SS512 mapping is supported.");
		final int rBits = curveParameter.securityParameter() < 128 ? Math.max(32, curveParameter.securityParameter()) : 160;
		final int qBits = curveParameter.securityParameter() < 128 ? Math.max(128, rBits * 4) : 512;
		final TypeACurveGenerator generator = new TypeACurveGenerator(RANDOM, rBits, qBits, false);
		final PairingParameters parameters = generator.generate();
		PairingFactory.getInstance().setUsePBCWhenPossible(false);
		return PairingFactory.getPairing(parameters, RANDOM);
	}

	private static double elapsedSeconds(final long startTime)
	{
		return (System.nanoTime() - startTime) / 1_000_000_000.0;
	}

	private static <T> List<T> shuffledCopy(final Collection<T> source)
	{
		final List<T> result = new ArrayList<>(source);
		Collections.shuffle(result, RANDOM);
		return result;
	}

	private static Set<Integer> randomSubset(final Collection<Integer> source, final int size)
	{
		final List<Integer> shuffled = shuffledCopy(source);
		return new LinkedHashSet<>(shuffled.subList(0, Math.min(size, shuffled.size())));
	}

	private Element immutable(final Element element)
	{
		return element.getImmutable();
	}

	private Element scalar(final int value)
	{
		return this.immutable(this.pairing.getZr().newElement(value));
	}

	private Element randomScalar()
	{
		return this.immutable(this.pairing.getZr().newRandomElement());
	}

	private Element randomG1()
	{
		return this.immutable(this.pairing.getG1().newRandomElement());
	}

	private Element randomGT()
	{
		return this.immutable(this.pairing.getGT().newRandomElement());
	}

	private Element oneG1()
	{
		return this.immutable(this.pairing.getG1().newOneElement());
	}

	private Element oneZR()
	{
		return this.immutable(this.pairing.getZr().newOneElement());
	}

	private static Element add(final Element left, final Element right)
	{
		return left.duplicate().add(right).getImmutable();
	}

	private static Element subtract(final Element left, final Element right)
	{
		return left.duplicate().sub(right).getImmutable();
	}

	private static Element multiply(final Element left, final Element right)
	{
		return left.duplicate().mul(right).getImmutable();
	}

	private static Element divide(final Element left, final Element right)
	{
		return left.duplicate().div(right).getImmutable();
	}

	private static Element negate(final Element value)
	{
		return value.duplicate().negate().getImmutable();
	}

	private static Element power(final Element base, final Element exponent)
	{
		return base.duplicate().powZn(exponent).getImmutable();
	}

	private Element pair(final Element left, final Element right)
	{
		return this.immutable(this.pairing.pairing(left, right));
	}

	private Element product(final Collection<Element> elements)
	{
		if (elements == null || elements.isEmpty())
			return this.oneZR();
		Element result = null;
		for (final Element element : elements)
			result = result == null ? element.duplicate() : result.mul(element);
		return this.immutable(result);
	}

	private Element computePolynomial(final Element x, final List<Element> coefficients)
	{
		if (x == null || coefficients == null || coefficients.isEmpty())
			return null;
		final int degree = coefficients.size() - 1;
		Element result = coefficients.get(0).duplicate();
		for (int index = 1; index < degree; ++index)
		{
			Element xPower = x.duplicate();
			for (int powerIndex = 1; powerIndex < index; ++powerIndex)
				xPower.mul(x);
			result.add(coefficients.get(index).duplicate().mul(xPower));
		}
		Element highestPower = x.duplicate();
		for (int powerIndex = 1; powerIndex < degree; ++powerIndex)
			highestPower.mul(x);
		result.add(highestPower);
		return this.immutable(result);
	}

	private List<Element> polynomialCoefficients(final Element constant)
	{
		final List<Element> coefficients = new ArrayList<>(this.d);
		coefficients.add(constant);
		for (int index = 0; index < this.d - 2; ++index)
			coefficients.add(this.randomScalar());
		coefficients.add(this.oneZR());
		return coefficients;
	}

	private Element identityHash(final Element[] vector, final Element[] identity)
	{
		Element result = vector[0].duplicate();
		for (int index = 0; index < this.n; ++index)
			result.mul(power(vector[index + 1], identity[index]));
		return this.immutable(result);
	}

	private Element hashToG1(final byte[] value)
	{
		return this.immutable(this.pairing.getG1().newElementFromHash(value, 0, value.length));
	}

	private static byte[] concatenate(final byte[]... values)
	{
		final ByteArrayOutputStream stream = new ByteArrayOutputStream();
		for (final byte[] value : values)
			stream.writeBytes(value);
		return stream.toByteArray();
	}

	private Element delta(final int index, final Set<Integer> indices, final int x)
	{
		final List<Element> factors = new ArrayList<>();
		for (final int other : indices)
			if (other != index)
				factors.add(divide(this.scalar(x - other), this.scalar(index - other)));
		return this.product(factors);
	}

	private boolean validIdentity(final Element[] identity)
	{
		if (identity == null || identity.length != this.n)
			return false;
		for (final Element element : identity)
			if (element == null || element.getField() != this.pairing.getZr())
				return false;
		return true;
	}

	private boolean validSet(final Set<Integer> values, final int size)
	{
		if (values == null || values.size() != size)
			return false;
		for (final Integer value : values)
			if (value == null || value.intValue() < 0 || value.intValue() >= this.n)
				return false;
		return true;
	}

	private Element[] randomIdentity()
	{
		final Element[] identity = new Element[this.n];
		for (int index = 0; index < identity.length; ++index)
			identity[index] = this.randomScalar();
		return identity;
	}

	private Set<Integer> randomIndexSet(final int size)
	{
		final List<Integer> universe = new ArrayList<>(this.n);
		for (int index = 0; index < this.n; ++index)
			universe.add(Integer.valueOf(index));
		return randomSubset(universe, size);
	}

	private int getLengthOf(final Object object)
	{
		if (object == null)
			return -1;
		if (object instanceof Element)
			return ((Element)object).toBytes().length;
		if (object instanceof Integer || object instanceof Long || object instanceof EncryptionOracle || object instanceof DecryptionOracle)
			return (this.securityParameter + 7) >>> 3;
		if (object instanceof byte[])
			return ((byte[])object).length;
		if (object instanceof Object[])
			return this.sumLengths(Arrays.asList((Object[])object));
		if (object instanceof Collection<?>)
			return this.sumLengths((Collection<?>)object);
		if (object instanceof Map<?, ?>)
			return this.sumLengths(((Map<?, ?>)object).values());
		if (object instanceof MasterPublicKey value)
			return this.sumLengths(List.of(value.g1(), value.g1Prime(), value.g2(), value.g3(), value.y1(), value.y2(), value.v1(), value.v2(), value.v3(), value.v4(), value.uVector(), value.tVector(), value.uPrimeVector(), value.tPrimeVector(), Integer.valueOf(0)));
		if (object instanceof MasterSecretKey value)
			return this.sumLengths(List.of(value.g2Alpha(), value.beta(), value.t1(), value.t2(), value.t3(), value.t4()));
		if (object instanceof EncryptionKeyComponent value)
			return this.sumLengths(List.of(value.first(), value.second()));
		if (object instanceof DecryptionKeyComponent value)
			return this.sumLengths(List.of(value.first(), value.second(), value.third(), value.fourth(), value.fifth()));
		if (object instanceof CipherText value)
			return this.sumLengths(List.of(value.encryptionSet(), value.interpolationSet(), value.c(), value.c1(), value.c2(), value.c3(), value.c4(), value.c5(), value.c6(), value.c7(), value.c8()));
		return -1;
	}

	private int sumLengths(final Collection<?> values)
	{
		long total = 0L;
		for (final Object value : values)
		{
			final int length = this.getLengthOf(value);
			if (length < 0)
				return -1;
			total += length;
			if (total > Integer.MAX_VALUE)
				return Integer.MAX_VALUE;
		}
		return (int)total;
	}

	private static Object printableSize(final int size)
	{
		return size < 0 ? "N/A" : Integer.valueOf(size);
	}

	private static boolean metricPositive(final Object metric)
	{
		return metric instanceof Number && ((Number)metric).doubleValue() > 0.0;
	}

	private static boolean averagedResultValid(final List<Object> result, final int runCount)
	{
		if (result == null || result.size() != 29)
			return false;
		for (int index = 6; index < 12; ++index)
		{
			final Object validator = result.get(index);
			if (validator instanceof Boolean)
			{
				if (runCount != 1 || !((Boolean)validator).booleanValue())
					return false;
			}
			else if (!(validator instanceof Integer) || ((Integer)validator).intValue() != runCount)
				return false;
		}
		for (int index = 12; index < result.size(); ++index)
			if (!metricPositive(result.get(index)))
				return false;
		return true;
	}

	private static List<Object> averageResults(final List<RunResult> runs)
	{
		if (runs.isEmpty())
			return List.of();
		final List<Object> result = new ArrayList<>(runs.get(0).asList());
		final int queryLength = 6;
		final int validatorLength = 6;
		if (runs.size() > 1)
			for (int index = queryLength; index < queryLength + validatorLength; ++index)
			{
				int successes = 0;
				for (final RunResult run : runs)
					if (Boolean.TRUE.equals(run.asList().get(index)))
						++successes;
				result.set(index, Integer.valueOf(successes));
			}
		for (int index = queryLength + validatorLength; index < result.size(); ++index)
		{
			double sum = 0.0;
			boolean valid = true;
			for (final RunResult run : runs)
			{
				final Object metric = run.asList().get(index);
				if (!metricPositive(metric))
				{
					valid = false;
					break;
				}
				sum += ((Number)metric).doubleValue();
			}
			if (!valid)
				result.set(index, "N/A");
			else
			{
				final double average = sum / runs.size();
				if (average == Math.rint(average))
					result.set(index, Integer.valueOf((int)average));
				else
					result.set(index, Double.valueOf(average));
			}
		}
		result.set(5, Integer.valueOf(runs.size()));
		return result;
	}

	private static String formatWaitingTime(final double waitingTime, final int decimalPlace)
	{
		return String.format(Locale.ROOT, "%." + decimalPlace + "f", waitingTime).replaceFirst("0+$", "").replaceFirst("\\.$", "");
	}

	public SchemeAAIBME()
	{
		this(new CurveParameter("SS512", 512));
	}

	public SchemeAAIBME(final CurveParameter curveParameter)
	{
		this(createPairing(curveParameter), curveParameter.securityParameter());
	}

	public SchemeAAIBME(final Pairing pairing, final int securityParameter)
	{
		if (pairing == null || !pairing.isSymmetric())
			throw new IllegalArgumentException("The scheme requires a symmetric pairing.");
		this.pairing = pairing;
		this.securityParameter = securityParameter >= 1 ? securityParameter : 512;
	}

	public SetupResult Setup(final int requestedN, final int requestedK, final int requestedD)
	{
		this.setUp = false;
		if (requestedN >= 1 && requestedD >= 1 && requestedD <= requestedK && requestedK <= requestedN)
		{
			this.n = requestedN;
			this.k = requestedK;
			this.d = requestedD;
		}
		else
		{
			this.n = DEFAULT_N;
			this.k = DEFAULT_K;
			this.d = DEFAULT_D;
			System.out.println("Setup: Invalid n, k, or d was replaced with the default values.");
		}
		final Element g = this.oneG1();
		final Element alpha = this.randomScalar();
		final Element beta = this.randomScalar();
		final Element t1 = this.randomScalar();
		final Element t2 = this.randomScalar();
		final Element t3 = this.randomScalar();
		final Element t4 = this.randomScalar();
		final Element g2 = this.randomG1();
		final Element g3 = this.randomG1();
		final Element[] tVector = new Element[this.n];
		final Element[] tPrimeVector = new Element[this.n];
		final Element[] uVector = new Element[this.n + 1];
		final Element[] uPrimeVector = new Element[this.n + 1];
		for (int index = 0; index < this.n; ++index)
		{
			tVector[index] = this.randomG1();
			tPrimeVector[index] = this.randomG1();
		}
		for (int index = 0; index <= this.n; ++index)
		{
			uVector[index] = this.randomG1();
			uPrimeVector[index] = this.randomG1();
		}
		final Element g1 = power(g, alpha);
		final Element g1Prime = power(g, beta);
		final Element y1 = power(this.pair(g1, g2), multiply(t1, t2));
		final Element y2 = power(this.pair(g3, g), beta);
		final Element v1 = power(g, t1);
		final Element v2 = power(g, t2);
		final Element v3 = power(g, t3);
		final Element v4 = power(g, t4);
		this.masterPublicKey = new MasterPublicKey(g1, g1Prime, g2, g3, y1, y2, v1, v2, v3, v4, uVector, tVector, uPrimeVector, tPrimeVector);
		this.masterSecretKey = new MasterSecretKey(power(g2, alpha), beta, t1, t2, t3, t4);
		this.setUp = true;
		return new SetupResult(this.masterPublicKey, this.masterSecretKey);
	}

	public Map<Integer, EncryptionKeyComponent> EKGen(final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Element[] identity = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element g = this.oneG1();
		final Element[] randomVector = new Element[this.n];
		for (int index = 0; index < this.n; ++index)
			randomVector[index] = this.randomScalar();
		final List<Element> coefficients = this.polynomialCoefficients(this.masterSecretKey.beta());
		final Element identityValue = this.identityHash(this.masterPublicKey.uVector(), identity);
		final List<EncryptionKeyComponent> completeKey = new ArrayList<>(this.n);
		for (int index = 0; index < this.n; ++index)
		{
			final Element qAtIndex = this.computePolynomial(this.scalar(index), coefficients);
			final Element base = multiply(identityValue, this.masterPublicKey.tVector()[index]);
			final Element first = multiply(power(this.masterPublicKey.g3(), qAtIndex), power(base, randomVector[index]));
			final Element second = power(g, randomVector[index]);
			completeKey.add(new EncryptionKeyComponent(first, second));
		}
		final Map<Integer, EncryptionKeyComponent> result = new LinkedHashMap<>();
		for (final int index : selected)
			result.put(Integer.valueOf(index), completeKey.get(index));
		return result;
	}

	public Map<Integer, DecryptionKeyComponent> DKGen(final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Element[] identity = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element g = this.oneG1();
		final Element identityValue = this.identityHash(this.masterPublicKey.uVector(), identity);
		final List<DecryptionKeyComponent> completeKey = new ArrayList<>(this.n);
		for (int index = 0; index < this.n; ++index)
		{
			final Element k1 = this.randomScalar();
			final Element k2 = this.randomScalar();
			final Element base = multiply(identityValue, this.masterPublicKey.tVector()[index]);
			final Element firstExponent = add(multiply(multiply(k1, this.masterSecretKey.t1()), this.masterSecretKey.t2()), multiply(multiply(k2, this.masterSecretKey.t3()), this.masterSecretKey.t4()));
			final Element first = power(g, firstExponent);
			final Element second = multiply(power(this.masterSecretKey.g2Alpha(), negate(this.masterSecretKey.t2())), power(base, negate(multiply(k1, this.masterSecretKey.t2()))));
			final Element third = multiply(power(this.masterSecretKey.g2Alpha(), negate(this.masterSecretKey.t1())), power(base, negate(multiply(k1, this.masterSecretKey.t1()))));
			final Element fourth = power(base, negate(multiply(k2, this.masterSecretKey.t4())));
			final Element fifth = power(base, negate(multiply(k2, this.masterSecretKey.t3())));
			completeKey.add(new DecryptionKeyComponent(first, second, third, fourth, fifth));
		}
		Collections.shuffle(completeKey, RANDOM);
		final Map<Integer, DecryptionKeyComponent> result = new LinkedHashMap<>();
		for (final int index : selected)
			result.put(Integer.valueOf(index), completeKey.get(index));
		return result;
	}

	public CipherText Enc(
		final Map<Integer, EncryptionKeyComponent> requestedEncryptionKey,
		final Element[] requestedIdentityA,
		final Element[] requestedIdentityB,
		final Set<Integer> requestedCipherSet,
		final Set<Integer> requestedEncryptionSet,
		final Element requestedMessage
	)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> cipherSet = this.validSet(requestedCipherSet, this.k) ? new LinkedHashSet<>(requestedCipherSet) : this.randomIndexSet(this.k);
		final Set<Integer> encryptionSet = this.validSet(requestedEncryptionSet, this.d) ? new LinkedHashSet<>(requestedEncryptionSet) : randomSubset(cipherSet, this.d);
		final Element[] identityA = this.validIdentity(requestedIdentityA) ? requestedIdentityA : this.randomIdentity();
		final Map<Integer, EncryptionKeyComponent> encryptionKey = requestedEncryptionKey != null && requestedEncryptionKey.size() == this.d ? requestedEncryptionKey : this.EKGen(identityA, encryptionSet);
		final Element[] identityB = this.validIdentity(requestedIdentityB) ? requestedIdentityB : this.randomIdentity();
		final Element message = requestedMessage != null && requestedMessage.getField() == this.pairing.getGT() ? requestedMessage : this.randomGT();
		final Element g = this.oneG1();
		final Element s = this.randomScalar();
		final Element[] s1Vector = new Element[this.n];
		final Element[] s2Vector = new Element[this.n];
		for (int index = 0; index < this.n; ++index)
		{
			s1Vector[index] = this.randomScalar();
			s2Vector[index] = this.randomScalar();
		}
		final List<Element> coefficients = this.polynomialCoefficients(s);
		final Element ks = power(this.masterPublicKey.y1(), s);
		final Element kl = power(this.masterPublicKey.y2(), s);
		final Element c = multiply(multiply(message, ks), kl);
		final Element identityBValue = this.identityHash(this.masterPublicKey.uVector(), identityB);
		final Map<Integer, Element> c1 = new LinkedHashMap<>();
		final Map<Integer, Element> c2 = new LinkedHashMap<>();
		final Map<Integer, Element> c3 = new LinkedHashMap<>();
		final Map<Integer, Element> c4 = new LinkedHashMap<>();
		final Map<Integer, Element> c5 = new LinkedHashMap<>();
		for (final int index : cipherSet)
		{
			final Element qAtIndex = this.computePolynomial(this.scalar(index), coefficients);
			c1.put(Integer.valueOf(index), power(multiply(identityBValue, this.masterPublicKey.tVector()[index]), qAtIndex));
			c2.put(Integer.valueOf(index), power(this.masterPublicKey.v1(), subtract(qAtIndex, s1Vector[index])));
			c3.put(Integer.valueOf(index), power(this.masterPublicKey.v2(), s1Vector[index]));
			c4.put(Integer.valueOf(index), power(this.masterPublicKey.v3(), subtract(qAtIndex, s2Vector[index])));
			c5.put(Integer.valueOf(index), power(this.masterPublicKey.v4(), s2Vector[index]));
		}
		final Element identityAValue = this.identityHash(this.masterPublicKey.uPrimeVector(), identityA);
		final Map<Integer, Element> c6 = new LinkedHashMap<>();
		final Map<Integer, Element> c7 = new LinkedHashMap<>();
		final Map<Integer, Element> c8 = new LinkedHashMap<>();
		for (final int index : encryptionSet)
		{
			final Element z = this.randomScalar();
			final Element zPrime = this.randomScalar();
			final Element c6Value = power(g, zPrime);
			final EncryptionKeyComponent component = encryptionKey.get(Integer.valueOf(index));
			final Element c7Value = power(multiply(component.second(), power(g, z)), s);
			final byte[] transcript = concatenate(c.toBytes(), c1.get(Integer.valueOf(index)).toBytes(), c2.get(Integer.valueOf(index)).toBytes(), c3.get(Integer.valueOf(index)).toBytes(), c4.get(Integer.valueOf(index)).toBytes(), c5.get(Integer.valueOf(index)).toBytes(), c6Value.toBytes(), c7Value.toBytes());
			final Element c8Value = multiply(multiply(power(component.first(), s), power(multiply(identityAValue, this.masterPublicKey.tPrimeVector()[index]), multiply(s, z))), this.hashToG1(transcript));
			c6.put(Integer.valueOf(index), c6Value);
			c7.put(Integer.valueOf(index), c7Value);
			c8.put(Integer.valueOf(index), c8Value);
		}
		final Set<Integer> intersection = new LinkedHashSet<>(encryptionSet);
		intersection.retainAll(cipherSet);
		final Set<Integer> interpolationSet = intersection.size() >= this.d ? randomSubset(intersection, this.d) : new LinkedHashSet<>(intersection);
		while (interpolationSet.size() < this.d)
			interpolationSet.add(Integer.valueOf(RANDOM.nextInt(this.n)));
		return new CipherText(encryptionSet, interpolationSet, c, c1, c2, c3, c4, c5, c6, c7, c8);
	}

	public Object Dec(
		final Map<Integer, DecryptionKeyComponent> requestedDecryptionKey,
		final Element[] requestedIdentityB,
		final Element[] requestedIdentityA,
		final Set<Integer> requestedCipherSet,
		final Set<Integer> requestedDecryptionSet,
		final CipherText requestedCipherText
	)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> cipherSet = this.validSet(requestedCipherSet, this.k) ? new LinkedHashSet<>(requestedCipherSet) : this.randomIndexSet(this.k);
		final Set<Integer> decryptionSet = this.validSet(requestedDecryptionSet, this.d) ? new LinkedHashSet<>(requestedDecryptionSet) : randomSubset(cipherSet, this.d);
		final Element[] identityB = this.validIdentity(requestedIdentityB) ? requestedIdentityB : this.randomIdentity();
		final Map<Integer, DecryptionKeyComponent> decryptionKey = requestedDecryptionKey != null && requestedDecryptionKey.size() == this.d ? requestedDecryptionKey : this.DKGen(identityB, decryptionSet);
		final Element[] identityA = this.validIdentity(requestedIdentityA) ? requestedIdentityA : this.randomIdentity();
		final CipherText cipherText;
		if (requestedCipherText == null)
		{
			final Set<Integer> encryptionSet = randomSubset(cipherSet, this.d);
			cipherText = this.Enc(this.EKGen(identityA, encryptionSet), identityA, identityB, cipherSet, encryptionSet, this.randomGT());
		}
		else
			cipherText = requestedCipherText;
		final Map<Integer, byte[]> transcripts = new LinkedHashMap<>();
		for (final int index : cipherText.interpolationSet())
			transcripts.put(Integer.valueOf(index), concatenate(cipherText.c().toBytes(), cipherText.c1().get(Integer.valueOf(index)).toBytes(), cipherText.c2().get(Integer.valueOf(index)).toBytes(), cipherText.c3().get(Integer.valueOf(index)).toBytes(), cipherText.c4().get(Integer.valueOf(index)).toBytes(), cipherText.c5().get(Integer.valueOf(index)).toBytes(), cipherText.c6().get(Integer.valueOf(index)).toBytes(), cipherText.c7().get(Integer.valueOf(index)).toBytes()));
		final Element g = this.oneG1();
		final Element identityAValue = this.identityHash(this.masterPublicKey.uPrimeVector(), identityA);
		final List<Element> klFactors = new ArrayList<>();
		for (final int index : cipherText.interpolationSet())
		{
			final Element numerator = this.pair(cipherText.c8().get(Integer.valueOf(index)), g);
			final Element denominator = multiply(this.pair(multiply(identityAValue, this.masterPublicKey.tPrimeVector()[index]), cipherText.c7().get(Integer.valueOf(index))), this.pair(this.hashToG1(transcripts.get(Integer.valueOf(index))), cipherText.c6().get(Integer.valueOf(index))));
			klFactors.add(power(divide(numerator, denominator), this.delta(index, cipherText.interpolationSet(), 0)));
		}
		final Element klPrime = this.product(klFactors);
		final Set<Integer> intersection = new LinkedHashSet<>(decryptionSet);
		intersection.retainAll(cipherSet);
		final Set<Integer> interpolationSet = intersection.size() >= this.d ? randomSubset(intersection, this.d) : intersection;
		while (interpolationSet.size() < this.d)
			interpolationSet.add(Integer.valueOf(RANDOM.nextInt(this.n)));
		final List<Element> ksFactors = new ArrayList<>();
		for (final int index : interpolationSet)
		{
			final DecryptionKeyComponent component = decryptionKey.get(Integer.valueOf(index));
			final Element numerator = multiply(multiply(this.pair(cipherText.c1().get(Integer.valueOf(index)), component.first()), this.pair(cipherText.c2().get(Integer.valueOf(index)), component.second())), this.pair(cipherText.c3().get(Integer.valueOf(index)), component.third()));
			final Element denominator = multiply(this.pair(cipherText.c4().get(Integer.valueOf(index)), component.fourth()), this.pair(cipherText.c5().get(Integer.valueOf(index)), component.fifth()));
			ksFactors.add(power(divide(numerator, denominator), this.delta(index, interpolationSet, 0)));
		}
		final Element ksPrime = this.product(ksFactors);
		final Set<Integer> encryptionIntersection = new LinkedHashSet<>(cipherText.encryptionSet());
		encryptionIntersection.retainAll(cipherSet);
		final Set<Integer> decryptionIntersection = new LinkedHashSet<>(decryptionSet);
		decryptionIntersection.retainAll(cipherSet);
		return encryptionIntersection.size() >= this.d && decryptionIntersection.size() >= this.d ? multiply(multiply(cipherText.c(), ksPrime), klPrime) : Boolean.FALSE;
	}

	public boolean EKeySanity(final Map<Integer, EncryptionKeyComponent> requestedKey, final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element[] identity = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Map<Integer, EncryptionKeyComponent> key = requestedKey != null && requestedKey.size() == this.d ? requestedKey : this.EKGen(identity, selected);
		final Set<Integer> interpolationSet = selected.size() >= this.d ? randomSubset(selected, this.d) : new LinkedHashSet<>(selected);
		while (interpolationSet.size() < this.d)
			interpolationSet.add(Integer.valueOf(RANDOM.nextInt(this.n)));
		final Element g = this.oneG1();
		final Element identityValue = this.identityHash(this.masterPublicKey.uPrimeVector(), identity);
		final List<Element> factors = new ArrayList<>();
		for (final int index : interpolationSet)
		{
			final EncryptionKeyComponent component = key.get(Integer.valueOf(index));
			final Element numerator = this.pair(component.first(), g);
			final Element denominator = this.pair(multiply(identityValue, this.masterPublicKey.tPrimeVector()[index]), component.second());
			factors.add(power(divide(numerator, denominator), this.delta(index, interpolationSet, 0)));
		}
		return this.product(factors).isEqual(this.pair(this.masterPublicKey.g3(), this.masterPublicKey.g1Prime()));
	}

	public boolean DKeySanity(final Map<Integer, DecryptionKeyComponent> requestedKey, final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element[] identity = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Map<Integer, DecryptionKeyComponent> key = requestedKey != null && requestedKey.size() == this.d ? requestedKey : this.DKGen(identity, selected);
		final Element identityValue = this.identityHash(this.masterPublicKey.uVector(), identity);
		final Element reciprocal = this.masterPublicKey.y1().duplicate().invert().getImmutable();
		for (final int index : selected)
		{
			final Element s1 = this.randomScalar();
			final Element s2 = this.randomScalar();
			final Element d1 = multiply(identityValue, this.masterPublicKey.tVector()[index]);
			final Element d2 = power(this.masterPublicKey.v1(), subtract(this.oneZR(), s1));
			final Element d3 = power(this.masterPublicKey.v2(), s1);
			final Element d4 = power(this.masterPublicKey.v3(), subtract(this.oneZR(), s2));
			final Element d5 = power(this.masterPublicKey.v4(), s2);
			final DecryptionKeyComponent component = key.get(Integer.valueOf(index));
			final Element numerator = multiply(multiply(this.pair(d1, component.first()), this.pair(d2, component.second())), this.pair(d3, component.third()));
			final Element denominator = multiply(this.pair(d4, component.fourth()), this.pair(d5, component.fifth()));
			if (!divide(numerator, denominator).isEqual(reciprocal))
				return false;
		}
		return true;
	}

	public boolean Trace1(final EncryptionOracle oracle, final Map<Integer, EncryptionKeyComponent> requestedKey, final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element[] identityA = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Map<Integer, EncryptionKeyComponent> key = requestedKey != null && requestedKey.size() == this.d ? requestedKey : this.EKGen(identityA, selected);
		if (oracle == null || !this.EKeySanity(key, identityA, selected))
			return false;
		final Element message = this.randomGT();
		final Element[] identityB = this.randomIdentity();
		final Set<Integer> cipherSet = new LinkedHashSet<>(selected);
		while (cipherSet.size() < this.k)
			cipherSet.add(Integer.valueOf(RANDOM.nextInt(this.n)));
		final Set<Integer> decryptionSet = randomSubset(cipherSet, this.d);
		try
		{
			final Object decrypted = this.Dec(this.DKGen(identityB, decryptionSet), identityB, identityA, cipherSet, decryptionSet, oracle.apply(key, identityA, identityB, cipherSet, selected, message));
			return decrypted instanceof Element && ((Element)decrypted).isEqual(message);
		}
		catch (final RuntimeException exception)
		{
			return false;
		}
	}

	public boolean Trace2(final DecryptionOracle oracle, final Map<Integer, DecryptionKeyComponent> requestedKey, final Element[] requestedIdentity, final Set<Integer> requestedSet)
	{
		if (!this.setUp)
			this.Setup(DEFAULT_N, DEFAULT_K, DEFAULT_D);
		final Set<Integer> selected = this.validSet(requestedSet, this.d) ? new LinkedHashSet<>(requestedSet) : this.randomIndexSet(this.d);
		final Element[] identityB = this.validIdentity(requestedIdentity) ? requestedIdentity : this.randomIdentity();
		final Map<Integer, DecryptionKeyComponent> key = requestedKey != null && requestedKey.size() == this.d ? requestedKey : this.DKGen(identityB, selected);
		if (oracle == null || !this.DKeySanity(key, identityB, selected))
			return false;
		final Element message = this.randomGT();
		final Element[] identityA = this.randomIdentity();
		final Set<Integer> cipherSet = new LinkedHashSet<>(selected);
		while (cipherSet.size() < this.k)
			cipherSet.add(Integer.valueOf(RANDOM.nextInt(this.n)));
		final Set<Integer> encryptionSet = randomSubset(cipherSet, this.d);
		try
		{
			final CipherText cipherText = this.Enc(this.EKGen(identityA, encryptionSet), identityA, identityB, cipherSet, encryptionSet, message);
			final Object decrypted = oracle.apply(key, identityB, identityA, cipherSet, selected, cipherText);
			return decrypted instanceof Element && ((Element)decrypted).isEqual(message);
		}
		catch (final RuntimeException exception)
		{
			return false;
		}
	}

	public static RunResult conductScheme(final CurveParameter curveParameter, final int n, final int k, final int d, final Integer run, final boolean verbose)
	{
		final String curveName = curveParameter == null ? "N/A" : curveParameter.curveName();
		final int securityParameter = curveParameter == null ? 512 : curveParameter.securityParameter();
		final Object runValue = run != null && run.intValue() >= 1 ? run : "N/A";
		if (verbose)
		{
			System.out.println("Curve: (" + curveName + ", " + securityParameter + ")");
			System.out.println("$n$: " + n);
			System.out.println("$k$: " + k);
			System.out.println("$d$: " + d);
			System.out.println("run: " + runValue);
		}
		if (n < 1 || d < 1 || d > k || k > n)
		{
			if (verbose)
			{
				System.out.println("Is the system valid? No. The parameters $n$, $k$, and $d$ should be three positive integers satisfying $1 \\leqslant d \\leqslant k \\leqslant n$.");
				System.out.println();
			}
			return RunResult.invalid(curveName, securityParameter, n, k, d, runValue);
		}
		final SchemeAAIBME scheme;
		try
		{
			scheme = new SchemeAAIBME(curveParameter);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
			{
				System.out.println("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to " + exception + ".");
				System.out.println();
			}
			return RunResult.invalid(curveName, securityParameter, n, k, d, runValue);
		}
		if (verbose)
			System.out.println("Is the system valid? Yes.");
		try
		{
			final int sizeZR = scheme.getLengthOf(scheme.randomScalar());
			final int sizeG1 = scheme.getLengthOf(scheme.randomG1());
			final int sizeGT = scheme.getLengthOf(scheme.randomGT());
			long startTime = System.nanoTime();
			final SetupResult setupResult = scheme.Setup(n, k, d);
			final double timeSetup = elapsedSeconds(startTime);
			final int sizeMpk = scheme.getLengthOf(setupResult.masterPublicKey());
			final int sizeMsk = scheme.getLengthOf(setupResult.masterSecretKey());
			startTime = System.nanoTime();
			final Element[] identityA = scheme.randomIdentity();
			final Set<Integer> cipherSet = scheme.randomIndexSet(k);
			final Set<Integer> encryptionSet = randomSubset(cipherSet, d);
			final Map<Integer, EncryptionKeyComponent> encryptionKey = scheme.EKGen(identityA, encryptionSet);
			final double timeEKGen = elapsedSeconds(startTime);
			final int sizeEncryptionKey = scheme.getLengthOf(encryptionKey);
			startTime = System.nanoTime();
			final Element[] identityB = scheme.randomIdentity();
			final Set<Integer> decryptionSet = randomSubset(cipherSet, d);
			final Map<Integer, DecryptionKeyComponent> decryptionKey = scheme.DKGen(identityB, decryptionSet);
			final double timeDKGen = elapsedSeconds(startTime);
			final int sizeDecryptionKey = scheme.getLengthOf(decryptionKey);
			startTime = System.nanoTime();
			final Element message = scheme.randomGT();
			final CipherText cipherText = scheme.Enc(encryptionKey, identityA, identityB, cipherSet, encryptionSet, message);
			final double timeEnc = elapsedSeconds(startTime);
			final int sizeCipherText = scheme.getLengthOf(cipherText);
			startTime = System.nanoTime();
			final Object decrypted = scheme.Dec(decryptionKey, identityB, identityA, cipherSet, decryptionSet, cipherText);
			final double timeDec = elapsedSeconds(startTime);
			final boolean schemeCorrect = decrypted instanceof Element && ((Element)decrypted).isEqual(message);
			startTime = System.nanoTime();
			final boolean encryptionKeySane = scheme.EKeySanity(encryptionKey, identityA, encryptionSet);
			final double timeEKeySanity = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final boolean decryptionKeySane = scheme.DKeySanity(decryptionKey, identityB, decryptionSet);
			final double timeDKeySanity = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final boolean tracingOne = scheme.Trace1(scheme::Enc, encryptionKey, identityA, encryptionSet);
			final double timeTrace1 = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final boolean tracingTwo = scheme.Trace2(scheme::Dec, decryptionKey, identityB, decryptionSet);
			final double timeTrace2 = elapsedSeconds(startTime);
			if (verbose)
			{
				System.out.println("Original: " + message);
				System.out.println("Decrypted: " + decrypted);
				System.out.println("Is the scheme correct (M == message)? " + (schemeCorrect ? "Yes" : "No") + ".");
				System.out.println("Is EKey Sanity? " + (encryptionKeySane ? "Yes" : "No") + ".");
				System.out.println("Is DKey Sanity? " + (decryptionKeySane ? "Yes" : "No") + ".");
				System.out.println("Is tracing 1 verified (M1 == message1)? " + (tracingOne ? "Yes" : "No") + ".");
				System.out.println("Is tracing 2 verified (M2 == message2)? " + (tracingTwo ? "Yes" : "No") + ".");
				System.out.println("Time: (" + timeSetup + ", " + timeEKGen + ", " + timeDKGen + ", " + timeEnc + ", " + timeDec + ", " + timeEKeySanity + ", " + timeDKeySanity + ", " + timeTrace1 + ", " + timeTrace2 + ")");
				System.out.println("Space: (" + sizeZR + ", " + sizeG1 + ", " + sizeGT + ", " + sizeMpk + ", " + sizeMsk + ", " + sizeEncryptionKey + ", " + sizeDecryptionKey + ", " + sizeCipherText + ")");
				System.out.println();
			}
			return new RunResult(curveName, securityParameter, n, k, d, runValue, true, schemeCorrect, encryptionKeySane, decryptionKeySane, tracingOne, tracingTwo, timeSetup, timeEKGen, timeDKGen, timeEnc, timeDec, timeEKeySanity, timeDKeySanity, timeTrace1, timeTrace2, printableSize(sizeZR), printableSize(sizeG1), printableSize(sizeGT), printableSize(sizeMpk), printableSize(sizeMsk), printableSize(sizeEncryptionKey), printableSize(sizeDecryptionKey), printableSize(sizeCipherText));
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("The scheme execution failed due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, n, k, d, runValue);
		}
	}

	@FunctionalInterface
	public interface EncryptionOracle
	{
		CipherText apply(Map<Integer, EncryptionKeyComponent> encryptionKey, Element[] identityA, Element[] identityB, Set<Integer> cipherSet, Set<Integer> encryptionSet, Element message);
	}

	@FunctionalInterface
	public interface DecryptionOracle
	{
		Object apply(Map<Integer, DecryptionKeyComponent> decryptionKey, Element[] identityB, Element[] identityA, Set<Integer> cipherSet, Set<Integer> decryptionSet, CipherText cipherText);
	}

	public record CurveParameter(String curveName, int securityParameter)
	{
		public CurveParameter
		{
			curveName = curveName == null || curveName.isBlank() ? "N/A" : curveName;
			securityParameter = securityParameter >= 1 ? securityParameter : 512;
		}
	}

	public record MasterPublicKey(
		Element g1,
		Element g1Prime,
		Element g2,
		Element g3,
		Element y1,
		Element y2,
		Element v1,
		Element v2,
		Element v3,
		Element v4,
		Element[] uVector,
		Element[] tVector,
		Element[] uPrimeVector,
		Element[] tPrimeVector
	)
	{
	}

	public record MasterSecretKey(Element g2Alpha, Element beta, Element t1, Element t2, Element t3, Element t4)
	{
	}

	public record SetupResult(MasterPublicKey masterPublicKey, MasterSecretKey masterSecretKey)
	{
	}

	public record EncryptionKeyComponent(Element first, Element second)
	{
	}

	public record DecryptionKeyComponent(Element first, Element second, Element third, Element fourth, Element fifth)
	{
	}

	public record CipherText(
		Set<Integer> encryptionSet,
		Set<Integer> interpolationSet,
		Element c,
		Map<Integer, Element> c1,
		Map<Integer, Element> c2,
		Map<Integer, Element> c3,
		Map<Integer, Element> c4,
		Map<Integer, Element> c5,
		Map<Integer, Element> c6,
		Map<Integer, Element> c7,
		Map<Integer, Element> c8
	)
	{
	}

	public record RunResult(
		String curveName,
		int securityParameter,
		int n,
		int k,
		int d,
		Object run,
		boolean systemValid,
		boolean schemeCorrect,
		boolean encryptionKeySane,
		boolean decryptionKeySane,
		boolean tracingOneVerified,
		boolean tracingTwoVerified,
		Object setupTime,
		Object encryptionKeyGenerationTime,
		Object decryptionKeyGenerationTime,
		Object encryptionTime,
		Object decryptionTime,
		Object encryptionKeySanityTime,
		Object decryptionKeySanityTime,
		Object tracingOneTime,
		Object tracingTwoTime,
		Object scalarSize,
		Object sourceGroupSize,
		Object targetGroupSize,
		Object masterPublicKeySize,
		Object masterSecretKeySize,
		Object encryptionKeySize,
		Object decryptionKeySize,
		Object cipherTextSize
	)
	{
		private static RunResult invalid(final String curveName, final int securityParameter, final int n, final int k, final int d, final Object run)
		{
			return new RunResult(curveName, securityParameter, n, k, d, run, false, false, false, false, false, false, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A");
		}

		public List<Object> asList()
		{
			return List.of(this.curveName, Integer.valueOf(this.securityParameter), Integer.valueOf(this.n), Integer.valueOf(this.k), Integer.valueOf(this.d), this.run, Boolean.valueOf(this.systemValid), Boolean.valueOf(this.schemeCorrect), Boolean.valueOf(this.encryptionKeySane), Boolean.valueOf(this.decryptionKeySane), Boolean.valueOf(this.tracingOneVerified), Boolean.valueOf(this.tracingTwoVerified), this.setupTime, this.encryptionKeyGenerationTime, this.decryptionKeyGenerationTime, this.encryptionTime, this.decryptionTime, this.encryptionKeySanityTime, this.decryptionKeySanityTime, this.tracingOneTime, this.tracingTwoTime, this.scalarSize, this.sourceGroupSize, this.targetGroupSize, this.masterPublicKeySize, this.masterSecretKeySize, this.encryptionKeySize, this.decryptionKeySize, this.cipherTextSize);
		}
	}

	public static void main(final String[] arguments)
	{
		final String[] parserArguments = new String[(arguments == null ? 0 : arguments.length) + 1];
		parserArguments[0] = Parser.getSchemeName();
		if (arguments != null)
			System.arraycopy(arguments, 0, parserArguments, 1, arguments.length);
		final Parser parser = new Parser(parserArguments);
		Parser.Result options = parser.parse();
		int errorLevel = EOF;
		if (options.flag() > EXIT_SUCCESS && options.flag() > EOF)
		{
			options = parser.checkOverwriting(options);
			System.out.println("The execution has started.");
			System.out.println();
			final List<CurveParameter> curveParameters = List.of(new CurveParameter("SS512", 128), new CurveParameter("SS512", 160), new CurveParameter("SS512", 224), new CurveParameter("SS512", 256), new CurveParameter("SS512", 384), new CurveParameter("SS512", 512));
			final List<String> columns = List.of("curveParameter", "secparam", "n", "k", "d", "runCount", "isSystemValid", "isSchemeCorrect", "isEKeySanity", "isDKeySanity", "isTracing1Verified", "isTracing2Verified", "Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", "EKeySanity (s)", "DKeySanity (s)", "Trace1 (s)", "Trace2 (s)", "elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", "mpk (B)", "msk (B)", "ek_ID_A_S (B)", "dk_ID_B_SPrime (B)", "CT (B)");
			final Saver saver = new Saver(options.outputFilePath(), columns, options.decimalPlace(), options.encoding());
			final List<List<Object>> results = new ArrayList<>();
			try
			{
				for (final CurveParameter curveParameter : curveParameters)
					for (int n = 15; n <= 30; n += 5)
						for (int k = 10; k < n; k += 5)
							for (int d = 5; d < k; d += 5)
							{
								final List<RunResult> runs = new ArrayList<>();
								for (int run = 1; run <= options.runCount(); ++run)
									runs.add(conductScheme(curveParameter, n, k, d, Integer.valueOf(run), options.verbose()));
								results.add(averageResults(runs));
								saver.save(results);
							}
				boolean valid = !results.isEmpty();
				for (final List<Object> result : results)
					if (!averagedResultValid(result, options.runCount()))
					{
						valid = false;
						break;
					}
				errorLevel = valid ? EXIT_SUCCESS : EXIT_FAILURE;
			}
			catch (final RuntimeException exception)
			{
				System.out.println("The experiments were interrupted by " + exception + ". Saved results are retained.");
				errorLevel = EXIT_FAILURE;
			}
		}
		else if (options.flag() == EXIT_SUCCESS)
			errorLevel = EXIT_SUCCESS;
		if (options.waitingTime() == 0.0)
			System.out.println("The execution has finished (" + errorLevel + ").");
		else if (Double.isFinite(options.waitingTime()) && options.waitingTime() > 0.0)
		{
			System.out.println("Please wait " + formatWaitingTime(options.waitingTime(), options.decimalPlace()) + " second(s) for automatic exit (" + errorLevel + ").");
			try
			{
				Thread.sleep((long)(options.waitingTime() * 1000.0));
			}
			catch (final InterruptedException exception)
			{
				Thread.currentThread().interrupt();
			}
			System.out.println("The execution has finished (" + errorLevel + ").");
		}
		else
		{
			System.out.println("Please press the Enter key to exit (" + errorLevel + ").");
			final Console console = System.console();
			if (console != null)
				console.readLine();
			else
			{
				try (Scanner scanner = new Scanner(System.in, StandardCharsets.UTF_8))
				{
					if (scanner.hasNextLine())
						scanner.nextLine();
				}
			}
		}
		System.exit(errorLevel);
	}
}