#!/usr/bin/env bash

set -u
set -o pipefail

readonly EXIT_SUCCESS=0
readonly EXIT_FAILURE=1
readonly SCRIPT_NAME='fetchJavaDependencies.sh'
readonly LOG4J_SUPPORTED_MAJOR='2'
readonly -a DOWNLOADABLE_ARTIFACTS=(
	'commons-collections4'
	'commons-compress'
	'commons-io'
	'log4j-api'
	'log4j-core'
	'poi'
	'poi-ooxml'
	'poi-ooxml-lite'
	'xmlbeans'
)
readonly -a ORDERED_ARTIFACTS=(
	'commons-collections4'
	'commons-compress'
	'commons-io'
	'jpbc-api'
	'jpbc-plaf'
	'log4j-api'
	'log4j-core'
	'poi'
	'poi-ooxml'
	'poi-ooxml-lite'
	'xmlbeans'
)
declare -a SELECTED_SOURCES=()
declare -a SELECTED_VERSIONS=()
declare -a STAGED_ARTIFACTS=()
TEMPORARY_DIRECTORY=''
DEPENDENCY_PATHS=''

fail()
{
	printf 'fetchJavaDependencies: %s\n' "$1" >&2
	exit "$EXIT_FAILURE"
}

cleanup()
{
	local status=$?

	trap - EXIT
	if [[ -n "$TEMPORARY_DIRECTORY" && -d "$TEMPORARY_DIRECTORY" ]]
	then
		rm -rf -- "$TEMPORARY_DIRECTORY" >/dev/null 2>&1 || true
	fi
	exit "$status"
}

report_added_file()
{
	printf '+++ lib/%s\n' "$1" >&2
}

report_removed_file()
{
	printf '%s\n' "--- lib/$1" >&2
}

trap cleanup EXIT
trap 'exit "$EXIT_FAILURE"' HUP INT TERM

LIB_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)" || fail 'failed to resolve the lib directory'
readonly LIB_DIRECTORY

require_commands()
{
	local command_name=''

	for command_name in awk curl find head mktemp mv rm sed
	do
		command -v "$command_name" >/dev/null 2>&1 || fail "required command is unavailable: ${command_name}"
	done
}

validate_jar()
{
	local jar_path="$1"
	local signature=''

	[[ -f "$jar_path" && ! -L "$jar_path" ]] || return 1
	signature="$(LC_ALL=C head -c 2 -- "$jar_path" 2>/dev/null)" || return 1
	[[ "$signature" == 'PK' ]]
}

is_downloadable_filename()
{
	local filename="$1"
	local artifact=''

	for artifact in "${DOWNLOADABLE_ARTIFACTS[@]}"
	do
		if [[ "$filename" =~ ^${artifact}-[0-9][0-9A-Za-z._+-]*\.jar$ ]]
		then
			return 0
		fi
	done
	return 1
}

is_known_filename()
{
	local filename="$1"

	case "$filename" in
	"$SCRIPT_NAME"|'jpbc-api-2.0.0.jar'|'jpbc-plaf-2.0.0.jar')
		return 0
		;;
	esac
	is_downloadable_filename "$filename"
}

validate_directory_entries()
{
	local entry=''
	local filename=''

	while IFS= read -r -d '' entry
	do
		filename="${entry##*/}"
		is_known_filename "$filename" || fail "unexpected lib entry was preserved: ${filename}"
		[[ -f "$entry" && ! -L "$entry" ]] || fail "lib entry is not a regular file: ${filename}"
	done < <(find "$LIB_DIRECTORY" -mindepth 1 -maxdepth 1 -print0)
}

read_latest_version()
{
	sed -n 's:.*<latest>\([^<]*\)</latest>.*:\1:p' "$1" | awk 'NR == 1 { print; exit }'
}

read_latest_supported_version()
{
	local metadata_path="$1"
	local artifact="$2"

	case "$artifact" in
	'log4j-api'|'log4j-core')
		sed -n 's:.*<version>\([^<]*\)</version>.*:\1:p' "$metadata_path" | awk -v prefix="${LOG4J_SUPPORTED_MAJOR}." 'index($0, prefix) == 1 { version = $0 } END { if (version) print version; else exit 1 }'
		;;
	*)
		read_latest_version "$metadata_path"
		;;
	esac
}

read_version_rank()
{
	awk -v wanted="$2" '
		match($0, /<version>[^<]+<\/version>/) {
			value = substr($0, RSTART, RLENGTH)
			sub(/^<version>/, "", value)
			sub(/<\/version>$/, "", value)
			++rank
			if (value == wanted) {
				print rank
				found = 1
				exit
			}
		}
		END { if (!found) exit 1 }
	' "$1"
}

