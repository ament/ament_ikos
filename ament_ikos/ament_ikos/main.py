#!/usr/bin/env python3

# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import List
import xml.etree.ElementTree as ET

IKOS_MARKER_FILE_EXT = '.ikosbin'
IKOS_DB_FILE_EXT = '.ikosdb'


def indent(elem, level=0):
    """Use a low-budget method to format the XML to avoid bringing in another library (stack overflow #3095434)."""
    i = '\n' + level * '  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def scan_marker_files(directory: str) -> List[pathlib.Path]:
    """Return a list of marker files in a target directory."""
    def remove_cmake_compiler_test_files(path: pathlib.Path) -> bool:
        if '/CMakeFiles/' in str(path):
            return False
        else:
            return True

    return list(filter(remove_cmake_compiler_test_files, sorted(pathlib.Path(directory).glob('**/*' + IKOS_MARKER_FILE_EXT))))


def run_ikos(bitcode_path, ikos_db_path):
    """Run an IKOS analysis on a bitcode file."""
    # IKOS doesn't provide the report on stdout if there are > 15 items. So, use "--format no" here
    # to avoid generating a report to stdout here and we'll do it later using a separate ikos-report
    cmd = ['ikos', bitcode_path, '-o', ikos_db_path, '-q', '--format', 'no']

    rc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if rc.returncode != 0:
        print(
            'ikos analysis error: "' + ' '.join(cmd) +
            '" exited with return code ' + str(rc.returncode))
        print(rc.stdout)
        return False
    return True


def generate_ikos_stdout(ikos_db_path):
    """Run the IKOS report generator to print the issue list to stdout."""
    rc = subprocess.run(['ikos-report', ikos_db_path])
    if rc.returncode != 0:
        pass


def generate_ikos_report(ikos_db_path, fmt='junit', format_ext='junit.xml'):
    """Generate an IKOS report in one of the IKOS-supported formats (we use JUnit XML and SARIF)."""
    report_filename = f'{os.path.splitext(ikos_db_path)[0]}.{format_ext}'
    cmd = ['ikos-report', '--format', fmt, '--report-file', report_filename]

    # The target database must be the last argument, after the flags
    cmd.append(ikos_db_path)

    rc = subprocess.run(cmd)
    if rc.returncode != 0:
        pass


def process_marker_file(marker_file, args):
    """Generate the stdout as well as optional JUnit XML and SARIF output files."""
    with marker_file.open() as jsonf:
        data = json.load(jsonf)
        bc_path = data['bc']
        ikos_db_path = data['exe'] + IKOS_DB_FILE_EXT

        if run_ikos(bc_path, ikos_db_path):
            # Run the ikos reporting tool to generate the stdout for the issues
            generate_ikos_stdout(ikos_db_path)

            # Generate JUnit XML and SARIF files, as requested
            if args.xunit_file:
                generate_ikos_report(ikos_db_path, 'junit', 'junit.xml')
            if args.sarif_file:
                generate_ikos_report(ikos_db_path, 'sarif', 'sarif')

            return ikos_db_path
        else:
            print('Cannot generate report for ' + bc_path + ' due to analysis failure.')


def aggregate_junit_xml_files(ikos_db_filenames, summary_filename, summary_name):
    """Aggregate the JUnit XML files for each test into a single ikos.junit.xml file."""
    with open(summary_filename, 'wb') as xunit_file:
        # Wrap all of the concatenated XML output files with a <testsuites> element
        top = ET.Element('testsuites')

        # Counters to aggregate the test suite results for all test suites
        total_tests = 0
        total_errors = 0
        total_failures = 0
        total_time = 0.0

        # Set the attributes for the <testsuites> element
        top.attrib['name'] = summary_name

        # Handle the file that was output by IKOS for each test
        for db_filename in ikos_db_filenames:
            junit_xml_filename = os.path.splitext(db_filename)[0] + '.junit.xml'

            tree = ET.parse(junit_xml_filename)
            root = tree.getroot()

            # Replace the default testsuite name with the program name that was run under IKOS
            root.attrib['name'] = os.path.basename(os.path.splitext(db_filename)[0])

            # Work around a bug in the IKOS output where the failures are not reported correctly.
            # Instead of using the summary value, count the number of failure nodes.
            root.attrib['failures'] = str(len(root.findall('.//failure')))

            total_tests += int(root.attrib['tests'])
            total_errors += int(root.attrib['errors'])
            total_failures += int(root.attrib['failures'])
            total_time += float(root.attrib['time'])

            # Add the <testsuite> node to the parent <testsuites> node
            top.append(root)

        # Update summary fields for the top-level <testsuites>
        top.attrib['tests'] = str(total_tests)
        top.attrib['errors'] = str(total_errors)
        top.attrib['failures'] = str(total_failures)
        top.attrib['time'] = str(total_time)

        indent(top)
        xunit_file.write(ET.tostring(top, encoding='utf8', method='xml'))


def aggregate_sarif_files(ikos_db_filenames, summary_filename, summary_name):
    """Aggregate the SARIF files for each test into a single ikos.sarif file."""
    # TODO(mjeronimo): Write a function to aggregate the SARIF files
    pass


def main(argv=sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(
        description='Perform ikos analysis on files compiled with ikos-scan-cc / ikos-scan-c++.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'directory',
        default=os.curdir,
        help='Directory to scan recursively for ikos marker files.')
    parser.add_argument(
        '--xunit-file',
        help='Generate an xunit-compliant XML file')
    parser.add_argument(
        '--sarif-file',
        help='Generate a SARIF-compliant output file')
    args = parser.parse_args(argv)

    ikos_db_files = []

    # Scan for the marker files left by IKOS (*.ikosbin) in the target directory
    marker_files = scan_marker_files(args.directory)
    if not marker_files:
        print('No marker files found when scanning ' + args.directory)
        return 0

    # Process each one
    for m in marker_files:
        result = process_marker_file(m, args)
        if result:
            ikos_db_files.append(result)

    # Generate the output files
    test_name = f'{os.path.basename(args.directory)}.ikos'
    if args.xunit_file:
        aggregate_junit_xml_files(ikos_db_files, args.xunit_file, test_name)
    if args.sarif_file:
        aggregate_sarif_files(ikos_db_files, args.sarif_file, test_name)

    return 0


if __name__ == '__main__':
    sys.exit(main())
