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
import it.unisa.dia.gas.plaf.jpbc.pairing.f.TypeFCurveGenerator;
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
	private static final String SCHEME_NAME = "SchemeCANIPSI";
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
		System.out.println("This is a possible implementation of the CA-NI-PSI cryptographic scheme in Java based on JPBC.");
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

public final class SchemeCANIPSI
{
	private static final int DEFAULT_N = 30;
	private static final int DEFAULT_M = 10;
	private static final int EXIT_SUCCESS = 0;
	private static final int EXIT_FAILURE = 1;
	private static final int EOF = -1;
	private static final SecureRandom RANDOM = new SecureRandom();
	private static final Map<String, Pairing> PAIRINGS = new LinkedHashMap<>();
	private final Pairing pairing;
	private final int securityParameter;
	private int n = DEFAULT_N;
	private int m = DEFAULT_M;
	private BasicPublicKey basicPublicKey = null;
	private BasicSecretKey basicSecretKey = null;
	private boolean basicSetUp = false;
	private MasterPublicKey masterPublicKey = null;
	private MasterSecretKey masterSecretKey = null;
	private boolean setUp = false;

	private static Pairing createPairing(final CurveParameter curveParameter)
	{
		if (curveParameter == null)
			throw new IllegalArgumentException("The curve parameter is missing.");
		final String curveName = curveParameter.curveName();
		final String cacheKey = curveName.toUpperCase(Locale.ROOT) + ':' + curveParameter.securityParameter();
		synchronized (PAIRINGS)
		{
			final Pairing cached = PAIRINGS.get(cacheKey);
			if (cached != null)
				return cached;
			final PairingParameters parameters;
			if ("BN254".equalsIgnoreCase(curveName))
				parameters = new TypeFCurveGenerator(RANDOM, 254).generate();
			else if ("SS512".equalsIgnoreCase(curveName))
				parameters = new TypeACurveGenerator(RANDOM, 160, 512, false).generate();
			else if ("SS1024".equalsIgnoreCase(curveName))
				parameters = new TypeACurveGenerator(RANDOM, 160, 1024, false).generate();
			else if ("MNT201".equalsIgnoreCase(curveName) || "MNT224".equalsIgnoreCase(curveName))
				throw new IllegalArgumentException("The JPBC distribution does not provide the requested MNT parameters.");
			else
				throw new IllegalArgumentException("Unsupported curve: " + curveName + '.');
			PairingFactory.getInstance().setUsePBCWhenPossible(false);
			final Pairing created = PairingFactory.getPairing(parameters, RANDOM);
			PAIRINGS.put(cacheKey, created);
			return created;
		}
	}

	private static double elapsedSeconds(final long startTime)
	{
		return Math.max(Double.MIN_VALUE, (System.nanoTime() - startTime) / 1_000_000_000.0);
	}

	private static Element multiply(final Element left, final Element right)
	{
		return left.duplicate().mul(right).getImmutable();
	}

	private static Element divide(final Element left, final Element right)
	{
		return left.duplicate().div(right).getImmutable();
	}

	private static Element add(final Element left, final Element right)
	{
		return left.duplicate().add(right).getImmutable();
	}

	private static Element subtract(final Element left, final Element right)
	{
		return left.duplicate().sub(right).getImmutable();
	}

	private static Element scalarProduct(final Element left, final Element right)
	{
		return left.duplicate().mul(right).getImmutable();
	}

	private static Element power(final Element base, final Element exponent)
	{
		return base.duplicate().powZn(exponent).getImmutable();
	}

	private static Element negate(final Element scalar)
	{
		return scalar.duplicate().negate().getImmutable();
	}

	private static byte[] concatenate(final byte[]... vectors)
	{
		final ByteArrayOutputStream output = new ByteArrayOutputStream();
		for (final byte[] vector : vectors)
			if (vector != null)
				output.writeBytes(vector);
		return output.toByteArray();
	}

	private static Object printableSize(final int size)
	{
		return size < 0 ? "N/A" : Integer.valueOf(size);
	}

	private static boolean positiveMetric(final Object metric)
	{
		return metric instanceof Number && ((Number)metric).doubleValue() > 0.0;
	}

	private Element immutable(final Element element)
	{
		return element.getImmutable();
	}

	private Element randomScalar()
	{
		return this.immutable(this.pairing.getZr().newRandomElement());
	}

	private Element generateRandomNonZeroZRElement()
	{
		Element element = this.randomScalar();
		while (element.isZero())
			element = this.randomScalar();
		return element;
	}

