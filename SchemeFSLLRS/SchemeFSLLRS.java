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
	private static final String SCHEME_NAME = "SchemeFSLLRS";
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
		System.out.println("This is the official implementation of the FS-LLRS cryptographic scheme in Java programming language.");
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


final class FSLLRSMatrix
{
	private FSLLRSMatrix() {}

	private static void requireRectangular(final long[][] matrix)
	{
		if (matrix == null || matrix.length == 0 || matrix[0] == null || matrix[0].length == 0)
			throw new IllegalArgumentException("The matrix is empty.");
		final int columns = matrix[0].length;
		for (final long[] row : matrix)
			if (row == null || row.length != columns)
				throw new IllegalArgumentException("The matrix is not rectangular.");
	}

	private static void requireSameShape(final long[][] left, final long[][] right)
	{
		requireRectangular(left);
		requireRectangular(right);
		if (left.length != right.length || left[0].length != right[0].length)
			throw new IllegalArgumentException("The matrix dimensions do not match.");
	}

	private static long modularInverse(final long value, final int modulus)
	{
		return BigInteger.valueOf(mod(value, modulus)).modInverse(BigInteger.valueOf(modulus)).longValueExact();
	}

	private static void updateDigest(final MessageDigest digest, final Object value)
	{
		if (value == null)
		{
			digest.update((byte)0);
			return;
		}
		if (value.getClass().isArray())
		{
			final int length = java.lang.reflect.Array.getLength(value);
			for (int index = 0; index < length; ++index)
				updateDigest(digest, java.lang.reflect.Array.get(value, index));
			return;
		}
		final long number = value instanceof Number ? ((Number)value).longValue() : value.hashCode();
		for (int shift = 56; shift >= 0; shift -= 8)
			digest.update((byte)(number >>> shift));
	}

	static byte[] digest(final Object... values)
	{
		try
		{
			final MessageDigest digest = MessageDigest.getInstance("SHA3-256");
			for (final Object value : values)
				updateDigest(digest, value);
			return digest.digest();
		}
		catch (final NoSuchAlgorithmException exception)
		{
			throw new IllegalStateException("SHA3-256 is unavailable.", exception);
		}
	}

	static int bit(final byte[] bytes, final int index)
	{
		return index < bytes.length << 3 ? (bytes[index >> 3] >>> (7 - (index & 7))) & 1 : 0;
	}

	static long mod(final long value, final int modulus)
	{
		return Math.floorMod(value, modulus);
	}

	static long[][] identity(final int size)
	{
		if (size < 1)
			throw new IllegalArgumentException("The identity size must be positive.");
		final long[][] result = new long[size][size];
		for (int index = 0; index < size; ++index)
			result[index][index] = 1;
		return result;
	}

	static long[][] random(final int rows, final int columns, final int bound, final SecureRandom random)
	{
		if (rows < 1 || columns < 1 || bound < 1 || random == null)
			throw new IllegalArgumentException("The random matrix parameters are invalid.");
		final long[][] result = new long[rows][columns];
		for (int row = 0; row < rows; ++row)
			for (int column = 0; column < columns; ++column)
				result[row][column] = random.nextInt(bound);
		return result;
	}

	static long[][] randomSigned(final int rows, final int columns, final SecureRandom random)
	{
		final long[][] result = random(rows, columns, 2, random);
		for (int row = 0; row < rows; ++row)
			for (int column = 0; column < columns; ++column)
				result[row][column] = (result[row][column] << 1) - 1;
		return result;
	}

	static long[][] transpose(final long[][] matrix)
	{
		requireRectangular(matrix);
		final long[][] result = new long[matrix[0].length][matrix.length];
		for (int row = 0; row < matrix.length; ++row)
			for (int column = 0; column < matrix[row].length; ++column)
				result[column][row] = matrix[row][column];
		return result;
	}

