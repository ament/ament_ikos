# copied from ament_cmake_ikos/ament_cmake_ikos-extras.cmake

find_package(ament_cmake_test QUIET REQUIRED)

include("${ament_cmake_ikos_DIR}/ament_ikos.cmake")

ament_register_extension("ament_lint_auto" "ament_cmake_ikos"
"ament_cmake_ikos_lint_hook.cmake")