	private Element randomG1()
	{
		return this.immutable(this.pairing.getG1().newRandomElement());
	}

	private Element randomG2()
	{
		return this.immutable(this.pairing.getG2().newRandomElement());
	}

	private Element randomGT()
	{
		return this.immutable(this.pairing.getGT().newRandomElement());
	}

	private Element pair(final Element source, final Element target)
	{
		return this.immutable(this.pairing.pairing(source, target));
	}

	private Element hashToG1(final byte[] bytes)
	{
		return this.immutable(this.pairing.getG1().newElementFromHash(bytes, 0, bytes.length));
	}

	private Element hashToScalar(final byte[] bytes)
	{
		return this.immutable(this.pairing.getZr().newElementFromHash(bytes, 0, bytes.length));
	}

	private Element hashToScalar(final Element element)
	{
		return this.hashToScalar(element.toBytes());
	}

	private Element[] computeCoefficients(final List<Element> roots)
	{
		if (roots == null || roots.isEmpty())
			return new Element[] { this.pairing.getZr().newOneElement().getImmutable() };
		Element[] coefficients = new Element[] { this.pairing.getZr().newOneElement().getImmutable() };
		for (final Element root : roots)
		{
			final Element[] next = new Element[coefficients.length + 1];
			for (int index = 0; index < next.length; ++index)
				next[index] = this.pairing.getZr().newZeroElement().getImmutable();
			for (int index = 0; index < coefficients.length; ++index)
			{
				next[index] = add(next[index], scalarProduct(negate(root), coefficients[index]));
				next[index + 1] = add(next[index + 1], coefficients[index]);
			}
			coefficients = next;
		}
		return coefficients;
	}

	private Element computePolynomial(final Element value, final Element[] coefficients)
	{
		if (value == null || coefficients == null || coefficients.length == 0)
			return null;
		Element result = coefficients[coefficients.length - 1];
		for (int index = coefficients.length - 2; index >= 0; --index)
			result = add(scalarProduct(result, value), coefficients[index]);
		return result;
	}

	private Element pairingProduct(final Element firstLeft, final Element firstRight, final Element[] left, final Element[] right)
	{
		Element result = this.pair(firstLeft, firstRight);
		for (int index = 0; index < left.length; ++index)
			result = multiply(result, this.pair(left[index], right[index]));
		return result;
	}

	private List<Element> membershipValues(final Element omega, final List<Element> secrets)
	{
		final List<Element> values = new ArrayList<>();
		for (final Element secret : secrets)
			values.add(this.hashToScalar(power(omega, secret)));
		return values;
	}

	private List<Element> normalizeSecrets(final List<Element> secrets)
	{
		if (secrets != null && secrets.size() == this.n && secrets.stream().allMatch(this::validScalar))
			return List.copyOf(secrets);
		return this.randomSecrets(this.n);
	}

	private Element normalizeSelectedSecret(final List<Element> secrets, final Element selected)
	{
		if (selected != null)
			for (final Element value : secrets)
				if (value.isEqual(selected))
					return value;
		return secrets.get(RANDOM.nextInt(secrets.size()));
	}

	private byte[] normalizeKeyword(final byte[] keyword)
	{
		if (keyword != null)
			return Arrays.copyOf(keyword, keyword.length);
		final byte[] generated = new byte[(this.securityParameter + 7) >>> 3];
		RANDOM.nextBytes(generated);
		return generated;
	}

	private boolean validScalar(final Element element)
	{
		return element != null && element.getField() == this.pairing.getZr();
	}

	private boolean validG1(final Element element)
	{
		return element != null && element.getField() == this.pairing.getG1();
	}

	private boolean validG2(final Element element)
	{
		return element != null && element.getField() == this.pairing.getG2();
	}