	static long[][] add(final long[][] left, final long[][] right, final int modulus)
	{
		requireSameShape(left, right);
		final long[][] result = new long[left.length][left[0].length];
		for (int row = 0; row < left.length; ++row)
			for (int column = 0; column < left[row].length; ++column)
				result[row][column] = mod(left[row][column] + right[row][column], modulus);
		return result;
	}

	static long[][] subtract(final long[][] left, final long[][] right, final int modulus)
	{
		requireSameShape(left, right);
		final long[][] result = new long[left.length][left[0].length];
		for (int row = 0; row < left.length; ++row)
			for (int column = 0; column < left[row].length; ++column)
				result[row][column] = mod(left[row][column] - right[row][column], modulus);
		return result;
	}

	static long[][] scale(final long[][] matrix, final long scalar, final int modulus)
	{
		requireRectangular(matrix);
		final long[][] result = new long[matrix.length][matrix[0].length];
		for (int row = 0; row < matrix.length; ++row)
			for (int column = 0; column < matrix[row].length; ++column)
				result[row][column] = mod(matrix[row][column] * scalar, modulus);
		return result;
	}

	static long[][] addScalar(final long[][] matrix, final long scalar, final int modulus)
	{
		requireRectangular(matrix);
		final long[][] result = new long[matrix.length][matrix[0].length];
		for (int row = 0; row < matrix.length; ++row)
			for (int column = 0; column < matrix[row].length; ++column)
				result[row][column] = mod(matrix[row][column] + scalar, modulus);
		return result;
	}

	static long[][] multiply(final long[][] left, final long[][] right, final int modulus)
	{
		requireRectangular(left);
		requireRectangular(right);
		if (left[0].length != right.length)
			throw new IllegalArgumentException("The matrix dimensions cannot be multiplied.");
		final long[][] result = new long[left.length][right[0].length];
		for (int row = 0; row < left.length; ++row)
			for (int common = 0; common < right.length; ++common)
				for (int column = 0; column < right[common].length; ++column)
					result[row][column] = mod(result[row][column] + left[row][common] * right[common][column], modulus);
		return result;
	}

	static long[][] horizontal(final long[][]... matrices)
	{
		if (matrices == null || matrices.length == 0)
			throw new IllegalArgumentException("No matrices were supplied.");
		int columns = 0;
		final int rows = matrices[0].length;
		for (final long[][] matrix : matrices)
		{
			requireRectangular(matrix);
			if (matrix.length != rows)
				throw new IllegalArgumentException("The matrices have different row counts.");
			columns += matrix[0].length;
		}
		final long[][] result = new long[rows][columns];
		int offset = 0;
		for (final long[][] matrix : matrices)
		{
			for (int row = 0; row < rows; ++row)
				System.arraycopy(matrix[row], 0, result[row], offset, matrix[row].length);
			offset += matrix[0].length;
		}
		return result;
	}

	static long[][] vertical(final long[][]... matrices)
	{
		if (matrices == null || matrices.length == 0)
			throw new IllegalArgumentException("No matrices were supplied.");
		int rows = 0;
		final int columns = matrices[0][0].length;
		for (final long[][] matrix : matrices)
		{
			requireRectangular(matrix);
			if (matrix[0].length != columns)
				throw new IllegalArgumentException("The matrices have different column counts.");
			rows += matrix.length;
		}
		final long[][] result = new long[rows][columns];
		int offset = 0;
		for (final long[][] matrix : matrices)
		{
			for (int row = 0; row < matrix.length; ++row)
				result[offset + row] = matrix[row].clone();
			offset += matrix.length;
		}
		return result;
	}

	static long[][] kronecker(final long[][] left, final long[][] right, final int modulus)
	{
		requireRectangular(left);
		requireRectangular(right);
		final long[][] result = new long[left.length * right.length][left[0].length * right[0].length];
		for (int leftRow = 0; leftRow < left.length; ++leftRow)
			for (int leftColumn = 0; leftColumn < left[leftRow].length; ++leftColumn)
				for (int rightRow = 0; rightRow < right.length; ++rightRow)
					for (int rightColumn = 0; rightColumn < right[rightRow].length; ++rightColumn)
						result[leftRow * right.length + rightRow][leftColumn * right[0].length + rightColumn] =
							mod(left[leftRow][leftColumn] * right[rightRow][rightColumn], modulus);
		return result;
	}

