# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_bash8
----------------------------------

Tests for `bash8` module.
"""

import mock

from bash8 import bash8

from bash8.tests import base


class TestBash8(base.TestCase):

    def setUp(self):
        super(TestBash8, self).setUp()

        # cleanup global IGNOREs
        def reset_ignores():
            bash8.IGNORE = None
        self.addCleanup(reset_ignores)

    def test_multi_ignore(self):
        bash8.register_ignores('E001|E011')
        bash8.check_no_trailing_whitespace("if ")
        bash8.check_if_then("if ")
        self.assertEqual(bash8.ERRORS, 0)

    def test_ignore(self):
        bash8.register_ignores('E001')
        bash8.check_no_trailing_whitespace("if ")
        self.assertEqual(bash8.ERRORS, 0)

    @mock.patch('bash8.bash8.print_error')
    def test_while_check_for_do(self, m_print_error):
        test_line = 'while `do something args`'
        bash8.check_for_do(test_line)

        m_print_error.assert_called_once_with(
            'E010: Do not on same line as while', test_line)


class TestBash8Samples(base.TestCase):
    """End to end regression testing of bash8 against script samples."""

    def setUp(self):
        super(TestBash8Samples, self).setUp()
        log_error_patcher = mock.patch('bash8.bash8.log_error')
        self.m_log_error = log_error_patcher.start()
        self.addCleanup(log_error_patcher.stop)

    def assert_error_found(self, error, lineno):
        error_found = False
        for call in self.m_log_error.call_args_list:
            # unwrap args
            args = call[0]
            if (args[0].startswith(error) and
                lineno == args[3]):
                error_found = True
        if not error_found:
            self.fail('Error %s expected at line %d not found!' %
                      (error, lineno))

    def test_sample_E001(self):
        test_file = 'bash8/tests/samples/E001_bad.sh'
        bash8.check_files(test_file, False)

        self.assert_error_found('E001', 4)

    def test_sample_E002(self):
        test_file = 'bash8/tests/samples/E002_bad.sh'
        bash8.check_files(test_file, False)

        self.assert_error_found('E002', 3)

    def test_pre_zero_dot_one_sample_file(self):
        """Test the sample file with all pre 0.1.0 release checks.

        This is a legacy compatibility check to make sure we still
        catch the same errors as we did before the first 0.1.0
        release of the bash8 pypi package. There were no tests
        before this, so it is our baseline regression check.

        New checks shouldn't need to be added here, and should
        have their own separate unit test and/or sample file checks.
        """

        test_file = 'bash8/tests/samples/legacy_sample.sh'
        bash8.check_files(test_file, False)

        # NOTE(mrodden): E012 actually requires iterating more than one
        # file to detect at the moment; this is bug
        expected_errors = [
            ('E002', 4),
            ('E003', 6),
            ('E001', 10),
            ('E010', 13),
            ('E010', 18),
            ('E010', 23),
            ('E011', 29),
            ('E020', 3)
        ]

        for error in expected_errors:
            self.assert_error_found(*error)