	private int getLengthOf(final Object object)
	{
		if (object == null)
			return -1;
		if (object instanceof Element)
			return ((Element)object).toBytes().length;
		if (object instanceof byte[])
			return ((byte[])object).length;
		if (object instanceof String)
			return ((String)object).getBytes(StandardCharsets.UTF_8).length;
		if (object instanceof Collection<?>)
			return this.sumLengths((Collection<?>)object);
		if (object instanceof Element[])
			return this.sumLengths(Arrays.asList((Element[])object));
		if (object instanceof BasicPublicKey value)
			return this.sumLengths(List.of(value.g(), value.g1(), value.omega(), value.v1(), value.v2(), value.v3(), value.v4()));
		if (object instanceof BasicSecretKey value)
			return this.sumLengths(List.of(value.omega(), value.t1(), value.t2(), value.t3(), value.t4()));
		if (object instanceof MasterPublicKey value)
			return this.sumLengths(List.of(value.g1(), value.g2(), value.g3(), value.r(), value.s(), value.t(), value.omega(), value.v1(), value.v2(), value.v3(), value.v4()));
		if (object instanceof MasterSecretKey value)
			return this.sumLengths(List.of(value.r(), value.s(), value.t(), value.omega(), value.t1(), value.t2(), value.t3(), value.t4()));
		if (object instanceof EncryptionKey value)
			return this.sumLengths(List.of(value.x(), value.z()));
		if (object instanceof BasicCipherText value)
			return this.sumLengths(List.of(value.c0(), value.c1(), value.c2(), value.c3(), value.c4(), value.coefficients()));
		if (object instanceof Token value)
			return this.sumLengths(List.of(value.t0(), value.t1(), value.t2(), value.t3(), value.t4()));
		if (object instanceof CipherText value)
			return this.sumLengths(List.of(value.c0(), value.c1(), value.c2(), value.c3(), value.c4(), value.proof1(), value.proof2(), value.proof3(), value.proof4(), value.proof5()));
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

	private static List<Object> averageResults(final List<RunResult> runs)
	{
		if (runs.isEmpty())
			return List.of();
		final List<Object> result = new ArrayList<>(runs.get(0).asList());
		for (int index = 5; index < 9; ++index)
		{
			if ("N/A".equals(result.get(index)))
				continue;
			int successes = 0;
			for (final RunResult run : runs)
				if (Boolean.TRUE.equals(run.asList().get(index)))
					++successes;
			result.set(index, Integer.valueOf(successes));
		}
		for (int index = 9; index < result.size(); ++index)
		{
			double total = 0.0;
			boolean valid = true;
			for (final RunResult run : runs)
			{
				final Object metric = run.asList().get(index);
				if (!positiveMetric(metric))
				{
					valid = false;
					break;
				}
				total += ((Number)metric).doubleValue();
			}
			if (valid)
			{
				final double average = total / runs.size();
				result.set(index, average == Math.rint(average) ? Integer.valueOf((int)average) : Double.valueOf(average));
			}
			else
				result.set(index, "N/A");
		}
		result.set(4, Integer.valueOf(runs.size()));
		return result;
	}

	private static boolean averagedResultValid(final List<Object> result, final int runCount)
	{
		if (result == null || result.size() != 35)
			return false;
		for (final int index : new int[] { 5, 7, 8 })
			if (!(result.get(index) instanceof Integer) || ((Integer)result.get(index)).intValue() != runCount)
				return false;
		for (int index = 14; index < 24; ++index)
			if (!positiveMetric(result.get(index)))
				return false;
		for (int index = 29; index < 35; ++index)
			if (!positiveMetric(result.get(index)))
				return false;
		return true;
	}

	private static boolean expectedUnavailable(final List<Object> result)
	{
		return result != null && !result.isEmpty() && ("MNT201".equals(result.get(0)) || "MNT224".equals(result.get(0))) && Boolean.FALSE.equals(result.get(5));
	}

	public SchemeCANIPSI()
	{
		this(new CurveParameter("SS512", 512));
	}

	public SchemeCANIPSI(final CurveParameter curveParameter)
	{
		this(createPairing(curveParameter), curveParameter.securityParameter());
	}

	public SchemeCANIPSI(final Pairing pairing, final int securityParameter)
	{
		if (pairing == null)
			throw new IllegalArgumentException("The pairing is missing.");
		this.pairing = pairing;
		this.securityParameter = securityParameter >= 1 ? securityParameter : 512;
	}

	public List<Element> randomSecrets(final int count)
	{
		final int length = count >= 1 ? count : this.n;
		final List<Element> secrets = new ArrayList<>();
		for (int index = 0; index < length; ++index)
			secrets.add(this.randomScalar());
		return List.copyOf(secrets);
	}

	public BasicSetupResult BSetup(final int requestedN, final int requestedM)
	{
		if (!this.pairing.isSymmetric())
			throw new IllegalStateException("The basic scheme requires a symmetric pairing.");
		this.basicSetUp = false;
		if (requestedN >= 1 && requestedM >= 1 && requestedM <= requestedN)
		{
			this.n = requestedN;
			this.m = requestedM;
		}
		else
		{
			this.n = DEFAULT_N;
			this.m = DEFAULT_M;
		}
		final Element g = this.randomG1();
		final Element omega = this.randomScalar();
		final Element t1 = this.generateRandomNonZeroZRElement();
		final Element t2 = this.generateRandomNonZeroZRElement();
		final Element t3 = this.generateRandomNonZeroZRElement();
		final Element t4 = this.generateRandomNonZeroZRElement();
		final Element omegaPublic = power(this.pair(g, g), scalarProduct(scalarProduct(t1, t2), omega));
		this.basicPublicKey = new BasicPublicKey(g, this.randomG1(), omegaPublic, power(g, t1), power(g, t2), power(g, t3), power(g, t4));
		this.basicSecretKey = new BasicSecretKey(omega, t1, t2, t3, t4);
		this.basicSetUp = true;
		return new BasicSetupResult(this.basicPublicKey, this.basicSecretKey);
	}

	public Element BKGen(final Object identity)
	{
		if (!this.basicSetUp)
			this.BSetup(this.n, this.m);
		return this.randomScalar();
	}

	public BasicCipherText BEncryption(final byte[] keyword, final List<Element> sourceSecrets, final Element selectedSecret)
	{
		if (!this.basicSetUp)
			this.BSetup(this.n, this.m);
		final byte[] target = this.normalizeKeyword(keyword);
		final List<Element> secrets = this.normalizeSecrets(sourceSecrets);
		final Element selected = this.normalizeSelectedSecret(secrets, selectedSecret);
		final Element s1 = this.randomScalar();
		final Element s2 = this.randomScalar();
		final Element keywordBase = multiply(this.basicPublicKey.g1(), this.hashToG1(target));
		final List<Element> values = this.membershipValues(this.basicPublicKey.omega(), secrets);
		return new BasicCipherText(
			power(keywordBase, selected),
			power(this.basicPublicKey.v1(), subtract(selected, s1)),
			power(this.basicPublicKey.v2(), s1),
			power(this.basicPublicKey.v3(), subtract(selected, s2)),
			power(this.basicPublicKey.v4(), s2),
			this.computeCoefficients(values));
	}

	public Token BTokenGen(final byte[] keyword, final Element basicUserKey)
	{
		if (!this.basicSetUp)
			this.BSetup(this.n, this.m);
		final byte[] query = this.normalizeKeyword(keyword);
		final Element r1 = this.randomScalar();
		final Element r2 = this.randomScalar();
		final Element base = multiply(this.basicPublicKey.g1(), this.hashToG1(query));
		final BasicSecretKey secret = this.basicSecretKey;
		return new Token(
			power(this.basicPublicKey.g(), add(scalarProduct(scalarProduct(r1, secret.t1()), secret.t2()), scalarProduct(scalarProduct(r2, secret.t3()), secret.t4()))),
			multiply(power(this.basicPublicKey.v2(), secret.omega()), power(base, negate(scalarProduct(r1, secret.t2())))),
			multiply(power(this.basicPublicKey.v1(), secret.omega()), power(base, negate(scalarProduct(r1, secret.t1())))),
			power(base, negate(scalarProduct(r2, secret.t4()))),
			power(base, negate(scalarProduct(r2, secret.t3()))));
	}

	public boolean BQuery(final BasicCipherText cipherText, final Token token)
	{
		if (!this.basicSetUp || cipherText == null || token == null)
			return false;
		final Element paired = this.pairingProduct(
			token.t0(), cipherText.c0(),
			new Element[] { token.t1(), token.t2(), token.t3(), token.t4() },
			new Element[] { cipherText.c1(), cipherText.c2(), cipherText.c3(), cipherText.c4() });
		final Element polynomial = this.computePolynomial(this.hashToScalar(paired), cipherText.coefficients());
		return polynomial != null && polynomial.isZero();
	}

	public SetupResult Setup(final int requestedN, final int requestedM)
	{
		this.setUp = false;
		if (requestedN >= 1 && requestedM >= 1 && requestedM <= requestedN)
		{
			this.n = requestedN;
			this.m = requestedM;
		}
		else
		{
			this.n = DEFAULT_N;
			this.m = DEFAULT_M;
		}
		final Element g1 = this.randomG1();
		final Element g2 = this.randomG2();
		final Element r = this.randomScalar();
		final Element s = this.generateRandomNonZeroZRElement();
		final Element t = this.randomScalar();
		final Element omega = this.randomScalar();
		final Element t1 = this.generateRandomNonZeroZRElement();
		final Element t2 = this.generateRandomNonZeroZRElement();
		final Element t3 = this.generateRandomNonZeroZRElement();
		final Element t4 = this.generateRandomNonZeroZRElement();
		this.masterPublicKey = new MasterPublicKey(
			g1, g2, this.randomG1(), power(g1, r), power(g2, s), power(g1, t),
			power(this.pair(g1, g2), scalarProduct(scalarProduct(t1, t2), omega)),
			power(g2, t1), power(g2, t2), power(g2, t3), power(g2, t4));
		this.masterSecretKey = new MasterSecretKey(r, s, t, omega, t1, t2, t3, t4);
		this.setUp = true;
		return new SetupResult(this.masterPublicKey, this.masterSecretKey);
	}

	public UserKeys KGen(final Object identity, final List<TraceEntry> tracingList)
	{
		if (!this.setUp)
			this.Setup(this.n, this.m);
		final List<TraceEntry> entries = tracingList == null ? new ArrayList<>() : tracingList;
		final Element secretKey = this.randomScalar();
		final Element x = this.generateRandomNonZeroZRElement();
		final Element denominator = scalarProduct(this.masterSecretKey.s(), x);
		final Element z = scalarProduct(subtract(this.masterSecretKey.r(), x), denominator.duplicate().invert().getImmutable());
		final Element zPublic = power(this.masterPublicKey.g1(), z);
		final EncryptionKey encryptionKey = new EncryptionKey(x, zPublic);
		final Element tag = this.hashToScalar(power(zPublic, x));
		entries.add(new TraceEntry(identity, secretKey, tag));
		return new UserKeys(secretKey, encryptionKey);
	}

	public CipherText Encryption(final byte[] keyword, final Element userSecretKey, final EncryptionKey encryptionKey, final List<Element> sourceSecrets, final Element selectedSecret)
	{
		if (!this.setUp)
			this.Setup(this.n, this.m);
		final Element secretKey = this.validScalar(userSecretKey) ? userSecretKey : this.randomScalar();
		final EncryptionKey publicKey = encryptionKey != null && this.validScalar(encryptionKey.x()) && this.validG1(encryptionKey.z()) ? encryptionKey : this.KGen(null, new ArrayList<>()).encryptionKey();
		final byte[] target = this.normalizeKeyword(keyword);
		final List<Element> secrets = this.normalizeSecrets(sourceSecrets);
		final Element selected = this.normalizeSelectedSecret(secrets, selectedSecret);
		final Element split1 = this.randomScalar();
		final Element split2 = this.randomScalar();
		final Element keywordBase = multiply(this.masterPublicKey.g3(), this.hashToG1(target));
		final Element c0 = power(keywordBase, selected);
		final Element c1 = power(this.masterPublicKey.v1(), subtract(selected, split1));
		final Element c2 = power(this.masterPublicKey.v2(), split1);
		final Element c3 = power(this.masterPublicKey.v3(), subtract(selected, split2));
		final Element c4 = power(this.masterPublicKey.v4(), split2);
		final Element[] coefficients = this.computeCoefficients(this.membershipValues(this.masterPublicKey.omega(), secrets));
		final Element alpha = this.randomScalar();
		final Element proof1 = power(this.masterPublicKey.g1(), alpha);
		final Element proof2 = multiply(power(publicKey.z(), publicKey.x()), power(this.masterPublicKey.t(), alpha));
		final Element proof3 = power(this.pair(this.masterPublicKey.t(), this.masterPublicKey.s()), alpha);
		final ByteArrayOutputStream serialized = new ByteArrayOutputStream();
		for (final Element element : new Element[] { c0, c1, c2, c3, c4 })
			serialized.writeBytes(element.toBytes());
		for (int index = 0; index + 1 < coefficients.length; ++index)
			serialized.writeBytes(coefficients[index].toBytes());
		for (final Element element : new Element[] { proof1, proof2, proof3 })
			serialized.writeBytes(element.toBytes());
		final Element proof4 = this.hashToScalar(serialized.toByteArray());
		final Element proof5 = add(scalarProduct(secretKey, proof4), publicKey.x());
		return new CipherText(c0, c1, c2, c3, c4, proof1, proof2, proof3, proof4, proof5);
	}

	public Token TokenGen(final byte[] keyword, final Element userSecretKey)
	{
		if (!this.setUp)
			this.Setup(this.n, this.m);
		final byte[] query = this.normalizeKeyword(keyword);
		final Element r1 = this.randomScalar();
		final Element r2 = this.randomScalar();
		final Element base = multiply(this.masterPublicKey.g3(), this.hashToG1(query));
		final MasterSecretKey secret = this.masterSecretKey;
		return new Token(
			power(this.masterPublicKey.g2(), add(scalarProduct(scalarProduct(r1, secret.t1()), secret.t2()), scalarProduct(scalarProduct(r2, secret.t3()), secret.t4()))),
			multiply(power(this.masterPublicKey.g1(), scalarProduct(secret.omega(), secret.t2())), power(base, negate(scalarProduct(r1, secret.t2())))),
			multiply(power(this.masterPublicKey.g1(), scalarProduct(secret.omega(), secret.t1())), power(base, negate(scalarProduct(r1, secret.t1())))),
			power(base, negate(scalarProduct(r2, secret.t4()))),
			power(base, negate(scalarProduct(r2, secret.t3()))));
	}

	public boolean Query(final CipherText cipherText, final Token token, final List<Element> sourceSecrets)
	{
		if (!this.setUp || cipherText == null || token == null)
			return false;
		final List<Element> secrets = this.normalizeSecrets(sourceSecrets);
		final Element[] coefficients = this.computeCoefficients(this.membershipValues(this.masterPublicKey.omega(), secrets));
		Element paired = this.pair(cipherText.c0(), token.t0());
		for (final Element[] term : new Element[][] {
			{ token.t1(), cipherText.c1() }, { token.t2(), cipherText.c2() },
			{ token.t3(), cipherText.c3() }, { token.t4(), cipherText.c4() } })
			paired = multiply(paired, this.pair(term[0], term[1]));
		final Element polynomial = this.computePolynomial(this.hashToScalar(paired), coefficients);
		return polynomial != null && polynomial.isZero();
	}

	public TraceEntry Trace(final CipherText cipherText, final List<TraceEntry> tracingList)
	{
		if (!this.setUp || cipherText == null || tracingList == null)
			return null;
		final Element tag = this.hashToScalar(divide(cipherText.proof2(), power(cipherText.proof1(), this.masterSecretKey.t())));
		for (final TraceEntry entry : tracingList)
			if (entry != null && entry.tag() != null && entry.tag().isEqual(tag))
				return entry;
		return null;
	}

	public static RunResult conductScheme(final CurveParameter curveParameter, final int n, final int m, final Integer run, final boolean verbose)
	{
		final String curveName = curveParameter == null ? "N/A" : curveParameter.curveName();
		final int securityParameter = curveParameter == null ? 512 : curveParameter.securityParameter();
		final Object runValue = run != null && run.intValue() >= 1 ? run : "N/A";
		if (verbose)
		{
			System.out.println("Curve: (" + curveName + ", " + securityParameter + ")");
			System.out.println("$n$: " + n);
			System.out.println("$m$: " + m);
			System.out.println("run: " + runValue);
		}
		if (n < 1 || m < 1 || m > n)
			return RunResult.invalid(curveName, securityParameter, n, m, runValue);
		final SchemeCANIPSI scheme;
		try
		{
			scheme = new SchemeCANIPSI(curveParameter);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, n, m, runValue);
		}
		if (verbose)
			System.out.println("Is the system valid? Yes.");
		try
		{
			final List<Object> metrics = new ArrayList<>();
			boolean basicCorrect = false;
			if (scheme.pairing.isSymmetric())
			{
				long startTime = System.nanoTime();
				final BasicSetupResult basicSetup = scheme.BSetup(n, m);
				metrics.add(Double.valueOf(elapsedSeconds(startTime)));
				startTime = System.nanoTime();
				final List<Element> basicKeys = new ArrayList<>();
				for (int index = 0; index < n; ++index)
					basicKeys.add(scheme.BKGen(Integer.valueOf(index)));
				metrics.add(Double.valueOf(elapsedSeconds(startTime) / n));
				final List<Element> secrets = scheme.randomSecrets(n);
				final List<BasicCipherText> ciphers = new ArrayList<>();
				startTime = System.nanoTime();
				for (int index = 0; index < n; ++index)
					ciphers.add(scheme.BEncryption(("TP" + index).getBytes(StandardCharsets.UTF_8), secrets, secrets.get(index)));
				metrics.add(Double.valueOf(elapsedSeconds(startTime) / n));
				final List<Token> tokens = new ArrayList<>();
				startTime = System.nanoTime();
				for (int index = 0; index < m; ++index)
					tokens.add(scheme.BTokenGen(("TP" + index).getBytes(StandardCharsets.UTF_8), basicKeys.get(index)));
				metrics.add(Double.valueOf(elapsedSeconds(startTime) / m));
				startTime = System.nanoTime();
				basicCorrect = true;
				for (int index = 0; index < m; ++index)
					basicCorrect &= scheme.BQuery(ciphers.get(index), tokens.get(index));
				metrics.add(Double.valueOf(elapsedSeconds(startTime) / m));
				metrics.add(Integer.valueOf(scheme.getLengthOf(basicSetup.publicKey())));
				metrics.add(Integer.valueOf(scheme.getLengthOf(basicSetup.secretKey())));
				metrics.add(Integer.valueOf(scheme.getLengthOf(basicKeys)));
				metrics.add(Integer.valueOf(scheme.getLengthOf(ciphers)));
				metrics.add(Integer.valueOf(scheme.getLengthOf(tokens)));
			}
			else
				for (int index = 0; index < 10; ++index)
					metrics.add("N/A");
			long startTime = System.nanoTime();
			final SetupResult setup = scheme.Setup(n, m);
			final double setupTime = elapsedSeconds(startTime);
			final List<TraceEntry> tracingList = new ArrayList<>();
			final List<UserKeys> keys = new ArrayList<>();
			startTime = System.nanoTime();
			for (int index = 0; index < n; ++index)
				keys.add(scheme.KGen(Integer.valueOf(index), tracingList));
			final double keyTime = elapsedSeconds(startTime) / n;
			final List<Element> secrets = scheme.randomSecrets(n);
			final List<CipherText> ciphers = new ArrayList<>();
			startTime = System.nanoTime();
			for (int index = 0; index < n; ++index)
				ciphers.add(scheme.Encryption(("TP" + index).getBytes(StandardCharsets.UTF_8), keys.get(index).secretKey(), keys.get(index).encryptionKey(), secrets, secrets.get(index)));
			final double encryptionTime = elapsedSeconds(startTime) / n;
			final List<Token> tokens = new ArrayList<>();
			startTime = System.nanoTime();
			for (int index = 0; index < m; ++index)
				tokens.add(scheme.TokenGen(("TP" + index).getBytes(StandardCharsets.UTF_8), keys.get(index).secretKey()));
			final double tokenTime = elapsedSeconds(startTime) / m;
			startTime = System.nanoTime();
			boolean schemeCorrect = true;
			for (int index = 0; index < m; ++index)
				schemeCorrect &= scheme.Query(ciphers.get(index), tokens.get(index), secrets);
			final double queryTime = elapsedSeconds(startTime) / m;
			startTime = System.nanoTime();
			boolean tracingVerified = true;
			for (int index = 0; index < m; ++index)
				tracingVerified &= scheme.Trace(ciphers.get(index), tracingList) != null;
			final double traceTime = elapsedSeconds(startTime) / m;
			final List<Object> orderedMetrics = new ArrayList<>(metrics.subList(0, 5));
			orderedMetrics.addAll(List.of(setupTime, keyTime, encryptionTime, tokenTime, queryTime, traceTime));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(scheme.randomScalar())));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(scheme.randomG1())));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(scheme.randomG2())));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(scheme.randomGT())));
			orderedMetrics.addAll(metrics.subList(5, 10));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(setup.publicKey())));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(setup.secretKey())));
			final List<Element> secretKeys = keys.stream().map(UserKeys::secretKey).toList();
			final List<EncryptionKey> encryptionKeys = keys.stream().map(UserKeys::encryptionKey).toList();
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(secretKeys)));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(encryptionKeys)));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(ciphers)));
			orderedMetrics.add(Integer.valueOf(scheme.getLengthOf(tokens)));
			if (verbose)
			{
				System.out.println("Is the basic scheme correct? " + (scheme.pairing.isSymmetric() && basicCorrect ? "Yes." : scheme.pairing.isSymmetric() ? "No." : "N/A."));
				System.out.println("Is the scheme correct? " + (schemeCorrect ? "Yes." : "No."));
				System.out.println("Is the tracing verified? " + (tracingVerified ? "Yes." : "No."));
				System.out.println();
			}
			return new RunResult(curveName, securityParameter, n, m, runValue, true, scheme.pairing.isSymmetric() ? Boolean.valueOf(basicCorrect) : "N/A", schemeCorrect, tracingVerified, orderedMetrics);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("The experiment failed due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, n, m, runValue);
		}
	}

	public record BasicPublicKey(Element g, Element g1, Element omega, Element v1, Element v2, Element v3, Element v4) {}

	public record BasicSecretKey(Element omega, Element t1, Element t2, Element t3, Element t4) {}

	public record BasicSetupResult(BasicPublicKey publicKey, BasicSecretKey secretKey) {}

	public record MasterPublicKey(Element g1, Element g2, Element g3, Element r, Element s, Element t, Element omega, Element v1, Element v2, Element v3, Element v4) {}

	public record MasterSecretKey(Element r, Element s, Element t, Element omega, Element t1, Element t2, Element t3, Element t4) {}

	public record SetupResult(MasterPublicKey publicKey, MasterSecretKey secretKey) {}

	public record EncryptionKey(Element x, Element z) {}

	public record UserKeys(Element secretKey, EncryptionKey encryptionKey) {}

	public record TraceEntry(Object identity, Element secretKey, Element tag) {}

	public record BasicCipherText(Element c0, Element c1, Element c2, Element c3, Element c4, Element[] coefficients) {}

	public record Token(Element t0, Element t1, Element t2, Element t3, Element t4) {}

	public record CipherText(Element c0, Element c1, Element c2, Element c3, Element c4, Element proof1, Element proof2, Element proof3, Element proof4, Element proof5) {}

	public record CurveParameter(String curveName, int securityParameter) {}

	public record RunResult(String curveName, int securityParameter, int n, int m, Object run, boolean systemValid, Object basicSchemeCorrect, boolean schemeCorrect, boolean tracingVerified, List<Object> metrics)
	{
		private static RunResult invalid(final String curveName, final int securityParameter, final int n, final int m, final Object run)
		{
			return new RunResult(curveName, securityParameter, n, m, run, false, Boolean.FALSE, false, false, Collections.nCopies(26, "N/A"));
		}

		public List<Object> asList()
		{
			final List<Object> values = new ArrayList<>(List.of(
				this.curveName, Integer.valueOf(this.securityParameter), Integer.valueOf(this.n), Integer.valueOf(this.m), this.run,
				Boolean.valueOf(this.systemValid), this.basicSchemeCorrect, Boolean.valueOf(this.schemeCorrect), Boolean.valueOf(this.tracingVerified)));
			values.addAll(this.metrics);
			return values;
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
			final List<CurveParameter> curves = List.of(
				new CurveParameter("BN254", 128),
				new CurveParameter("SS512", 128), new CurveParameter("SS512", 256), new CurveParameter("SS512", 512),
				new CurveParameter("SS1024", 512), new CurveParameter("SS1024", 1024));
			final List<String> columns = List.of(
				"curveParameter", "secparam", "n", "m", "runCount", "isSystemValid", "isBSchemeCorrect", "isSchemeCorrect", "isTracingVerified",
				"BSetup (s)", "BKGen (s)", "BEncryption (s)", "BTokenGen (s)", "BQuery (s)", "Setup (s)", "KGen (s)",
				"Encryption (s)", "TokenGen (s)", "Query (s)", "Trace (s)", "elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)",
				"elementOfGT (B)", "bpk (B)", "bsk (B)", "bsk_IDs (B)", "BCT_TPs (B)", "BTokens (B)", "mpk (B)", "msk (B)",
				"sk_IDs (B)", "ek_IDs (B)", "CT_TPs (B)", "Tokens (B)");
			final Saver saver = new Saver(options.outputFilePath(), columns, options.decimalPlace(), options.encoding());
			final List<List<Object>> results = new ArrayList<>();
			final int runCount = options.runCount();
			for (final CurveParameter curve : curves)
				for (int n = 10; n <= 30; n += 5)
					for (int m = 5; m < n; m += 5)
					{
						final List<RunResult> runs = new ArrayList<>();
						for (int run = 1; run <= runCount; ++run)
							runs.add(conductScheme(curve, n, m, Integer.valueOf(run), options.verbose()));
						final List<Object> average = averageResults(runs);
						results.add(average);
						saver.save(results);
					}
			errorLevel = !results.isEmpty() && results.stream().allMatch(result -> expectedUnavailable(result) || averagedResultValid(result, runCount)) ? EXIT_SUCCESS : EXIT_FAILURE;
		}
		else if (options.flag() == EXIT_SUCCESS)
			errorLevel = EXIT_SUCCESS;
		if (options.waitingTime() == 0.0)
			System.out.println("The execution has finished (" + errorLevel + ").");
		else if (Double.isFinite(options.waitingTime()) && options.waitingTime() > 0.0)
		{
			System.out.println("Please wait " + options.waitingTime() + " second(s) for automatic exit (" + errorLevel + ").");
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
}