	static long[][] inverseMod(final long[][] matrix, final int modulus)
	{
		requireRectangular(matrix);
		if (matrix.length != matrix[0].length)
			throw new IllegalArgumentException("The matrix must be square.");
		final int size = matrix.length;
		final long[][] augmented = new long[size][size << 1];
		for (int row = 0; row < size; ++row)
		{
			for (int column = 0; column < size; ++column)
				augmented[row][column] = mod(matrix[row][column], modulus);
			augmented[row][size + row] = 1;
		}
		for (int column = 0; column < size; ++column)
		{
			int pivot = column;
			while (pivot < size && BigInteger.valueOf(augmented[pivot][column]).gcd(BigInteger.valueOf(modulus)).longValue() != 1L)
				++pivot;
			if (pivot == size)
				throw new ArithmeticException("The matrix is not invertible modulo q.");
			final long[] temporary = augmented[column];
			augmented[column] = augmented[pivot];
			augmented[pivot] = temporary;
			final long inverse = modularInverse(augmented[column][column], modulus);
			for (int index = 0; index < size << 1; ++index)
				augmented[column][index] = mod(augmented[column][index] * inverse, modulus);
			for (int row = 0; row < size; ++row)
				if (row != column)
				{
					final long factor = augmented[row][column];
					for (int index = 0; index < size << 1; ++index)
						augmented[row][index] = mod(augmented[row][index] - factor * augmented[column][index], modulus);
				}
		}
		final long[][] result = new long[size][size];
		for (int row = 0; row < size; ++row)
			System.arraycopy(augmented[row], size, result[row], 0, size);
		return result;
	}
}

public final class SchemeFSLLRS
{
	private static final int DEFAULT_RING_SIZE = 2;
	private static final int DEFAULT_DIMENSION = 4;
	private static final int DEFAULT_MODULUS = 251;
	private static final int EXIT_SUCCESS = 0;
	private static final int EXIT_FAILURE = 1;
	private static final int EOF = -1;
	private static final SecureRandom RANDOM = new SecureRandom();
	private int ringSize = 0;
	private int dimension = 0;
	private int modulus = 0;
	private long[][] ringMatrix = null;
	private long[][] secretKeys = null;
	private long[][] publicKeys = null;
	private Integer signer = null;
	private long epoch = 0;
	private byte[] message = null;
	private Object[] ringSignature = null;
	private Object[] linkedSignature = null;

	private static double elapsedSeconds(final long startTime)
	{
		return Math.max(Double.MIN_VALUE, (System.nanoTime() - startTime) / 1_000_000_000.0);
	}

	private static int lengthOf(final Object value)
	{
		if (value == null)
			return 0;
		if (value instanceof Number)
			return Math.max(1, (BigInteger.valueOf(Math.abs(((Number)value).longValue())).bitLength() + 7) >> 3);
		if (value instanceof Boolean)
			return 1;
		if (value instanceof CharSequence)
			return value.toString().getBytes(StandardCharsets.UTF_8).length;
		if (value.getClass().isArray())
		{
			int total = 0;
			final int length = java.lang.reflect.Array.getLength(value);
			for (int index = 0; index < length; ++index)
				total = Math.addExact(total, lengthOf(java.lang.reflect.Array.get(value, index)));
			return total;
		}
		if (value instanceof Collection<?> collection)
		{
			int total = 0;
			for (final Object element : collection)
				total = Math.addExact(total, lengthOf(element));
			return total;
		}
		return value.toString().getBytes(StandardCharsets.UTF_8).length;
	}

