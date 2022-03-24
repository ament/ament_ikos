function(ament_ikos)
  cmake_parse_arguments(ARG "" "TESTNAME" "" ${ARGN})
  if(NOT ARG_TESTNAME)
    set(ARG_TESTNAME "ikos")
  endif()

  find_program(ament_ikos_BIN NAMES "ament_ikos")
  if(NOT ament_ikos_BIN)
    message(FATAL_ERROR "ament_ikos() variable 'ament_ikos_BIN' must not be empty")
  endif()

  set(junit_file "${AMENT_TEST_RESULTS_DIR}/${PROJECT_NAME}/${ARG_TESTNAME}.xunit.xml")
  set(sarif_file "${AMENT_TEST_RESULTS_DIR}/${PROJECT_NAME}/${ARG_TESTNAME}.sarif")

  set(cmd "${ament_ikos_BIN}" "--xunit-file" "${junit_file}" "--sarif-file" "${sarif_file}")
  list(APPEND cmd ${ARG_UNPARSED_ARGUMENTS})

  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ament_ikos")
  ament_add_test(
    "${ARG_TESTNAME}"
    COMMAND ${cmd}
    OUTPUT_FILE "${CMAKE_BINARY_DIR}/ament_ikos/${ARG_TESTNAME}.txt"
    RESULT_FILE "${junit_file}"
    WORKING_DIRECTORY "${CMAKE_BINARY_DIR}"
  )
  set_tests_properties(
    "${ARG_TESTNAME}"
    PROPERTIES
    LABELS "ikos;linter"
  )
endfunction()

