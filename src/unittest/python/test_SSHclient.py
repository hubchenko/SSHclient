
import unittest
from mock import patch
# from mock import mock_open
from mock import call
from mock import Mock
# from mock import PropertyMock

from SSHclient import SSHclient
from SSHclient import ExecuteError
from SSHclient import ConnectError
from SSHclient import TimeOutError
from SSHclient import NotAuthorizedError
from SSHclient import UnknownHostError
from SSHclient import print_out
from SSHclient import connect
from SSHclient import generate_hostnames
from SSHclient.sshclient import check_success_responses
from SSHclient.sshclient import _shell_receive

from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException
from socket import gaierror
from socket import timeout

import sys
import logging
logger = logging.getLogger(__name__)

consoleHandler = logging.StreamHandler(sys.stdout)
logFormatter = logging.Formatter(
    "%(asctime)s %(threadName)s %(name)s [%(funcName)s] %(levelname)s %(message)s")
consoleHandler.setFormatter(logFormatter)
rootLogger = logging.getLogger()
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)


class TestSSHclient(unittest.TestCase):

    def setUp(self):
        """
        """
        pass

    def tearDown(self):
        """
        """
        pass

    @patch('SSHclient.sshclient.generate_hostnames')
    @patch('SSHclient.sshclient.connect', return_value='ssh connection')
    def test__init__Should_SetAttributes_When_Called(self, *patches):
        client = SSHclient('server', 'username', 'password')
        self.assertEqual(client.hostname, 'server')
        self.assertEqual(client.username, 'username')
        self.assertEqual(client.ssh, 'ssh connection')

    @patch('SSHclient.sshclient.generate_hostnames', return_value=['host1.vcff1.cps.intel.com', 'host1.vcff2.cps.intel.com'])
    @patch('SSHclient.sshclient.connect')
    def test__init_Should_RaiseConnectError_When_DomainsConnectError(self, connect, *patches):
        connect.side_effect = [
            ConnectError('connect error'),
            ConnectError('connect error'),
            ConnectError('connect error')
        ]
        with self.assertRaises(ConnectError):
            SSHclient('host1', 'value', 'value', domains=['vcff1.cps.intel.com', 'vcff2.cps.intel.com'])

    @patch('SSHclient.sshclient.generate_hostnames', return_value=['host1.vcff1.cps.intel.com', 'host1.vcff2.cps.intel.com'])
    @patch('SSHclient.sshclient.connect')
    def test__init_Should_SetSshHostname_When_HostnameDomainsConnect(self, connect, *patches):
        ssh_mock = Mock()
        connect.side_effect = [
            ConnectError('connect error'),
            ssh_mock
        ]
        client = SSHclient('host1', 'value', 'value', domains=['vcff1.cps.intel.com', 'vcff2.cps.intel.com'])
        self.assertEqual(client.hostname, 'host1.vcff2.cps.intel.com')
        self.assertEqual(client.ssh, ssh_mock)

    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_RaiseExecutionError_When_SshExecCodeNonZero(self, connect, *patches):
        mock_stderr = Mock()
        mock_stderr.readlines.return_value = ['error']
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = []
        mock_stdout.channel.recv_exit_status.return_value = 1

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('server', 'username', 'password')

        with self.assertRaises(ExecuteError):
            client.execute('command')

    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_RaiseExecutionError_When_SshExecCodeNotExpected(self, connect, *patches):
        mock_stderr = Mock()
        mock_stderr.readlines.return_value = ['error']
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = []
        mock_stdout.channel.recv_exit_status.return_value = 3

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('server', 'username', 'password')

        with self.assertRaises(ExecuteError):
            client.execute('command', expected_exit_code=1)

    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_Succeed_When_SshExecCodeExpected(self, connect, *patches):
        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['some output']
        mock_stdout.channel.recv_exit_status.return_value = 3

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('server', 'username', 'password')

        result = client.execute('command', expected_exit_code=3)
        self.assertEqual(result, ['some output'])

    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_ReturnStdoutLines_When_SshExecReturnsStdoutLines(self, connect, *patches):
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['output']
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('server', 'username', 'password')
        result = client.execute('command')
        expected_result = ['output']

        self.assertEqual(result, expected_result)

    @patch('SSHclient.sshclient.print_out')
    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_PrintStdoutLines_When_SshExecReturnsStdoutLinesAndPrintoutTrue(self, connect, print_out, *patches):
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['output']
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('server', 'username', 'password')
        client.execute('command', printout=True)

        self.assertTrue(print_out.called)

    @patch('SSHclient.sshclient.check_success_responses', return_value=False)
    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_RaiseExcecuteError_When_CheckSuccessResponsesReturnsFalse(self, connect, *patches):
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['nobs']

        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        with self.assertRaises(ExecuteError):
            client.execute('myfakecommand', success_responses=['bs1', 'bs2'])

    @patch('SSHclient.sshclient.check_success_responses', return_value=True)
    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_ReturnStdoutLines_When_CheckSuccessResponsesReturnsTrue(self, connect, *patches):
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['bs1', 'nobs']

        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = None, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        result = client.execute('myfakecommand', success_responses=['bs1', 'bs2'])
        expected_result = ['bs1', 'nobs']
        self.assertEqual(expected_result, result)

    @patch('SSHclient.sshclient.check_success_responses', return_value=True)
    @patch('SSHclient.sshclient.connect')
    def test__execute_Should_WriteStdin_When_SendInputProvided(self, connect, *patches):
        mock_stdout = Mock()
        mock_stdout.readlines.return_value = ['success']

        mock_stderr = Mock()
        mock_stderr.readlines.return_value = []

        mock_stdin = Mock()

        ssh_mock = Mock()
        ssh_mock.exec_command.return_value = mock_stdin, mock_stdout, mock_stderr
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        client.execute('command', send_input='YES', success_responses=['success'])

        self.assertEqual(mock_stdin.write.mock_calls[0], call('YES\n'))
        self.assertTrue(mock_stdin.flush.called)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_RaiseConnectionError_When_ParamikoRaisesSSHException(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client_mock.connect.side_effect = [
            SSHException('ssh exception')
        ]
        ssh_client.return_value = ssh_client_mock

        with self.assertRaises(ConnectError):
            connect('hostname', 'username', 'password', 5)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_RaiseTimeOutError_When_SocketTimeoutException(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client_mock.connect.side_effect = [
            timeout('timeout')
        ]
        ssh_client.return_value = ssh_client_mock

        with self.assertRaises(TimeOutError):
            connect('hostname', 'username', 'password', 5)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_RaiseNotAuthorizedError_When_ParamikoRaisesAuthenticationException(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client_mock.connect.side_effect = [
            AuthenticationException('ssh exception')
        ]
        ssh_client.return_value = ssh_client_mock

        with self.assertRaises(NotAuthorizedError):
            connect('hostname', 'username', 'password', 5)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_RaiseUnknownHostError_When_SocketGaierror(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client_mock.connect.side_effect = [
            gaierror('gaierror')
        ]
        ssh_client.return_value = ssh_client_mock

        with self.assertRaises(UnknownHostError):
            connect('hostname', 'username', 'password', 5)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_ReturnSSHConnect_When_NoException(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client_mock.connect.return_value = 'ssh connect'
        ssh_client.return_value = ssh_client_mock

        result = connect('hostname', 'username', 'password', 5)
        expected_result = ssh_client_mock
        self.assertEqual(result, expected_result)

    @patch('SSHclient.sshclient.paramiko.SSHClient')
    def test__connect_Should_SetMissingHostKeyPolicy_When_SetMissingHostKeyPolicyIsSpecified(self, ssh_client, *patches):
        ssh_client_mock = Mock()
        ssh_client.return_value = ssh_client_mock

        connect('server', 'username', 'password', 5, set_missing_host_key_policy=False)
        self.assertFalse(ssh_client_mock.set_missing_host_key_policy.called)

        connect('server', 'username', 'password', 5, set_missing_host_key_policy=True)
        self.assertTrue(ssh_client_mock.set_missing_host_key_policy.called)

    def test__generate_hostnames_Should_ReturnHostnamesList_When_Called(self, *patches):
        result = generate_hostnames('hostname', ['.cps.intel.com', '.fm.intel.com'])
        expected_result = ['hostname.cps.intel.com', 'hostname.fm.intel.com']
        self.assertEqual(result, expected_result)

    def test__print_out_Should_CallPrint_When_Called(self, *patches):

        print_out(['line1', 'line2'])

    def test__check_success_responses_Should_ReturnFalse_When_SucessResponseNotFoundInContents(self, *patches):
        contents = """
        this is some contents
        """
        success_responses = [
            'emilio',
            'reyes'
        ]
        self.assertFalse(check_success_responses(contents, success_responses))

    def test__check_success_responses_Should_ReturnTrue_When_SucessResponseFoundInContents(self, *patches):
        contents = """
        this is some contents
        """
        success_responses = [
            'emilio',
            'reyes',
            'some contents'
        ]
        self.assertTrue(check_success_responses(contents, success_responses))

    def test__check_success_responses_Should_ReturnTrue_When_SucessResponseRegexMatchContents(self, *patches):
        contents = """
        and some up here
        this is some contents items=231 cached=231 and some more contents afterwards
        and some down here
        """
        success_responses = [
            'emilio',
            'reyes',
            '{regex}.*items=[1-9][0-9]* cached=[1-9][0-9]*.*'
        ]
        self.assertTrue(check_success_responses(contents, success_responses))

    def test__check_success_responses_Should_ConvertSuccessResponseToStr_When_Comparing(self, *patches):
        contents = """
        this is some contents 14.04 and more
        contents here
        """
        success_responses = [
            'emilio',
            'reyes',
            14.04,
            'some contents'
        ]
        self.assertTrue(check_success_responses(contents, success_responses))

    @patch('SSHclient.sshclient.sleep')
    def test__shell_receive_Should_CallSleep_When_ShellRecvReadyReturnsFalse(self, sleep, *patches):
        shell_mock = Mock()
        shell_mock.recv_ready.side_effect = [
            False,
            False,
            True,
            True,
            True,
            False
        ]
        shell_mock.recv.side_effect = [
            'data1\r\n',
            'data2\r\n'
        ]
        lines = [
            'data0'
        ]
        _shell_receive(shell_mock, lines)
        self.assertEqual(len(sleep.mock_calls), 2)

    @patch('SSHclient.sshclient.sleep')
    def test__shell_receive_Should_ReturnAppendedRecv_When_ShellRecvReady(self, sleep, *patches):
        shell_mock = Mock()
        shell_mock.recv_ready.side_effect = [
            False,
            False,
            True,
            True,
            True,
            False
        ]
        shell_mock.recv.side_effect = [
            'data1\r\n',
            'data2\r\n'
        ]
        lines = [
            'data0'
        ]
        result = _shell_receive(shell_mock, lines)
        expected_result = 'data1\r\ndata2\r\n'
        self.assertEqual(result, expected_result)
        expected_lines = [
            'data0',
            'data1',
            'data2',
            ''
        ]
        self.assertEqual(lines, expected_lines)

    @patch('SSHclient.sshclient.sleep')
    def test__shell_receive_Should_AppendRecvToLines_When_ShellRecvReady(self, sleep, *patches):
        shell_mock = Mock()
        shell_mock.recv_ready.side_effect = [
            False,
            False,
            True,
            True,
            True,
            False
        ]
        shell_mock.recv.side_effect = [
            'data1\r\n',
            'data2\r\n'
        ]
        lines = [
            'data0'
        ]
        _shell_receive(shell_mock, lines)
        expected_lines = [
            'data0',
            'data1',
            'data2',
            ''
        ]
        self.assertEqual(lines, expected_lines)

    @patch('SSHclient.sshclient.check_success_responses', return_value=True)
    @patch('SSHclient.sshclient._shell_receive')
    @patch('SSHclient.sshclient.connect')
    def test__shell_execute_Should_SendCommand_When_Called(self, connect, *patches):
        ssh_mock = Mock()
        shell_mock = Mock()
        ssh_mock.invoke_shell.return_value = shell_mock
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        client.shell_execute('command', send_inputs=['YES', 'NO', 'YES'], success_responses=['Successfully processed'])

        self.assertEqual(shell_mock.send.mock_calls[0], call('command\n'))

    @patch('SSHclient.sshclient.check_success_responses', return_value=True)
    @patch('SSHclient.sshclient._shell_receive')
    @patch('SSHclient.sshclient.connect')
    def test__shell_execute_Should_SendInput_When_Called(self, connect, *patches):
        ssh_mock = Mock()
        shell_mock = Mock()
        ssh_mock.invoke_shell.return_value = shell_mock
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        client.shell_execute('command', send_inputs=['YES', 'NO', 'MAYBE'], success_responses=['Successfully processed'])

        self.assertEqual(shell_mock.send.mock_calls[1], call('YES\n'))
        self.assertEqual(shell_mock.send.mock_calls[2], call('NO\n'))
        self.assertEqual(shell_mock.send.mock_calls[3], call('MAYBE\n'))

    @patch('SSHclient.sshclient.check_success_responses', return_value=False)
    @patch('SSHclient.sshclient._shell_receive')
    @patch('SSHclient.sshclient.connect')
    def test__shell_execute_Should_RaiseExecuteError_When_SuccessResponsesPassedAndCheckSuccessResponseReturnsFalse(self, connect, *patches):
        ssh_mock = Mock()
        shell_mock = Mock()
        ssh_mock.invoke_shell.return_value = shell_mock
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        with self.assertRaises(ExecuteError):
            client.shell_execute('command', send_inputs=['YES', 'NO', 'MAYBE'], success_responses=['Successfully processed'])

    @patch('SSHclient.sshclient.check_success_responses', return_value=True)
    @patch('SSHclient.sshclient._shell_receive')
    @patch('SSHclient.sshclient.connect')
    def test__shell_execute_Should_ReturnLines_When_SuccessResponsesNotSpecified(self, connect, *patches):
        ssh_mock = Mock()
        shell_mock = Mock()
        ssh_mock.invoke_shell.return_value = shell_mock
        connect.return_value = ssh_mock

        client = SSHclient('hostname', 'user', 'password')
        result = client.shell_execute('command', send_inputs=['YES', 'NO', 'MAYBE'])
        expected_result = []
        self.assertEqual(result, expected_result)