	private static List<Object> averageRuns(final List<RunResult> runs)
	{
		final RunResult first = runs.get(0);
		final List<Object> result = new ArrayList<>(List.of(
			Integer.valueOf(first.ringSize()), Integer.valueOf(first.dimension()), Integer.valueOf(first.modulus()),
			Integer.valueOf(runs.size()), Integer.valueOf((int)runs.stream().filter(RunResult::systemValid).count()),
			Integer.valueOf((int)runs.stream().filter(RunResult::schemeCorrect).count())));
		for (int metric = 0; metric < first.metrics().size(); ++metric)
		{
			double total = 0.0;
			boolean valid = true;
			for (final RunResult run : runs)
			{
				final Object value = run.metrics().get(metric);
				if (!(value instanceof Number) || ((Number)value).doubleValue() <= 0.0)
				{
					valid = false;
					break;
				}
				total += ((Number)value).doubleValue();
			}
			if (!valid)
				result.add("N/A");
			else
			{
				final double average = total / runs.size();
				result.add(average == Math.rint(average) ? Long.valueOf((long)average) : Double.valueOf(average));
			}
		}
		return result;
	}

	private static boolean resultValid(final List<Object> result, final int runCount)
	{
		if (result.size() < 18 || !Integer.valueOf(runCount).equals(result.get(3))
			|| !Integer.valueOf(runCount).equals(result.get(4)) || !Integer.valueOf(runCount).equals(result.get(5)))
			return false;
		for (int index = 6; index < result.size(); ++index)
			if (!(result.get(index) instanceof Number) || ((Number)result.get(index)).doubleValue() <= 0.0)
				return false;
		return true;
	}

	private static long[][] randomNonZero(final int rows, final int columns, final int bound)
	{
		final long[][] result = new long[rows][columns];
		for (int row = 0; row < rows; ++row)
			for (int column = 0; column < columns; ++column)
				result[row][column] = 1 + RANDOM.nextInt(bound - 1);
		return result;
	}

	private static long[] randomVector(final int length, final int bound)
	{
		final long[] result = new long[length];
		for (int index = 0; index < length; ++index)
			result[index] = RANDOM.nextInt(bound);
		return result;
	}

	private static long[][] column(final long[] vector)
	{
		final long[][] result = new long[vector.length][1];
		for (int index = 0; index < vector.length; ++index)
			result[index][0] = vector[index];
		return result;
	}

	private static void copyColumnToRow(final long[][] destination, final int rowIndex, final long[][] source)
	{
		for (int index = 0; index < source.length; ++index)
			destination[rowIndex][index] = source[index][0];
	}

	private static byte[] encode(final Object value)
	{
		if (value instanceof byte[] bytes)
			return bytes.clone();
		if (value instanceof long[] vector)
		{
			final byte[] result = new byte[vector.length << 3];
			for (int index = 0; index < vector.length; ++index)
				for (int byteIndex = 0; byteIndex < 8; ++byteIndex)
					result[(index << 3) + byteIndex] = (byte)(vector[index] >>> (56 - (byteIndex << 3)));
			return result;
		}
		if (value instanceof long[][] matrix)
		{
			int offset = 0;
			final byte[] result = new byte[matrix.length * matrix[0].length * 8];
			for (final long[] row : matrix)
				for (final long element : row)
					for (int byteIndex = 0; byteIndex < 8; ++byteIndex)
						result[offset++] = (byte)(element >>> (56 - (byteIndex << 3)));
			return result;
		}
		return String.valueOf(value).getBytes(StandardCharsets.UTF_8);
	}

	private long hashScalar(final Object... values)
	{
		try
		{
			final MessageDigest digest = MessageDigest.getInstance("SHA3-256");
			for (final Object value : values)
			{
				final byte[] encoded = encode(value);
				final long length = encoded.length;
				for (int shift = 56; shift >= 0; shift -= 8)
					digest.update((byte)(length >>> shift));
				digest.update(encoded);
			}
			return new BigInteger(1, digest.digest()).mod(BigInteger.valueOf(this.modulus)).longValueExact();
		}
		catch (final NoSuchAlgorithmException exception)
		{
			throw new IllegalStateException("SHA3-256 is unavailable.", exception);
		}
	}

