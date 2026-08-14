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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
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
	private static final String SCHEME_NAME = "SchemePBAC";
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
		System.out.println("This is a possible implementation of the PBAC cryptographic scheme in Java based on JPBC.");
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


public final class SchemePBAC
{
	private static final int EXIT_SUCCESS = 0;
	private static final int EXIT_FAILURE = 1;
	private static final int EOF = -1;
	private static final SecureRandom RANDOM = new SecureRandom();
	private final Pairing pairing;
	private final int securityParameter;
	private final int messageBytes;
	private final BigInteger operand;
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

	private Element immutable(final Element element)
	{
		return element.getImmutable();
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

	private static Element multiply(final Element left, final Element right)
	{
		return left.duplicate().mul(right).getImmutable();
	}

	private static Element divide(final Element left, final Element right)
	{
		return left.duplicate().div(right).getImmutable();
	}

	private static Element power(final Element base, final Element exponent)
	{
		return base.duplicate().powZn(exponent).getImmutable();
	}

	private Element pair(final Element left, final Element right)
	{
		return this.immutable(this.pairing.pairing(left, right));
	}

	private Element hashToG1(final byte[] value)
	{
		return this.immutable(this.pairing.getG1().newElementFromHash(value, 0, value.length));
	}

	private Element hashToScalar(final byte[] value)
	{
		return this.immutable(this.pairing.getZr().newElementFromHash(value, 0, value.length));
	}

	private Element hash3(final Element first, final Element second, final BigInteger message)
	{
		return this.hashToScalar(concatenate(first.toBytes(), second.toBytes(), toFixedBytes(message, this.messageBytes)));
	}

	private BigInteger hash4(final Element value)
	{
		final String algorithm;
		if (this.securityParameter == 128)
			algorithm = "MD5";
		else if (this.securityParameter == 160)
			algorithm = "SHA-1";
		else if (this.securityParameter == 224)
			algorithm = "SHA3-224";
		else if (this.securityParameter == 256)
			algorithm = "SHA3-256";
		else if (this.securityParameter == 384)
			algorithm = "SHA3-384";
		else
			algorithm = "SHA3-512";
		try
		{
			final MessageDigest digest = MessageDigest.getInstance(algorithm);
			final ByteArrayOutputStream output = new ByteArrayOutputStream();
			while (output.size() < this.messageBytes)
				output.writeBytes(digest.digest(value.toBytes()));
			return new BigInteger(1, Arrays.copyOf(output.toByteArray(), this.messageBytes)).and(this.operand);
		}
		catch (final NoSuchAlgorithmException exception)
		{
			throw new IllegalStateException("The required digest is unavailable.", exception);
		}
	}

	private byte[] randomIdentity()
	{
		final byte[] identity = new byte[this.messageBytes];
		RANDOM.nextBytes(identity);
		return identity;
	}

	private static byte[] concatenate(final byte[]... values)
	{
		final ByteArrayOutputStream stream = new ByteArrayOutputStream();
		for (final byte[] value : values)
			stream.writeBytes(value);
		return stream.toByteArray();
	}

	private static byte[] unsignedBytes(final BigInteger value)
	{
		final byte[] bytes = value.toByteArray();
		if (bytes.length > 1 && bytes[0] == 0)
			return Arrays.copyOfRange(bytes, 1, bytes.length);
		return bytes;
	}

	private static byte[] toFixedBytes(final BigInteger value, final int length)
	{
		final byte[] source = unsignedBytes(value);
		final byte[] result = new byte[length];
		final int copied = Math.min(source.length, length);
		System.arraycopy(source, source.length - copied, result, length - copied, copied);
		return result;
	}

	private byte[] cipherDigestInput(final byte[] identity, final CipherText cipherText)
	{
		return concatenate(identity, cipherText.c1().toBytes(), cipherText.c2().toBytes(), cipherText.c3().toBytes(), unsignedBytes(cipherText.c4()));
	}

	private BigInteger normalizeMessage(final Object message)
	{
		final BigInteger candidate;
		if (message instanceof BigInteger && ((BigInteger)message).signum() >= 0)
			candidate = (BigInteger)message;
		else if (message instanceof Number && ((Number)message).longValue() >= 0L)
			candidate = BigInteger.valueOf(((Number)message).longValue());
		else if (message instanceof byte[])
			candidate = new BigInteger(1, (byte[])message);
		else
			candidate = new BigInteger(1, "SchemePBAC".getBytes(StandardCharsets.UTF_8));
		return candidate.and(this.operand);
	}

	private int getLengthOf(final Object object)
	{
		if (object == null)
			return -1;
		if (object instanceof Element)
			return ((Element)object).toBytes().length;
		if (object instanceof BigInteger || object instanceof Integer || object instanceof Long)
			return this.messageBytes;
		if (object instanceof byte[])
			return ((byte[])object).length;
		if (object instanceof Collection<?>)
			return this.sumLengths((Collection<?>)object);
		if (object instanceof MasterPublicKey value)
			return this.sumLengths(List.of(value.g(), value.gHat(), Integer.valueOf(0), Integer.valueOf(0), Integer.valueOf(0), Integer.valueOf(0), Integer.valueOf(0), Integer.valueOf(0)));
		if (object instanceof MasterSecretKey value)
			return this.sumLengths(List.of(value.s(), value.alpha()));
		if (object instanceof ReceiverKey value)
			return this.sumLengths(List.of(value.first(), value.second()));
		if (object instanceof CipherText value)
			return this.sumLengths(List.of(value.c1(), value.c2(), value.c3(), value.c4(), value.signature()));
		if (object instanceof ReKeyPart value)
			return this.sumLengths(List.of(value.nonce(), value.component()));
		if (object instanceof ReEncryptionKey value)
			return this.sumLengths(List.of(value.identity1(), value.identity2(), value.first(), value.second()));
		if (object instanceof TransformedCipherText value)
			return this.sumLengths(List.of(value.identity1(), value.c1(), value.c2Prime(), value.c3Prime(), value.c4(), value.nonce1(), value.nonce2()));
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
		}
		return total > Integer.MAX_VALUE ? Integer.MAX_VALUE : (int)total;
	}

