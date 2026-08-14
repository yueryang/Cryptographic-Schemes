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
	private static final String SCHEME_NAME = "SchemeVLPSICA";
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
		System.out.println("This is a possible implementation of the VLPSICA cryptographic scheme in Java based on JPBC.");
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

public final class SchemeVLPSICA
{
	private static final int DEFAULT_M = 10;
	private static final int DEFAULT_N = 10;
	private static final int DEFAULT_D = 10;
	private static final int EXIT_SUCCESS = 0;
	private static final int EXIT_FAILURE = 1;
	private static final int EOF = -1;
	private static final SecureRandom RANDOM = new SecureRandom();
	private static final Map<String, Pairing> PAIRINGS = new LinkedHashMap<>();
	private final Pairing pairing;
	private final int securityParameter;
	private int m = DEFAULT_M;
	private int n = DEFAULT_N;
	private int d = DEFAULT_D;
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

	private static Element scalarPower(final Element base, final int exponent)
	{
		return base.duplicate().pow(BigInteger.valueOf(exponent)).getImmutable();
	}

	private static Element negate(final Element value)
	{
		return value.duplicate().negate().getImmutable();
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

	private Element oneG1()
	{
		return this.immutable(this.pairing.getG1().newOneElement());
	}

	private Element oneG2()
	{
		return this.immutable(this.pairing.getG2().newOneElement());
	}

	private Element oneScalar()
	{
		return this.immutable(this.pairing.getZr().newOneElement());
	}

	private Element zeroScalar()
	{
		return this.immutable(this.pairing.getZr().newZeroElement());
	}

	private Element scalarFromInt(final int value)
	{
		return this.immutable(this.pairing.getZr().newElement(value));
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

	private BigInteger hashTarget(final Element element)
	{
		try
		{
			final String algorithm;
			final int digestBits;
			switch (this.securityParameter)
			{
			case 128:
				algorithm = "MD5";
				digestBits = 128;
				break;
			case 160:
				algorithm = "SHA-1";
				digestBits = 160;
				break;
			case 224:
				algorithm = "SHA3-224";
				digestBits = 224;
				break;
			case 256:
				algorithm = "SHA3-256";
				digestBits = 256;
				break;
			case 384:
				algorithm = "SHA3-384";
				digestBits = 384;
				break;
			default:
				algorithm = "SHA3-512";
				digestBits = 512;
				break;
			}
			final byte[] digest = MessageDigest.getInstance(algorithm).digest(element.toBytes());
			if (this.securityParameter == digestBits)
				return new BigInteger(1, digest);
			final int outputBytes = (this.securityParameter + 7) >>> 3;
			final ByteArrayOutputStream expanded = new ByteArrayOutputStream();
			while (expanded.size() < outputBytes)
				expanded.writeBytes(digest);
			final byte[] value = Arrays.copyOf(expanded.toByteArray(), outputBytes);
			final int excessBits = outputBytes * 8 - this.securityParameter;
			if (excessBits > 0)
				value[0] &= (byte)(0xFF >>> excessBits);
			return new BigInteger(1, value);
		}
		catch (final NoSuchAlgorithmException exception)
		{
			throw new IllegalStateException("The requested hash algorithm is unavailable.", exception);
		}
	}

	private Element interpolate(final List<Element> xPoints, final List<Element> yPoints, final Element x)
	{
		if (xPoints == null || yPoints == null || xPoints.size() != yPoints.size() || xPoints.isEmpty() || !this.validScalar(x))
			return this.zeroScalar();
		Element result = this.oneScalar();
		for (int index = 0; index < xPoints.size(); ++index)
		{
			Element basis = this.oneScalar();
			for (int other = 0; other < xPoints.size(); ++other)
				if (index != other)
				{
					final Element numerator = subtract(x, xPoints.get(other));
					final Element denominator = subtract(xPoints.get(index), xPoints.get(other)).duplicate().invert().getImmutable();
					basis = scalarProduct(basis, scalarProduct(numerator, denominator));
				}
			result = add(result, scalarProduct(yPoints.get(index), basis));
		}
		return result;
	}

	private Element groupProduct(final List<Element> elements, final boolean sourceGroup)
	{
		Element result = sourceGroup ? this.oneG1() : this.oneG2();
		for (final Element element : elements)
			result = multiply(result, element);
		return result;
	}

	private List<Element> normalizeScalars(final List<Element> values, final int expected)
	{
		if (values != null && values.size() == expected && values.stream().allMatch(this::validScalar))
			return List.copyOf(values);
		return this.randomScalars(expected);
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
		if (object instanceof BigInteger || object instanceof Integer || object instanceof Long)
			return (this.securityParameter + 7) >>> 3;
		if (object instanceof Collection<?>)
			return this.sumLengths((Collection<?>)object);
		if (object instanceof MasterPublicKey value)
			return this.sumLengths(List.of(value.g1(), value.sPrime()));
		if (object instanceof MasterSecretKey value)
			return this.sumLengths(List.of(value.g2(), value.sValues()));
		if (object instanceof SenderOutput value)
			return this.sumLengths(List.of(value.t(), value.u()));
		if (object instanceof ReceiverOutput value)
			return this.sumLengths(List.of(value.r(), value.rPrime()));
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
		for (int index = 6; index < 8; ++index)
		{
			int successes = 0;
			for (final RunResult run : runs)
				if (Boolean.TRUE.equals(run.asList().get(index)))
					++successes;
			result.set(index, Integer.valueOf(successes));
		}
		for (int index = 8; index < result.size(); ++index)
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
		result.set(5, Integer.valueOf(runs.size()));
		return result;
	}

	private static boolean averagedResultValid(final List<Object> result, final int runCount)
	{
		if (result == null || result.size() != 26)
			return false;
		for (int index = 6; index < 8; ++index)
			if (!(result.get(index) instanceof Integer) || ((Integer)result.get(index)).intValue() != runCount)
				return false;
		for (int index = 8; index < result.size(); ++index)
			if (!positiveMetric(result.get(index)))
				return false;
		return true;
	}

	private static boolean expectedUnavailable(final List<Object> result)
	{
		return result != null && !result.isEmpty() && ("MNT201".equals(result.get(0)) || "MNT224".equals(result.get(0))) && Boolean.FALSE.equals(result.get(6));
	}

	private List<Element> randomGroupElements(final int count, final boolean sourceGroup)
	{
		final List<Element> elements = new ArrayList<>();
		for (int index = 0; index < count; ++index)
			elements.add(sourceGroup ? this.randomG1() : this.randomG2());
		return List.copyOf(elements);
	}

	private <T> List<T> rotate(final List<T> values)
	{
		if (values.isEmpty())
			return List.of();
		final int offset = RANDOM.nextInt(values.size());
		final List<T> rotated = new ArrayList<>();
		for (int index = 0; index < values.size(); ++index)
			rotated.add(values.get((index + offset) % values.size()));
		return List.copyOf(rotated);
	}


	public SchemeVLPSICA()
	{
		this(new CurveParameter("SS512", 512));
	}

	public SchemeVLPSICA(final CurveParameter curveParameter)
	{
		this(createPairing(curveParameter), curveParameter.securityParameter());
	}

	public SchemeVLPSICA(final Pairing pairing, final int securityParameter)
	{
		if (pairing == null)
			throw new IllegalArgumentException("The pairing is missing.");
		this.pairing = pairing;
		this.securityParameter = securityParameter >= 1 ? securityParameter : 512;
	}

	public List<Element> randomScalars(final int count)
	{
		final int length = Math.max(1, count);
		final List<Element> values = new ArrayList<>();
		for (int index = 0; index < length; ++index)
			values.add(this.randomScalar());
		return List.copyOf(values);
	}

	public SetupResult Setup(final int requestedM, final int requestedN, final int requestedD)
	{
		this.setUp = false;
		this.m = requestedM >= 1 ? requestedM : DEFAULT_M;
		this.n = requestedN >= 1 ? requestedN : DEFAULT_N;
		this.d = requestedD >= 1 ? requestedD : DEFAULT_D;
		final Element g1 = this.oneG1();
		final Element g2 = this.oneG2();
		final Element s = this.generateRandomNonZeroZRElement();
		final List<Element> sValues = new ArrayList<>();
		for (int index = 0; index <= this.m + this.d; ++index)
			sValues.add(power(g2, scalarPower(s, index)));
		this.masterPublicKey = new MasterPublicKey(g1, power(g1, s));
		this.masterSecretKey = new MasterSecretKey(g2, List.copyOf(sValues));
		this.setUp = true;
		return new SetupResult(this.masterPublicKey, this.masterSecretKey);
	}

	public SenderOutput Sender(final List<Element> sharedValues, final List<Element> senderValues)
	{
		if (!this.setUp)
			this.Setup(this.m, this.n, this.d);
		final List<Element> shared = this.normalizeScalars(sharedValues, this.d);
		final List<Element> sender = this.normalizeScalars(senderValues, this.n);
		final int rotation = RANDOM.nextInt(this.n);
		final List<Element> tValues = this.randomScalars(this.n);
		final List<Element> t = new ArrayList<>();
		final List<Element> u = new ArrayList<>();
		for (int index = 0; index < this.n; ++index)
		{
			t.add(power(this.masterPublicKey.g1(), tValues.get(index)));
			u.add(multiply(this.masterPublicKey.sPrime(), power(this.masterPublicKey.g1(), negate(sender.get((index + rotation) % this.n)))));
		}
		final List<Element> tPrimeValues = this.randomScalars(this.d);
		for (int index = 0; index < this.d; ++index)
		{
			t.add(power(this.masterPublicKey.g1(), tPrimeValues.get(index)));
			u.add(multiply(this.masterPublicKey.sPrime(), power(power(this.masterPublicKey.g1(), negate(shared.get(index))), tPrimeValues.get(index))));
		}
		return new SenderOutput(List.copyOf(t), List.copyOf(u));
	}

	public ReceiverOutput Receiver(final List<Element> sharedValues, final List<Element> receiverValues)
	{
		if (!this.setUp)
			this.Setup(this.m, this.n, this.d);
		final List<Element> shared = this.normalizeScalars(sharedValues, this.d);
		final List<Element> receiver = this.normalizeScalars(receiverValues, this.m);
		final List<Element> combined = new ArrayList<>(receiver);
		combined.addAll(shared);
		final List<Element> xPoints = new ArrayList<>();
		for (int index = 1; index <= this.m + this.d; ++index)
			xPoints.add(this.scalarFromInt(index));
		final Element r = this.randomScalar();
		final List<Element> factors = new ArrayList<>();
		for (int index = 0; index <= this.m + this.d; ++index)
			factors.add(power(this.masterSecretKey.sValues().get(index), this.interpolate(xPoints, combined, this.scalarFromInt(index))));
		final Element aggregate = power(this.groupProduct(factors, false), r);
		final List<Element> shortened = new ArrayList<>();
		for (int index = 0; index < this.m + this.d; ++index)
			shortened.add(power(this.masterSecretKey.sValues().get(index), this.interpolate(xPoints, combined, this.scalarFromInt(index))));
		final Element repeated = power(this.groupProduct(shortened, false), r);
		final List<Element> rPrime = new ArrayList<>();
		for (int index = 0; index < this.m + this.d; ++index)
			rPrime.add(repeated);
		return new ReceiverOutput(aggregate, List.copyOf(rPrime));
	}

	public List<BigInteger> Cloud1(final List<Element> senderT, final Element receiverR)
	{
		if (!this.setUp)
			this.Setup(this.m, this.n, this.d);
		final List<Element> t = senderT != null && senderT.size() == this.n + this.d && senderT.stream().allMatch(this::validG1) ? senderT : this.randomGroupElements(this.n + this.d, true);
		final Element r = this.validG2(receiverR) ? receiverR : this.randomG2();
		final List<BigInteger> values = new ArrayList<>();
		for (final Element value : t)
			values.add(this.hashTarget(this.pair(value, r)));
		return this.rotate(values);
	}

	public List<BigInteger> Cloud2(final List<Element> senderU, final List<Element> receiverRPrime)
	{
		if (!this.setUp)
			this.Setup(this.m, this.n, this.d);
		final List<Element> u = senderU != null && senderU.size() == this.n + this.d && senderU.stream().allMatch(this::validG1) ? senderU : this.randomGroupElements(this.n + this.d, true);
		final List<Element> rPrime = receiverRPrime != null && receiverRPrime.size() == this.m + this.d && receiverRPrime.stream().allMatch(this::validG2) ? receiverRPrime : this.randomGroupElements(this.m + this.d, false);
		final List<BigInteger> values = new ArrayList<>();
		for (final Element receiver : rPrime)
			for (final Element sender : u)
				values.add(this.hashTarget(this.pair(sender, receiver)));
		return this.rotate(values);
	}

	public Object Verify(final List<BigInteger> cloud2Values, final List<BigInteger> cloud1Values)
	{
		if (!this.setUp)
			this.Setup(this.m, this.n, this.d);
		if (cloud2Values == null || cloud1Values == null || cloud2Values.size() != (this.m + this.d) * (this.n + this.d) || cloud1Values.size() != this.n + this.d)
			return Boolean.FALSE;
		return new LinkedHashSet<>(cloud2Values).containsAll(new LinkedHashSet<>(cloud1Values)) ? Integer.valueOf(this.n) : Boolean.FALSE;
	}

	public static RunResult conductScheme(final CurveParameter curveParameter, final int m, final int n, final int d, final Integer run, final boolean verbose)
	{
		final String curveName = curveParameter == null ? "N/A" : curveParameter.curveName();
		final int securityParameter = curveParameter == null ? 512 : curveParameter.securityParameter();
		final Object runValue = run != null && run.intValue() >= 1 ? run : "N/A";
		if (verbose)
		{
			System.out.println("Curve: (" + curveName + ", " + securityParameter + ")");
			System.out.println("$m$: " + m);
			System.out.println("$n$: " + n);
			System.out.println("$d$: " + d);
			System.out.println("run: " + runValue);
		}
		if (m < 1 || n < 1 || d < 1)
			return RunResult.invalid(curveName, securityParameter, m, n, d, runValue);
		final SchemeVLPSICA scheme;
		try
		{
			scheme = new SchemeVLPSICA(curveParameter);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("Is the system valid? No. Failed to create the ``PairingGroup`` instance due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, m, n, d, runValue);
		}
		if (verbose)
			System.out.println("Is the system valid? Yes.");
		try
		{
			long startTime = System.nanoTime();
			final SetupResult setup = scheme.Setup(m, n, d);
			final double setupTime = elapsedSeconds(startTime);
			final List<Element> shared = scheme.randomScalars(d);
			final List<Element> senderValues = scheme.randomScalars(n);
			startTime = System.nanoTime();
			final SenderOutput sender = scheme.Sender(shared, senderValues);
			final double senderTime = elapsedSeconds(startTime);
			final List<Element> receiverValues = scheme.randomScalars(m);
			startTime = System.nanoTime();
			final ReceiverOutput receiver = scheme.Receiver(shared, receiverValues);
			final double receiverTime = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final List<BigInteger> w = scheme.Cloud1(sender.t(), receiver.r());
			final double cloud1Time = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final List<BigInteger> k = scheme.Cloud2(sender.u(), receiver.rPrime());
			final double cloud2Time = elapsedSeconds(startTime);
			startTime = System.nanoTime();
			final Object verification = scheme.Verify(k, w);
			final double verifyTime = elapsedSeconds(startTime);
			final boolean correct = !Boolean.FALSE.equals(verification);
			if (verbose)
			{
				System.out.println("Verify: " + verification);
				System.out.println("Is the scheme correct (result is not False)? " + (correct ? "Yes." : "No."));
				System.out.println();
			}
			final List<Object> metrics = List.of(
				setupTime, senderTime, receiverTime, cloud1Time, cloud2Time, verifyTime,
				printableSize(scheme.getLengthOf(scheme.randomScalar())), printableSize(scheme.getLengthOf(scheme.randomG1())),
				printableSize(scheme.getLengthOf(scheme.randomG2())), printableSize(scheme.getLengthOf(scheme.randomGT())),
				printableSize(scheme.getLengthOf(setup.publicKey())), printableSize(scheme.getLengthOf(setup.secretKey())),
				printableSize(scheme.getLengthOf(sender.t())), printableSize(scheme.getLengthOf(sender.u())),
				printableSize(scheme.getLengthOf(receiver.r())), printableSize(scheme.getLengthOf(receiver.rPrime())),
				printableSize(scheme.getLengthOf(w)), printableSize(scheme.getLengthOf(k)));
			return new RunResult(curveName, securityParameter, m, n, d, runValue, true, correct, metrics);
		}
		catch (final RuntimeException exception)
		{
			if (verbose)
				System.out.println("The experiment failed due to " + exception + ".");
			return RunResult.invalid(curveName, securityParameter, m, n, d, runValue);
		}
	}

	public record MasterPublicKey(Element g1, Element sPrime) {}

	public record MasterSecretKey(Element g2, List<Element> sValues) {}

	public record SetupResult(MasterPublicKey publicKey, MasterSecretKey secretKey) {}

	public record SenderOutput(List<Element> t, List<Element> u) {}

	public record ReceiverOutput(Element r, List<Element> rPrime) {}

	public record CurveParameter(String curveName, int securityParameter) {}

	public record RunResult(String curveName, int securityParameter, int m, int n, int d, Object run, boolean systemValid, boolean schemeCorrect, List<Object> metrics)
	{
		private static RunResult invalid(final String curveName, final int securityParameter, final int m, final int n, final int d, final Object run)
		{
			return new RunResult(curveName, securityParameter, m, n, d, run, false, false, Collections.nCopies(18, "N/A"));
		}

		public List<Object> asList()
		{
			final List<Object> values = new ArrayList<>(List.of(
				this.curveName, Integer.valueOf(this.securityParameter), Integer.valueOf(this.m), Integer.valueOf(this.n), Integer.valueOf(this.d),
				this.run, Boolean.valueOf(this.systemValid), Boolean.valueOf(this.schemeCorrect)));
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
				new CurveParameter("MNT201", 512), new CurveParameter("MNT224", 512), new CurveParameter("BN254", 128),
				new CurveParameter("SS512", 128), new CurveParameter("SS512", 256), new CurveParameter("SS512", 512),
				new CurveParameter("SS1024", 512), new CurveParameter("SS1024", 1024));
			final List<String> columns = List.of(
				"curveParameter", "secparam", "m", "n", "d", "runCount", "isSystemValid", "isSchemeCorrect",
				"Setup (s)", "Sender (s)", "Receiver (s)", "Cloud1 (s)", "Cloud 2(s)", "Verify (s)", "elementOfZR (B)",
				"elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", "mpk (B)", "msk (B)", "(T, T') (B)",
				"(U, U') (B)", "R (B)", "R' (B)", "W (B)", "K (B)");
			final Saver saver = new Saver(options.outputFilePath(), columns, options.decimalPlace(), options.encoding());
			final List<List<Object>> results = new ArrayList<>();
			final int runCount = options.runCount();
			for (final CurveParameter curve : curves)
				for (int m = 5; m <= 30; m += 5)
					for (int n = 5; n <= 30; n += 5)
						for (int d = 5; d <= 30; d += 5)
						{
							final List<RunResult> runs = new ArrayList<>();
							for (int run = 1; run <= runCount; ++run)
								runs.add(conductScheme(curve, m, n, d, Integer.valueOf(run), options.verbose()));
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