	private byte[] keyTag(final long[] key)
	{
		return FSLLRSMatrix.digest((Object)key);
	}

	private void requireSetup()
	{
		if (this.ringSize < 1 || this.dimension < 1 || this.modulus < 2 || this.ringMatrix == null)
			throw new IllegalStateException("The scheme has not been set up.");
	}

	public Object[] LLRSSetup(final int inputRingSize, final int inputDimension, final int inputModulus)
	{
		if (inputRingSize <= 1 || inputDimension <= 1 || inputModulus <= 1)
			throw new IllegalArgumentException("The ring size, dimension, and modulus must be integers greater than one.");
		if ((inputRingSize & (inputRingSize - 1)) != 0)
			throw new IllegalArgumentException("The ring size must be a power of two.");
		this.ringSize = inputRingSize;
		this.dimension = inputDimension;
		this.modulus = inputModulus;
		final long[] diagonal = randomVector(this.dimension, this.modulus - 1);
		this.ringMatrix = FSLLRSMatrix.identity(this.dimension);
		for (int index = 0; index < this.dimension; ++index)
			this.ringMatrix[index][index] = diagonal[index] + 1;
		this.secretKeys = null;
		this.publicKeys = null;
		this.signer = null;
		this.epoch = 0;
		this.message = null;
		this.ringSignature = null;
		this.linkedSignature = null;
		return new Object[] { this.ringMatrix, Integer.valueOf(this.ringSize), Integer.valueOf(this.dimension), Integer.valueOf(this.modulus) };
	}

	public Object[] KeyExtract()
	{
		this.requireSetup();
		this.secretKeys = randomNonZero(this.ringSize, this.dimension, this.modulus);
		this.publicKeys = FSLLRSMatrix.multiply(
			this.secretKeys, FSLLRSMatrix.transpose(this.ringMatrix), this.modulus);
		return new Object[] { this.publicKeys, this.secretKeys };
	}

	public Object[] KeyUpdate()
	{
		this.requireSetup();
		if (this.secretKeys == null || this.publicKeys == null)
			throw new IllegalStateException("The ring keys have not been extracted.");
		this.signer = Integer.valueOf(RANDOM.nextInt(this.ringSize));
		++this.epoch;
		final long[] updatedSecret = new long[this.dimension];
		for (int index = 0; index < this.dimension; ++index)
		{
			final long value = this.hashScalar(this.secretKeys[this.signer.intValue()], Long.valueOf(this.epoch), Integer.valueOf(index));
			updatedSecret[index] = value == 0 ? 1 : value;
		}
		this.secretKeys[this.signer.intValue()] = updatedSecret;
		copyColumnToRow(
			this.publicKeys, this.signer.intValue(),
			FSLLRSMatrix.multiply(this.ringMatrix, column(updatedSecret), this.modulus));
		return new Object[] { this.signer, Long.valueOf(this.epoch), updatedSecret };
	}

