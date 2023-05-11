#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env -S bash -e

unset files_list
declare -A files_list

# formats commits that were not yet pushed
git_commits=($(git cherry -v origin/main | cut -c 3- | awk '{print $1}'))
for commit in "${git_commits[@]}"; do
  echo "commit ${commit}:"
  declare -a commit_files
  commit_files=($(git show --pretty=format: --name-only "${commit}"))
  for file in "${commit_files[@]}"; do
    echo "- ${file}"
    files_list["${file}"]="${file}"
  done
  echo
done

# list index and locally modified files
echo "staged, added and locally modified files:"
modified_files=($(git status --porcelain | grep -E '^( M|M|A)' | cut -c 4-))
for file in "${modified_files[@]}"; do
  echo "- ${file}"
  files_list["${file}"]="${file}"
done
echo

unset clang_format_files
declare -a clang_format_files
unset shell_check_files
declare -a shell_check_files
for file in "${!files_list[@]}"; do
  case "${file}" in
    *.cc | *.c | *.h | *.inl)
      clang_format_files+=("${file}")
      ;;

    *.sh)
      shell_check_files+=("${file}")
      ;;

    *)
      echo "skipping file format with unknown format: ${file}"
      ;;
  esac
done

if [[ "${#clang_format_files[@]}" -gt 0 ]]; then
  echo
  echo "-----------------------------------------"
  echo "files to be formatted using clang format:"
  for file in "${clang_format_files[@]}"; do
    echo "- ${file}"
  done
  echo
  while true; do
    echo -n "proceed? [y/n] "
    read -r answer
    case "${answer}" in
      y | Y | yes | Yes | YES)
        clang-format -i "${clang_format_files[@]}"
        break
        ;;
      n | N | no | No | NO)
        break
        ;;
    esac
  done
fi

if [[ "${#shell_check_files[@]}" -gt 0 ]]; then
  echo
  echo "-------------------------------------"
  echo "files to be checked using shellcheck:"
  for file in "${shell_check_files[@]}"; do
    echo "- ${file}"
  done
  echo
  while true; do
    echo -n "proceed? [y/n] "
    read -r answer
    case "${answer}" in
      y | Y | yes | Yes | YES)
        shellcheck -x "${shell_check_files[@]}"
        break
        ;;
      n | N | no | No | NO)
        break
        ;;
    esac
  done
fi
