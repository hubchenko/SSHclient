
import re
import paramiko
import socket
from time import sleep

import logging
logger = logging.getLogger(__name__)

logging.getLogger('paramiko').setLevel(logging.CRITICAL)


def print_out(lines):
    """ print lines to screen
    """
    for line in lines:
        print line.rstrip()


class ConnectError(Exception):
    """ connection error
    """
    pass


class TimeOutError(ConnectError):
    """ timeout error
    """
    pass


class NotAuthorizedError(ConnectError):
    """ not authorized error
    """
    pass


class UnknownHostError(ConnectError):
    """ host unknown error
    """
    pass


class ExecuteError(Exception):
    """ execution error
    """
    pass


def generate_hostnames(hostname, domains):
    """ return hostnames
    """
    return ['{}{}'.format(hostname, domain) for domain in domains]


def connect(hostname, username, password, timeout, set_missing_host_key_policy=False):
    """ return ssh connection
    """
    try:
        ssh = paramiko.SSHClient()

        if set_missing_host_key_policy:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.debug('attempting to connect to: {}'.format(hostname))
        ssh.connect(hostname, username=username, password=password, timeout=timeout)
        logger.debug('successfully connected to: {}'.format(hostname))
        return ssh

    except socket.timeout:
        message = 'error connecting to: {} timed out after {} seconds'.format(hostname, timeout)
        logger.error(message)
        raise TimeOutError(message)

    except socket.gaierror:
        message = 'error connecting to: {} host is unknown'.format(hostname)
        logger.error(message)
        raise UnknownHostError(message)

    except paramiko.ssh_exception.AuthenticationException:
        message = 'error connecting to: {} authentication error for user {} credentials'.format(hostname, username)
        logger.error(message)
        raise NotAuthorizedError(message)

    except paramiko.ssh_exception.SSHException as exception:
        message = 'error connecting to: {} : {}'.format(hostname, str(exception))
        logger.error(message)
        raise ConnectError(message)


def check_success_responses(contents, success_responses):
    """ returns True if any success response in contents False otherwise
    """
    for success_response in success_responses:
        if '{regex}' in str(success_response):
            success_response_split = success_response.split('{regex}')
            match = success_response_split[1]
            logger.debug('checking regex {} in contents'.format(match))
            if re.match(match, contents, re.DOTALL):
                logger.debug('regex {} found in contents'.format(match))
                return True
        else:
            if str(success_response) in contents:
                logger.debug('success response {} found in contents'.format(success_response))
                return True
    return False


def _shell_receive(shell, lines):
    """ return data received from shell and data to lines
    """
    while not shell.recv_ready():
        sleep(.1)

    data = ''
    while shell.recv_ready():
        data += shell.recv(16348)

    lines += data.split('\r\n')
    return data


class SSHclient(object):

    def __init__(self, hostname, username, password, set_missing_host_key_policy=True, timeout=None, domains=None):
        """ class constructor
        """
        logger.debug('SSHclient constructor')

        if not timeout:
            timeout = 10

        if domains:
            hostnames = generate_hostnames(hostname, domains)
            for hostname in hostnames:
                try:
                    self.ssh = connect(hostname, username, password, timeout, set_missing_host_key_policy=set_missing_host_key_policy)
                    self.hostname = hostname
                    break

                except ConnectError:
                    continue
            else:
                raise ConnectError('unable to connect to any {} with domains {}'.format(hostname, domains))

        else:
            self.ssh = connect(hostname, username, password, timeout, set_missing_host_key_policy=set_missing_host_key_policy)
            self.hostname = hostname

        self.username = username

    def execute(self, command, send_input=None, success_responses=None, printout=False, expected_exit_code=None):
        """ execute ssh command against host
        """
        if not expected_exit_code:
            expected_exit_code = 0

        logger.debug('executing command "{}" on host {}'.format(command, self.hostname))
        stdin, stdout, stderr = self.ssh.exec_command(command)
        if send_input:
            logger.debug('sending stdin')
            stdin.write('{}\n'.format(send_input))
            stdin.flush()

        stdoutlines = stdout.readlines()
        stdout_contents = ''.join(stdoutlines)
        logger.debug('\r\n{}'.format(stdout_contents))
        if success_responses:
            logger.debug('checking stdout for success responses "{}"'.format(success_responses))
            if check_success_responses(stdout_contents, success_responses):
                return stdoutlines

            raise ExecuteError('success responses not found in stdout')

        exit_code = stdout.channel.recv_exit_status()
        if exit_code != expected_exit_code:
            error = ''.join(stderr.readlines()) + 'exit code: {}'.format(exit_code)
            raise ExecuteError(error)

        if printout:
            return print_out(stdoutlines)

        return stdoutlines

    def shell_execute(self, command, send_inputs, success_responses=None):
        """ execute ssh shell command with provided inputs
        """
        stdoutlines = []
        logger.debug('executing shell command "{}" on host {}'.format(command, self.hostname))

        shell = self.ssh.invoke_shell()
        _shell_receive(shell, stdoutlines)

        shell.send(command + '\n')
        _shell_receive(shell, stdoutlines)

        for send_input in send_inputs:
            shell.send(send_input + '\n')
            _shell_receive(shell, stdoutlines)

        _shell_receive(shell, stdoutlines)
        shell.close()

        logger.debug('\r\n'.join(stdoutlines))
        stdout_contents = ''.join(stdoutlines)
        if success_responses:
            logger.debug('checking stdout for success responses "{}"'.format(success_responses))
            if check_success_responses(stdout_contents, success_responses):
                return stdoutlines

            raise ExecuteError('success responses not found in stdout')

        return stdoutlines
