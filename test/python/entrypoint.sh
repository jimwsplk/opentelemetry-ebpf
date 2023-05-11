#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


function cleanup {
	echo "Cleaning up..."
	echo "$exit_code"
	###########################################
	#
	# Cleanup bits to clean/remove all container/images
	#  - first stop all running containers (if any),
	#  - remove containers
	#  - remove images
	#  - remove volumes
	#

	# stop all running containers
	echo '####################################################'
	echo 'Stopping running containers (if available)...'
	echo '####################################################'
	# shellcheck disable=SC2046
	docker stop $(docker ps -aq) 2> /dev/null

	# remove all stopped containers
	echo '####################################################'
	echo 'Removing containers ..'
	echo '####################################################'
	# shellcheck disable=SC2046
	docker rm $(docker ps -aq)  2> /dev/null


	# remove all images
	echo '####################################################'
	echo 'Removing images ...'
	echo '####################################################'
	# shellcheck disable=SC2046
	docker rmi $(docker images -q) 2> /dev/null

	# remove all stray volumes if any
	echo '####################################################'
	echo 'Removing docker container volumes (if any)'
	echo '####################################################'
 	# shellcheck disable=SC2046
	docker volume rm $(docker volume ls -q) 2> /dev/null
 	sudo lsof -t -i:8080
 	exit
}

trap cleanup EXIT INT TERM


ROOT_DIR="$(pwd)"

EBPF_NET_OUT_DIR="${EBPF_NET_OUT_DIR:-${ROOT_DIR}/out}"

TEST_DIR="${TEST_DIR:-${ROOT_DIR}/tests}"

declare -A all_tests
all_tests=()

# discover tests
for test_script in "${TEST_DIR}"/*.py; do
  test_name="$(basename "${test_script}" .py)"
  all_tests[${test_name}]="${test_name}"
done

function print_help {
  echo "available test cases:"
  for test_name in "${all_tests[@]}"; do
    echo "- ${test_name}"
  done
}

exit_code=0

function run_test {
  test_name="$1"; shift
  test_script="${TEST_DIR}/${test_name}.py"

  if [[ ! -e "${test_script}" ]]; then
    echo "ERROR: can't find test '${test_name}' under '${test_script}'"
    exit 1
  fi

  mkdir -p "${EBPF_NET_OUT_DIR}"

  echo ">> running test '${test_name}' ---------------------------------------------"

  test_exit_code="0"
  PYTHONPATH="${ROOT_DIR}" pytest-3 -p no:cacheprovider "${test_script}" \
    || test_exit_code="$?"
  echo "${test_exit_code}" > "${EBPF_NET_OUT_DIR}/${test_name}.exit"

  [[ "${test_exit_code}" -eq 0 ]] || exit_code="${test_exit_code}"

  echo "<< test '${test_name}' finished with code ${test_exit_code} ================"
}

# parse args
[[ "$#" -gt 0 ]] || (print_help; exit 1)
unset test_list; declare -A test_list; test_list=()
while [[ "$#" -gt 0 ]]; do
  arg="$1"; shift

  case "${arg}" in
    \*)
      for test_name in "${all_tests[@]}"; do
        test_list[${test_name}]="${test_name}"
      done
      ;;

    *)
      test_list[${arg}]="${arg}"
      ;;
  esac
done

# run tests
echo "tests to run:" "${!test_list[@]}"
echo
for test_name in "${!test_list[@]}"; do
  run_test "${test_name}"
done

