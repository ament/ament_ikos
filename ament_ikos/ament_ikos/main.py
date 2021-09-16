import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

from typing import List


IKOS_MARKER_FILE_EXT = '.ikosbin'
IKOS_DB_FILE_EXT = '.ikosdb'


def scan_marker_files(directory: str) -> List[pathlib.Path]:
    """ Return a list of marker files in the current directory. """
    def remove_cmake_compiler_test_files(path: pathlib.Path) -> bool:
        if '/CMakeFiles/' in str(path):
            return False
        else:
            return True

    return filter(remove_cmake_compiler_test_files,
            sorted(pathlib.Path(directory).glob('**/*' + IKOS_MARKER_FILE_EXT)))


def run_ikos(bitcode_path, ikos_db_path):
    cmd = ['ikos', bitcode_path, '-o', ikos_db_path]
    rc = subprocess.run(cmd)
    if rc.returncode != 0:
        pass


def run_ikos_report(ikos_db_path):
    cmd = ['ikos-report', ikos_db_path]
    rc = subprocess.run(cmd)
    if rc.returncode != 0:
        pass

def main(argv=sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(
        description='Perform ikos analysis on files compiled with ikos-scan-cc / ikos-scan-c++.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'directory',
        default=os.curdir,
        help='Directory to scan recursively for ikos marker files.')
    args = parser.parse_args(argv)

    ikos_db_files = []
    marker_files = scan_marker_files(args.directory)
    if not marker_files:
        print('No marker files found when scanning ' + args.directory)
        return 0

    for m in marker_files:
        with m.open() as jsonf:
            data = json.load(jsonf)
            bc_path = data['bc']
            ikos_db_path = data['exe'] + IKOS_DB_FILE_EXT
            run_ikos(bc_path, ikos_db_path)
            run_ikos_report(ikos_db_path)
            ikos_db_files.append(ikos_db_path)

if __name__ == '__main__':
    sys.exit(main())
