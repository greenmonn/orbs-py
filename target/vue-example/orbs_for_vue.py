#!/usr/bin/env python

import io
import os
import sys
import re
import copy
import time
import subprocess

import argparse

criteria_text = r'✓ renders the correct message'
component_path = 'src/components/HelloWorld.vue'


class Path():
    def __init__(self, target_file_path):
        working_directory, file_name = os.path.split(target_file_path)

        self.working_directory = working_directory

        self.temp_file_name = '{}_orbs.vue'.format(file_name[:-4])
        self.criteria_file_name = 'criteria.txt'

        self.result_path = "slices{}/".format(str(time.time()))

    def get_temp_file_path(self):
        return os.path.join(self.working_directory, self.temp_file_name)

    def get_criteria_filepath(self):
        return os.path.join(self.working_directory, self.criteria_file_name)

    def get_result_path(self):
        return os.path.join(self.working_directory, self.result_path)


class ORBSlicer():
    def __init__(self):
        self.MAX_DEL_WINDOW_SIZE = 3
        self.use_pytest = False

        """
        Criteria
        """
        self.target_location = -1    # line number
        self.original_value = None

        """
        Code Object
        """
        self.program_lines = None
        self.program_lines_before = None    # for reverting of failing slice
        self.program_lines_original = None
        self.arguments = None

        """
        File Path
        """
        self.filepath = None
        self.temp_filepath = None
        self.criteria_filepath = None

    def set_pytest(self):
        self.use_pytest = True

    def setup(self, filepath, arguments):
        component_path = 'src/components/HelloWorld.vue'
        _, component_name = os.path.split(component_path)
        component_name = component_name[:-4]

        self.path = Path(component_path)
        self.filepath = filepath
        self.target_filepath = component_path
        self.temp_filepath = self.path.get_temp_file_path()
        self.criteria_filepath = self.path.get_criteria_filepath()
        self.test_filepath = '{}_orbs.spec.js'.format(filepath[:-8])

        program_lines = self._read_source_file(self.target_filepath)
        test_lines = self._read_source_file(self.filepath)

        code_str = ''.join(test_lines)
        code_str = code_str.replace(
            component_name, '{}_orbs'.format(component_name))
        with open(self.test_filepath, 'w+') as f:
            f.write(code_str)

        for i, arg in enumerate(arguments):
            if arg.find('./') >= 0:
                arguments[i] = arg.replace(
                    './', self.path.working_directory + '/')

        for i, l in enumerate(program_lines):
            if l.find('./') >= 0:
                program_lines[i] = l.replace(
                    './', self.path.working_directory + '/')

        self.arguments = arguments
        self.program_lines = program_lines
        self.program_lines_original = copy.deepcopy(
            self.program_lines)  # fixed

    def _read_source_file(self, filepath):
        # TODO: multiple files
        with open(filepath) as f:
            program_lines = f.readlines()

            return program_lines

    def _write_code_to_file(self, filepath=None):
        if filepath == None:
            filepath = self.temp_filepath

        try:
            os.makedirs(os.path.dirname(filepath))
        except FileExistsError:
            pass

        code_str = ''.join(self.program_lines)
        with open(filepath, 'w+') as f:
            f.write(code_str)

    def _execute_program(self):
        os.environ['PATH'] = ':'.join(
            [os.getenv('PATH'), self.path.working_directory])
        argv = ['jest', '--verbose', self.test_filepath, '--config']
        argv.extend(self.arguments)

        with open(self.temp_filepath, 'w') as f:
            code_str = ''.join(self.program_lines)
            f.write(code_str)

        output = None

        completed_process = subprocess.run(
            argv, capture_output=True)

        output = completed_process.stderr
        output = output.decode('utf-8')

        regex = re.compile(criteria_text)
        matches = regex.findall(output)

        if len(matches) > 0:
            print('Criteria Met!')
            return True

        return False

    def _compile_program(self):
        # TODO: connect with babel
        code_str = ''.join(self.program_lines)
        try:
            code = compile(code_str, 'orbs_target.py', 'exec')

        except SyntaxError as err:
            error_class = err.__class__.__name__
            detail = err.args[0]
            line_number = err.lineno
        else:
            with open(self.temp_filepath, 'w') as f:
                f.write(code_str)

            return True

        print(("%s at line %d of source string: %s" %
               (error_class, line_number, detail)))

        return False

    def _check_criteria(self):
        # check target variable at target location is identical to the original
        if not os.path.isfile(self.criteria_filepath):
            return False

        has_same_value = False
        with open(self.criteria_filepath) as f:
            value = f.read()
            if value == self.original_value:
                has_same_value = True
                # What if type is mismatched? compare in byte-level?

        if has_same_value:
            os.remove(self.criteria_filepath)
            return True

        return False

    def _delete_lines(self, start, end):
        # TODO: consider indentation level
        s = len(self.program_lines) - 1 - end
        e = len(self.program_lines) - 1 - start

        print('* * * attempt to delete {} to {}'.format(s, e))
        assert s <= e
        assert s >= 0 and e >= 0

        del self.program_lines[s:e+1]

    def do_slicing(self):
        self.program_lines = copy.deepcopy(self.program_lines_original)
        deleted = False

        # self._compile_program()
        self._execute_program()

        # print('* Original Value for Criteria: ', self.original_value)

        while not deleted:  # until nothing can be deleted
            i = 0
            success_count = 0
            buildfail_count = 0
            execfail_count = 0

            while i < len(self.program_lines):
                builds = False
                print('* * {}th iterations'.format(i))

                self.program_lines_before = copy.deepcopy(
                    self.program_lines)

                for j in range(0, self.MAX_DEL_WINDOW_SIZE):
                    self._delete_lines(
                        # TODO: why i becomes len(self.program_lines)
                        # when we attempt to delete 0 to 0? (behave like 0 to -1)
                        min(i, len(self.program_lines)-1), min(i+j, len(self.program_lines)-1))

                    # builds = self._compile_program()
                    builds = True
                    if builds:
                        # print('build success: window size {}'.format(j+1))
                        break

                if builds:
                    execute_success = self._execute_program()
                    if execute_success:
                        deleted = True
                        self._write_code_to_file(
                            os.path.join(self.path.get_result_path(), 'success/success_{}_{}.py'.format(
                                i, success_count)))
                        success_count += 1

                    else:
                        self._write_code_to_file(
                            os.path.join(self.path.get_result_path(), 'execfail/execfail_{}_{}.py'.format(
                                i, execfail_count)))
                        execfail_count += 1

                        self.program_lines = copy.deepcopy(
                            self.program_lines_before)

                        i += 1
                        success_count = 0
                        buildfail_count = 0
                        execfail_count = 0

                else:
                    self._write_code_to_file(
                        os.path.join(self.path.get_result_path(), 'buildfail/buildfail_{}_{}.py'.format(
                            i, buildfail_count)))
                    buildfail_count += 1

                    self.program_lines = copy.deepcopy(
                        self.program_lines_before)

                    i += 1
                    success_count = 0
                    buildfail_count = 0
                    execfail_count = 0


def main():
    argv = []

    if sys.argv[0] == 'python':
        argv = sys.argv[2:]
    else:
        argv = sys.argv[1:]

    orbs = ORBSlicer()

    filepath, arguments = 'tests/unit/helloworld.spec.js', []

    if len(argv) > 0:
        filepath = argv[0]
        arguments = argv[1:]

    print('Target Component: ', component_path)
    print('Running Test: ', filepath)
    print('Arguments: ', arguments)

    orbs.setup(filepath, arguments)
    orbs.do_slicing()


if __name__ == "__main__":
    main()