	public Object[] Sign()
	{
		this.requireSetup();
		if (this.secretKeys == null || this.publicKeys == null || this.signer == null)
			throw new IllegalStateException("The signer key has not been updated.");
		this.message = new byte[32];
		RANDOM.nextBytes(this.message);
		final long[] challenges = randomVector(this.ringSize, this.modulus);
		final long[][] responses = FSLLRSMatrix.random(this.ringSize, this.dimension, this.modulus, RANDOM);
		final long[][] commitments = new long[this.ringSize][this.dimension];
		final long[] witness = randomVector(this.dimension, this.modulus);
		final int signerIndex = this.signer.intValue();
		for (int index = 0; index < this.ringSize; ++index)
		{
			if (index == signerIndex)
				copyColumnToRow(
					commitments, index, FSLLRSMatrix.multiply(this.ringMatrix, column(witness), this.modulus));
			else
				copyColumnToRow(
					commitments, index, FSLLRSMatrix.subtract(
						FSLLRSMatrix.multiply(this.ringMatrix, column(responses[index]), this.modulus),
						FSLLRSMatrix.scale(column(this.publicKeys[index]), challenges[index], this.modulus),
						this.modulus));
		}
		final long challenge = this.hashScalar(this.message, this.publicKeys, commitments);
		long challengeSum = 0;
		for (final long value : challenges)
			challengeSum = FSLLRSMatrix.mod(challengeSum + value, this.modulus);
		challenges[signerIndex] = FSLLRSMatrix.mod(
			challenge - challengeSum + challenges[signerIndex], this.modulus);
		for (int index = 0; index < this.dimension; ++index)
			responses[signerIndex][index] = FSLLRSMatrix.mod(
				witness[index] + challenges[signerIndex] * this.secretKeys[signerIndex][index], this.modulus);
		final byte[] tag = this.keyTag(this.secretKeys[signerIndex]);
		this.ringSignature = new Object[] { challenges, responses, tag };
		return this.ringSignature;
	}

	private boolean verify(final Object[] signature, final byte[] verifiedMessage)
	{
		if (signature == null || signature.length != 3 || verifiedMessage == null
			|| this.publicKeys == null || this.ringMatrix == null)
			return false;
		if (!(signature[0] instanceof long[] challenges) || challenges.length != this.ringSize)
			return false;
		if (!(signature[1] instanceof long[][] responses) || responses.length != this.ringSize)
			return false;
		if (!(signature[2] instanceof byte[]))
			return false;
		for (final long[] response : responses)
			if (response == null || response.length != this.dimension)
				return false;
		final long[][] commitments = new long[this.ringSize][this.dimension];
		long challengeSum = 0;
		for (int index = 0; index < this.ringSize; ++index)
		{
			copyColumnToRow(
				commitments, index, FSLLRSMatrix.subtract(
					FSLLRSMatrix.multiply(this.ringMatrix, column(responses[index]), this.modulus),
					FSLLRSMatrix.scale(column(this.publicKeys[index]), challenges[index], this.modulus),
					this.modulus));
			challengeSum = FSLLRSMatrix.mod(challengeSum + challenges[index], this.modulus);
		}
		return challengeSum == this.hashScalar(verifiedMessage, this.publicKeys, commitments);
	}

	public boolean Verify()
	{
		return this.verify(this.ringSignature, this.message);
	}

	public boolean Link()
	{
		if (this.ringSignature == null)
			return false;
		final byte[] firstTag = (byte[])this.ringSignature[2];
		final Object[] secondSignature = this.Sign();
		this.linkedSignature = secondSignature;
		return Arrays.equals(firstTag, (byte[])secondSignature[2]) && this.verify(secondSignature, this.message);
	}