base_url_for()
{
	case "$1" in
	'commons-collections4')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/commons/commons-collections4/'
		;;
	'commons-compress')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/commons/commons-compress/'
		;;
	'commons-io')
		printf '%s\n' 'https://repo1.maven.org/maven2/commons-io/commons-io/'
		;;
	'log4j-api')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-api/'
		;;
	'log4j-core')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-core/'
		;;
	'poi')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/poi/poi/'
		;;
	'poi-ooxml')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/poi/poi-ooxml/'
		;;
	'poi-ooxml-lite')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/poi/poi-ooxml-lite/'
		;;
	'xmlbeans')
		printf '%s\n' 'https://repo1.maven.org/maven2/org/apache/xmlbeans/xmlbeans/'
		;;
	*)
		return 1
		;;
	esac
}

download_file()
{
	local url="$1"
	local destination="$2"

	curl -fsS --proto '=https' --connect-timeout 15 --max-time 180 --retry 2 --output "$destination" "$url"
}

select_artifact_version()
{
	local artifact_index="$1"
	local artifact="$2"
	local metadata_path="$TEMPORARY_DIRECTORY/${artifact}-maven-metadata.xml"
	local base_url=''
	local latest_version=''
	local latest_rank=''
	local highest_local_rank=-1
	local highest_local_version=''
	local highest_local_file=''
	local candidate=''
	local filename=''
	local local_version=''
	local local_rank=''
	local staged_path=''

	base_url="$(base_url_for "$artifact")" || fail "no repository URL is configured for ${artifact}"
	download_file "${base_url}maven-metadata.xml" "$metadata_path" || fail "failed to download metadata for ${artifact}"
	latest_version="$(read_latest_supported_version "$metadata_path" "$artifact")" || fail "failed to parse the latest supported version for ${artifact}"
	[[ "$latest_version" =~ ^[0-9][0-9A-Za-z._+-]*$ ]] || fail "invalid latest version for ${artifact}: ${latest_version}"
	latest_rank="$(read_version_rank "$metadata_path" "$latest_version")" || fail "latest version is absent from metadata for ${artifact}: ${latest_version}"

	while IFS= read -r -d '' candidate
	do
		filename="${candidate##*/}"
		if [[ "$filename" =~ ^${artifact}-([0-9][0-9A-Za-z._+-]*)\.jar$ ]]
		then
			local_version="${BASH_REMATCH[1]}"
			if [[ "$artifact" == 'log4j-api' || "$artifact" == 'log4j-core' ]] && [[ ! "$local_version" =~ ^${LOG4J_SUPPORTED_MAJOR}\. ]]
			then
				continue
			fi
			local_rank="$(read_version_rank "$metadata_path" "$local_version")" || fail "local version is absent from metadata for ${artifact}: ${local_version}"
			if ((local_rank > highest_local_rank))
			then
				highest_local_rank=$local_rank
				highest_local_version="$local_version"
				highest_local_file="$candidate"
			fi
		fi
	done < <(find "$LIB_DIRECTORY" -mindepth 1 -maxdepth 1 -type f -name "${artifact}-*.jar" -print0)

	if ((highest_local_rank >= latest_rank))
	then
		SELECTED_VERSIONS[$artifact_index]="$highest_local_version"
		SELECTED_SOURCES[$artifact_index]="$highest_local_file"
		STAGED_ARTIFACTS[$artifact_index]='0'
		validate_jar "$highest_local_file" || fail "local JAR is invalid: ${filename}"
		return 0
	fi

	staged_path="$TEMPORARY_DIRECTORY/${artifact}-${latest_version}.jar"
	download_file "${base_url}${latest_version}/${artifact}-${latest_version}.jar" "$staged_path" || fail "failed to download ${artifact}-${latest_version}.jar"
	validate_jar "$staged_path" || fail "downloaded JAR is invalid: ${artifact}-${latest_version}.jar"
	SELECTED_VERSIONS[$artifact_index]="$latest_version"
	SELECTED_SOURCES[$artifact_index]="$staged_path"
	STAGED_ARTIFACTS[$artifact_index]='1'
}

append_dependency_path()
{
	local filename="$1"

	if [[ -z "$DEPENDENCY_PATHS" ]]
	then
		DEPENDENCY_PATHS="lib/${filename}"
	else
		DEPENDENCY_PATHS="${DEPENDENCY_PATHS}:lib/${filename}"
	fi
}