	private static Object printableSize(final int size)
	{
		return size < 0 ? "N/A" : Integer.valueOf(size);
	}

	private static boolean metricPositive(final Object metric)
	{
		return metric instanceof Number && ((Number)metric).doubleValue() > 0.0;
	}

	private static List<Object> averageResults(final List<RunResult> runs)
	{
		if (runs.isEmpty())
			return List.of();
		final List<Object> result = new ArrayList<>(runs.get(0).asList());
		if (runs.size() > 1)
			for (int index = 3; index < 7; ++index)
			{
				int successes = 0;
				for (final RunResult run : runs)
					if (Boolean.TRUE.equals(run.asList().get(index)))
						++successes;
				result.set(index, Integer.valueOf(successes));
			}
		for (int index = 7; index < result.size(); ++index)
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
				result.set(index, average == Math.rint(average) ? Integer.valueOf((int)average) : Double.valueOf(average));
			}
		}
		result.set(2, Integer.valueOf(runs.size()));
		return result;
	}

	private static boolean averagedResultValid(final List<Object> result, final int runCount)
	{
		if (result == null || result.size() != 27)
			return false;
		for (int index = 3; index < 7; ++index)
		{
			final Object value = result.get(index);
			if (value instanceof Boolean ? runCount != 1 || !((Boolean)value).booleanValue() : !(value instanceof Integer) || ((Integer)value).intValue() != runCount)
				return false;
		}
		for (int index = 7; index < result.size(); ++index)
			if (!metricPositive(result.get(index)))
				return false;
		return true;
	}

	private static String formatWaitingTime(final double waitingTime, final int decimalPlace)
	{
		return String.format(Locale.ROOT, "%." + decimalPlace + "f", waitingTime).replaceFirst("0+$", "").replaceFirst("\\.$", "");
	}

	public SchemePBAC()
	{
		this(new CurveParameter("SS512", 512));
	}

	public SchemePBAC(final CurveParameter curveParameter)
	{
		this(createPairing(curveParameter), curveParameter.securityParameter());
	}

	public SchemePBAC(final Pairing pairing, final int securityParameter)
	{
		if (pairing == null || !pairing.isSymmetric())
			throw new IllegalArgumentException("The scheme requires a symmetric pairing.");
		this.pairing = pairing;
		this.securityParameter = securityParameter >= 1 ? securityParameter : 512;
		this.messageBytes = (this.securityParameter + 7) >>> 3;
		this.operand = BigInteger.ONE.shiftLeft(this.securityParameter).subtract(BigInteger.ONE);
	}

	public SetupResult Setup()
	{
		this.setUp = false;
		final Element g = this.oneG1();
		final Element s = this.randomScalar();
		final Element alpha = this.randomScalar();
		this.masterPublicKey = new MasterPublicKey(g, power(g, s));
		this.masterSecretKey = new MasterSecretKey(s, alpha);
		this.setUp = true;
		return new SetupResult(this.masterPublicKey, this.masterSecretKey);
	}

	public Element SKGen(final byte[] identity)
	{
		if (!this.setUp)
			this.Setup();
		final byte[] actualIdentity = identity == null ? this.randomIdentity() : identity;
		return power(this.hashToG1(actualIdentity), this.masterSecretKey.alpha());
	}

	public ReceiverKey RKGen(final byte[] identity)
	{
		if (!this.setUp)
			this.Setup();
		final byte[] actualIdentity = identity == null ? this.randomIdentity() : identity;
		final Element hash = this.hashToG1(actualIdentity);
		return new ReceiverKey(power(hash, this.masterSecretKey.alpha()), power(hash, this.masterSecretKey.s()));
	}

	public CipherText Enc(final Element encryptionKey, final byte[] receiverIdentity, final Object message)
	{
		if (!this.setUp)
			this.Setup();
		final byte[] identity = receiverIdentity == null ? this.randomIdentity() : receiverIdentity;
		final Element key = encryptionKey == null ? this.SKGen(this.randomIdentity()) : encryptionKey;
		final BigInteger plainText = this.normalizeMessage(message);
		final Element eta1 = this.randomGT();
		final Element eta2 = this.randomGT();
		final Element r = this.hash3(eta1, eta2, plainText);
		final Element c1 = power(this.masterPublicKey.g(), r);
		final Element receiverHash = this.hashToG1(identity);
		final Element c2 = multiply(eta1, this.pair(this.masterPublicKey.gHat(), power(receiverHash, r)));
		final Element c3 = multiply(eta2, this.pair(key, receiverHash));
		final BigInteger c4 = plainText.xor(this.hash4(eta1)).xor(this.hash4(eta2));
		final CipherText unsigned = new CipherText(c1, c2, c3, c4, this.oneG1());
		final Element signature = power(this.hashToG1(this.cipherDigestInput(identity, unsigned)), r);
		return new CipherText(c1, c2, c3, c4, signature);
	}

	public ReEncryptionKey PKGen(final Element encryptionKey2, final ReceiverKey receiverKey2, final byte[] identity1, final byte[] identity2, final byte[] identity3)
	{
		if (!this.setUp)
			this.Setup();
		final byte[] id1 = identity1 == null ? this.randomIdentity() : identity1;
		final byte[] id2 = identity2 == null ? this.randomIdentity() : identity2;
		final byte[] id3 = identity3 == null ? this.randomIdentity() : identity3;
		final Element ek2 = encryptionKey2 == null ? this.SKGen(id2) : encryptionKey2;
		final ReceiverKey dk2 = receiverKey2 == null ? this.RKGen(id2) : receiverKey2;
		final byte[] nonce1 = this.randomIdentity();
		final byte[] nonce2 = this.randomIdentity();
		final Element k1 = this.pair(dk2.second(), this.hashToG1(id3));
		final Element k2 = this.pair(ek2, this.hashToG1(id3));
		final Element component1 = multiply(this.hashToG1(concatenate(k1.toBytes(), id2, id3, nonce1)), dk2.second());
		final Element component2 = multiply(this.hashToG1(concatenate(k2.toBytes(), id2, id3, nonce2)), dk2.first());
		return new ReEncryptionKey(id1, id2, new ReKeyPart(nonce1, component1), new ReKeyPart(nonce2, component2));
	}

	public TransformedCipherText ProxyEnc(final ReEncryptionKey reEncryptionKey, final CipherText cipherText)
	{
		if (!this.setUp || reEncryptionKey == null || cipherText == null)
			return null;
		final Element hash = this.hashToG1(this.cipherDigestInput(reEncryptionKey.identity2(), cipherText));
		if (!this.pair(hash, cipherText.c1()).isEqual(this.pair(this.masterPublicKey.g(), cipherText.signature())))
			return null;
		final Element random = this.randomScalar();
		final Element numerator = this.pair(cipherText.c1(), multiply(reEncryptionKey.first().component(), power(hash, random)));
		final Element denominator = this.pair(power(this.masterPublicKey.g(), random), cipherText.signature());
		final Element c2Prime = divide(cipherText.c2(), divide(numerator, denominator));
		final Element c3Prime = divide(cipherText.c3(), this.pair(this.hashToG1(reEncryptionKey.identity1()), reEncryptionKey.second().component()));
		return new TransformedCipherText(reEncryptionKey.identity1(), cipherText.c1(), c2Prime, c3Prime, cipherText.c4(), reEncryptionKey.first().nonce(), reEncryptionKey.second().nonce());
	}

	public Object Dec1(final ReceiverKey receiverKey2, final byte[] identity2, final byte[] identity1, final CipherText cipherText)
	{
		if (!this.setUp || cipherText == null)
			return Boolean.FALSE;
		final byte[] id2 = identity2 == null ? this.randomIdentity() : identity2;
		final byte[] id1 = identity1 == null ? this.randomIdentity() : identity1;
		final ReceiverKey key = receiverKey2 == null ? this.RKGen(id2) : receiverKey2;
		final Element hash = this.hashToG1(this.cipherDigestInput(id2, cipherText));
		final Element random = this.randomScalar();
		final Element eta1 = divide(cipherText.c2(), divide(this.pair(cipherText.c1(), multiply(key.second(), power(hash, random))), this.pair(power(this.masterPublicKey.g(), random), cipherText.signature())));
		final Element eta2 = divide(cipherText.c3(), this.pair(key.first(), this.hashToG1(id1)));
		final BigInteger message = cipherText.c4().xor(this.hash4(eta1)).xor(this.hash4(eta2));
		final Element r = this.hash3(eta1, eta2, message);
		return cipherText.signature().isEqual(power(hash, r)) && cipherText.c1().isEqual(power(this.masterPublicKey.g(), r)) ? message : Boolean.FALSE;
	}

	public Object Dec2(final ReceiverKey receiverKey3, final byte[] identity3, final byte[] identity2, final TransformedCipherText cipherText)
	{
		if (!this.setUp || cipherText == null)
			return Boolean.FALSE;
		final byte[] id3 = identity3 == null ? this.randomIdentity() : identity3;
		final byte[] id2 = identity2 == null ? this.randomIdentity() : identity2;
		final ReceiverKey key = receiverKey3 == null ? this.RKGen(id3) : receiverKey3;
		final Element k1 = this.pair(key.second(), this.hashToG1(id2));
		final Element k2 = this.pair(key.first(), this.hashToG1(id2));
		final Element eta1 = multiply(cipherText.c2Prime(), this.pair(cipherText.c1(), this.hashToG1(concatenate(k1.toBytes(), id2, id3, cipherText.nonce1()))));
		final Element eta2 = multiply(cipherText.c3Prime(), this.pair(this.hashToG1(concatenate(k2.toBytes(), id2, id3, cipherText.nonce2())), this.hashToG1(cipherText.identity1())));
		final BigInteger message = cipherText.c4().xor(this.hash4(eta1)).xor(this.hash4(eta2));
		final Element r = this.hash3(eta1, eta2, message);
		return cipherText.c1().isEqual(power(this.masterPublicKey.g(), r)) ? message : Boolean.FALSE;
	}

	public static RunResult conductScheme(final CurveParameter curveParameter, final Integer run, final boolean verbose)
	{
		final String curveName = curveParameter == null ? "N/A" : curveParameter.curveName();
		final int securityParameter = curveParameter == null ? 512 : curveParameter.securityParameter();
		final Object runValue = run != null && run.intValue() >= 1 ? run : "N/A";
		if (verbose)
		{
			System.out.println("Curve: (" + curveName + ", " + securityParameter + ")");
			System.out.println("run: " + runValue);
		}
		final SchemePBAC scheme;
		try
		{
			scheme = new SchemePBAC(curveParameter);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, runValue);
		}
		if (verbose)
			System.out.println("Is the system valid? Yes.");
		try
		{
			final int sizeZR = scheme.getLengthOf(scheme.randomScalar());
			final int sizeG1G2 = scheme.getLengthOf(scheme.randomG1());
			final int sizeGT = scheme.getLengthOf(scheme.randomGT());
			long startTime = System.nanoTime();
			final SetupResult setupResult = scheme.Setup();
			final double timeSetup = elapsedSeconds(startTime);
			final int sizeMpk = scheme.getLengthOf(setupResult.masterPublicKey());
			final int sizeMsk = scheme.getLengthOf(setupResult.masterSecretKey());
			final byte[] id1 = scheme.randomIdentity();
			final byte[] id2 = scheme.randomIdentity();
			startTime = System.nanoTime();
			final Element encryptionKey1 = scheme.SKGen(id1);
			final Element encryptionKey2 = scheme.SKGen(id2);
			final double timeSKGen = elapsedSeconds(startTime) / 2.0;
			final byte[] id3 = scheme.randomIdentity();
			startTime = System.nanoTime();
			final ReceiverKey receiverKey2 = scheme.RKGen(id2);
			final ReceiverKey receiverKey3 = scheme.RKGen(id3);
			final double timeRKGen = elapsedSeconds(startTime) / 2.0;
			final BigInteger message = new BigInteger(1, "SchemePBAC".getBytes(StandardCharsets.UTF_8));
			startTime = System.nanoTime();
			final CipherText cipherText = scheme.Enc(encryptionKey1, id2, message);
			final double timeEnc = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final ReEncryptionKey reEncryptionKey = scheme.PKGen(encryptionKey2, receiverKey2, id1, id2, id3);
			final double timePKGen = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final TransformedCipherText transformed = scheme.ProxyEnc(reEncryptionKey, cipherText);
			final double timeProxyEnc = elapsedSeconds(startTime);
			final boolean proxyPassed = transformed != null;
			startTime = System.nanoTime();
			final Object direct = scheme.Dec1(receiverKey2, id2, id1, cipherText);
			final double timeDec1 = elapsedSeconds(startTime);
			final boolean dec1Passed = message.equals(direct);
			startTime = System.nanoTime();
			final Object delegated = scheme.Dec2(receiverKey3, id3, id2, transformed);
			final double timeDec2 = elapsedSeconds(startTime);
			final boolean dec2Passed = message.equals(delegated);
			if (verbose)
			{
				System.out.println("Original: " + message);
				System.out.println("Dec1: " + direct);
				System.out.println("Dec2: " + delegated);
				System.out.println("Is ``ProxyEnc`` passed? " + (proxyPassed ? "Yes" : "No") + ".");
				System.out.println("Is ``Dec1`` passed (m == message)? " + (dec1Passed ? "Yes" : "No") + ".");
				System.out.println("Is ``Dec2`` passed (m' == message)? " + (dec2Passed ? "Yes" : "No") + ".");
				System.out.println("Time: (" + timeSetup + ", " + timeSKGen + ", " + timeRKGen + ", " + timeEnc + ", " + timePKGen + ", " + timeProxyEnc + ", " + timeDec1 + ", " + timeDec2 + ")");
				System.out.println();
			}
			return new RunResult(curveName, securityParameter, runValue, true, proxyPassed, dec1Passed, dec2Passed, timeSetup, timeSKGen, timeRKGen, timeEnc, timePKGen, timeProxyEnc, timeDec1, timeDec2, printableSize(sizeZR), printableSize(sizeG1G2), printableSize(sizeGT), printableSize(sizeMpk), printableSize(sizeMsk), printableSize(scheme.getLengthOf(encryptionKey1)), printableSize(scheme.getLengthOf(encryptionKey2)), printableSize(scheme.getLengthOf(receiverKey2)), printableSize(scheme.getLengthOf(receiverKey3)), printableSize(scheme.getLengthOf(cipherText)), printableSize(scheme.getLengthOf(reEncryptionKey)), printableSize(scheme.getLengthOf(transformed)));
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("The scheme execution failed due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, runValue);
		}
	}

	public record CurveParameter(String curveName, int securityParameter)
	{
	}

	public record MasterPublicKey(Element g, Element gHat)
	{
	}

	public record MasterSecretKey(Element s, Element alpha)
	{
	}

	public record SetupResult(MasterPublicKey masterPublicKey, MasterSecretKey masterSecretKey)
	{
	}

	public record ReceiverKey(Element first, Element second)
	{
	}

	public record CipherText(Element c1, Element c2, Element c3, BigInteger c4, Element signature)
	{
	}

	public record ReKeyPart(byte[] nonce, Element component)
	{
	}

	public record ReEncryptionKey(byte[] identity1, byte[] identity2, ReKeyPart first, ReKeyPart second)
	{
	}

	public record TransformedCipherText(byte[] identity1, Element c1, Element c2Prime, Element c3Prime, BigInteger c4, byte[] nonce1, byte[] nonce2)
	{
	}

	public record RunResult(String curveName, int securityParameter, Object run, boolean systemValid, boolean proxyEncryptionPassed, boolean directDecryptionPassed, boolean delegatedDecryptionPassed, Object setupTime, Object senderKeyGenerationTime, Object receiverKeyGenerationTime, Object encryptionTime, Object proxyKeyGenerationTime, Object proxyEncryptionTime, Object directDecryptionTime, Object delegatedDecryptionTime, Object scalarSize, Object sourceGroupSize, Object targetGroupSize, Object masterPublicKeySize, Object masterSecretKeySize, Object encryptionKey1Size, Object encryptionKey2Size, Object receiverKey2Size, Object receiverKey3Size, Object cipherTextSize, Object reEncryptionKeySize, Object transformedCipherTextSize)
	{
		private static RunResult invalid(final String curveName, final int securityParameter, final Object run)
		{
			return new RunResult(curveName, securityParameter, run, false, false, false, false, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A");
		}

		public List<Object> asList()
		{
			return List.of(this.curveName, Integer.valueOf(this.securityParameter), this.run, Boolean.valueOf(this.systemValid), Boolean.valueOf(this.proxyEncryptionPassed), Boolean.valueOf(this.directDecryptionPassed), Boolean.valueOf(this.delegatedDecryptionPassed), this.setupTime, this.senderKeyGenerationTime, this.receiverKeyGenerationTime, this.encryptionTime, this.proxyKeyGenerationTime, this.proxyEncryptionTime, this.directDecryptionTime, this.delegatedDecryptionTime, this.scalarSize, this.sourceGroupSize, this.targetGroupSize, this.masterPublicKeySize, this.masterSecretKeySize, this.encryptionKey1Size, this.encryptionKey2Size, this.receiverKey2Size, this.receiverKey3Size, this.cipherTextSize, this.reEncryptionKeySize, this.transformedCipherTextSize);
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
			final List<CurveParameter> curves = List.of(new CurveParameter("SS512", 128), new CurveParameter("SS512", 160), new CurveParameter("SS512", 224), new CurveParameter("SS512", 256), new CurveParameter("SS512", 384), new CurveParameter("SS512", 512));
			final List<String> columns = List.of("curveParameter", "secparam", "runCount", "isSystemValid", "isProxyEncPassed", "isDec1Passed", "isDec2Passed", "Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "PKGen (s)", "ProxyEnc (s)", "Dec1 (s)", "Dec2 (s)", "elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", "mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "C (B)", "rk (B)", "CT (B)");
			final Saver saver = new Saver(options.outputFilePath(), columns, options.decimalPlace(), options.encoding());
			final List<List<Object>> results = new ArrayList<>();
			try
			{
				for (final CurveParameter curve : curves)
				{
					final List<RunResult> runs = new ArrayList<>();
					for (int run = 1; run <= options.runCount(); ++run)
						runs.add(conductScheme(curve, Integer.valueOf(run), options.verbose()));
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