	public static RunResult conductScheme(final Parameters parameters, final Integer run, final boolean verbose)
	{
		boolean systemValid = false;
		boolean schemeCorrect = false;
		final List<Object> metrics = new ArrayList<>(Collections.nCopies(12, "N/A"));
		if (verbose)
		{
			System.out.println("Parameters: " + parameters);
			System.out.println("run: " + (run == null ? "N/A" : run));
		}
		try
		{
			final SchemeFSLLRS scheme = new SchemeFSLLRS();
			long start = System.nanoTime();
			final Object[] publicParameters = scheme.LLRSSetup(
				parameters.ringSize(), parameters.dimension(), parameters.modulus());
			metrics.set(0, Double.valueOf(elapsedSeconds(start)));
			systemValid = true;
			start = System.nanoTime();
			final Object[] keys = scheme.KeyExtract();
			metrics.set(1, Double.valueOf(elapsedSeconds(start)));
			start = System.nanoTime();
			final Object[] updatedKey = scheme.KeyUpdate();
			metrics.set(2, Double.valueOf(elapsedSeconds(start)));
			start = System.nanoTime();
			final Object[] signature = scheme.Sign();
			metrics.set(3, Double.valueOf(elapsedSeconds(start)));
			start = System.nanoTime();
			final boolean verified = scheme.Verify();
			metrics.set(4, Double.valueOf(elapsedSeconds(start)));
			start = System.nanoTime();
			final boolean linked = scheme.Link();
			metrics.set(5, Double.valueOf(elapsedSeconds(start)));
			schemeCorrect = verified && linked;
			metrics.set(6, Integer.valueOf(lengthOf(publicParameters)));
			metrics.set(7, Integer.valueOf(lengthOf(keys[1])));
			metrics.set(8, Integer.valueOf(lengthOf(keys[0])));
			metrics.set(9, Integer.valueOf(lengthOf(updatedKey)));
			metrics.set(10, Integer.valueOf(lengthOf(signature)));
			metrics.set(11, Integer.valueOf(lengthOf(scheme.linkedSignature)));
			if (verbose)
			{
				System.out.println("Is the system valid? Yes.");
				System.out.println("Is the scheme correct? " + (schemeCorrect ? "Yes." : "No."));
				System.out.println("Time: " + metrics.subList(0, 6));
				System.out.println("Space: " + metrics.subList(6, metrics.size()));
				System.out.println();
			}
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
			{
				System.out.println("Is the system valid? No. The execution failed due to " + exception + '.');
				System.out.println();
			}
		}
		return new RunResult(
			parameters.ringSize(), parameters.dimension(), parameters.modulus(),
			run, systemValid, schemeCorrect, metrics);
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
			final List<Parameters> parameterSets = List.of(
				new Parameters(DEFAULT_RING_SIZE, DEFAULT_DIMENSION, DEFAULT_MODULUS),
				new Parameters(4, 4, DEFAULT_MODULUS));
			final List<String> columns = List.of(
				"N", "n", "q", "runCount", "isSystemValid", "isSchemeCorrect",
				"Setup (s)", "KeyExtract (s)", "KeyUpdate (s)", "Sign (s)", "Verify (s)", "Link (s)",
				"publicParameters (B)", "secretKeys (B)", "publicKeys (B)", "updatedKey (B)",
				"signature (B)", "linkedSignature (B)");
			final Saver saver = new Saver(options.outputFilePath(), columns, options.decimalPlace(), options.encoding());
			final List<List<Object>> results = new ArrayList<>();
			for (final Parameters parameters : parameterSets)
			{
				final List<RunResult> runs = new ArrayList<>();
				for (int run = 1; run <= options.runCount(); ++run)
					runs.add(conductScheme(parameters, Integer.valueOf(run), options.verbose()));
				final List<Object> result = averageRuns(runs);
				results.add(result);
				saver.save(results);
			}
			final int expectedRunCount = options.runCount();
			errorLevel = !results.isEmpty() && results.stream().allMatch(result -> resultValid(result, expectedRunCount))
				? EXIT_SUCCESS : EXIT_FAILURE;
		}
		else if (options.flag() == EXIT_SUCCESS)
			errorLevel = EXIT_SUCCESS;
		if (options.waitingTime() == 0.0)
			System.out.println("The execution has finished (" + errorLevel + ").");
		else if (Double.isFinite(options.waitingTime()) && options.waitingTime() > 0.0)
		{
			try
			{
				Thread.sleep(Math.max(0L, Math.round(options.waitingTime() * 1_000.0)));
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
			try (Scanner scanner = new Scanner(System.in, StandardCharsets.UTF_8))
			{
				if (scanner.hasNextLine())
					scanner.nextLine();
			}
		}
		System.exit(errorLevel);
	}

	public record Parameters(int ringSize, int dimension, int modulus) {}

	public record RunResult(
		int ringSize,
		int dimension,
		int modulus,
		Integer run,
		boolean systemValid,
		boolean schemeCorrect,
		List<Object> metrics
	) {}
}