commit_downloadable_artifact()
{
	local artifact_index="$1"
	local artifact="$2"
	local selected_version="${SELECTED_VERSIONS[$artifact_index]}"
	local selected_filename="${artifact}-${selected_version}.jar"
	local selected_path="$LIB_DIRECTORY/$selected_filename"
	local candidate=''
	local filename=''

	if [[ "${STAGED_ARTIFACTS[$artifact_index]}" == '1' ]]
	then
		mv -- "${SELECTED_SOURCES[$artifact_index]}" "$selected_path" || fail "failed to install ${selected_filename}"
		SELECTED_SOURCES[$artifact_index]="$selected_path"
		report_added_file "$selected_filename"
	fi

	while IFS= read -r -d '' candidate
	do
		filename="${candidate##*/}"
		if [[ "$filename" =~ ^${artifact}-([0-9][0-9A-Za-z._+-]*)\.jar$ && "$candidate" != "$selected_path" ]]
		then
			rm -f -- "$candidate" || fail "failed to remove obsolete JAR: ${filename}"
			report_removed_file "$filename"
		fi
	done < <(find "$LIB_DIRECTORY" -mindepth 1 -maxdepth 1 -type f -name "${artifact}-*.jar" -print0)

	validate_jar "$selected_path" || fail "selected JAR is invalid: ${selected_filename}"
	append_dependency_path "$selected_filename"
}

downloadable_artifact_index()
{
	local wanted="$1"
	local artifact_index=0

	for ((artifact_index = 0; artifact_index < ${#DOWNLOADABLE_ARTIFACTS[@]}; ++artifact_index))
	do
		if [[ "${DOWNLOADABLE_ARTIFACTS[$artifact_index]}" == "$wanted" ]]
		then
			printf '%s\n' "$artifact_index"
			return 0
		fi
	done
	return 1
}

validate_log4j_selection()
{
	local api_index=''
	local core_index=''

	api_index="$(downloadable_artifact_index 'log4j-api')" || fail 'failed to locate log4j-api'
	core_index="$(downloadable_artifact_index 'log4j-core')" || fail 'failed to locate log4j-core'
	[[ "${SELECTED_VERSIONS[$api_index]}" == "${SELECTED_VERSIONS[$core_index]}" ]] || fail "selected Log4j versions are incompatible: api=${SELECTED_VERSIONS[$api_index]}, core=${SELECTED_VERSIONS[$core_index]}"
}

commit_fixed_artifact()
{
	local artifact="$1"
	local filename="${artifact}-2.0.0.jar"
	local path="$LIB_DIRECTORY/$filename"

	validate_jar "$path" || fail "required fixed JAR is missing or invalid: ${filename}"
	append_dependency_path "$filename"
}

verify_final_directory()
{
	local entry_count=0
	local entry=''

	validate_directory_entries
	while IFS= read -r -d '' entry
	do
		entry_count=$((entry_count + 1))
	done < <(find "$LIB_DIRECTORY" -mindepth 1 -maxdepth 1 -print0)
	[[ $entry_count -eq 12 ]] || fail "the final lib directory contains ${entry_count} entries instead of 12"
}

main()
{
	local artifact=''
	local artifact_index=0

	require_commands
	validate_directory_entries
	validate_jar "$LIB_DIRECTORY/jpbc-api-2.0.0.jar" || fail 'required fixed JAR is missing or invalid: jpbc-api-2.0.0.jar'
	validate_jar "$LIB_DIRECTORY/jpbc-plaf-2.0.0.jar" || fail 'required fixed JAR is missing or invalid: jpbc-plaf-2.0.0.jar'
	TEMPORARY_DIRECTORY="$(mktemp -d "$LIB_DIRECTORY/.fetchJavaDependencies.XXXXXX")" || fail 'failed to create the temporary directory'

	for ((artifact_index = 0; artifact_index < ${#DOWNLOADABLE_ARTIFACTS[@]}; ++artifact_index))
	do
		artifact="${DOWNLOADABLE_ARTIFACTS[$artifact_index]}"
		select_artifact_version "$artifact_index" "$artifact"
	done
	validate_log4j_selection

	for artifact in "${ORDERED_ARTIFACTS[@]}"
	do
		case "$artifact" in
		'jpbc-api'|'jpbc-plaf')
			commit_fixed_artifact "$artifact"
			;;
		*)
			artifact_index="$(downloadable_artifact_index "$artifact")" || fail "unknown downloadable artifact: ${artifact}"
			commit_downloadable_artifact "$artifact_index" "$artifact"
			;;
		esac
	done

	rm -rf -- "$TEMPORARY_DIRECTORY" || fail 'failed to remove the temporary directory'
	TEMPORARY_DIRECTORY=''
	verify_final_directory
	printf '%s\n' "$DEPENDENCY_PATHS"
	exit "$EXIT_SUCCESS"
}

main "$@"
