#!/usr/bin/env python3

import os
import time
import argparse
import getpass
import textwrap
import json
import sys
import signal
import errno
import logging

from py3270 import Emulator, CommandError
from time import sleep
from multiprocessing import TimeoutError
from functools import wraps

# return codes
ALL_FINE = 0
NO_LOGON_SCREEN = 1
WRONG_ID_OR_PW = 2
LOGON_FAILED = 3
ALREADY_LOGGED_ON = 4
RESET_FAILED = 5
SSL_HANDSHAKE_ERROR = 6
CONNECTION_FAILED = 7
LOGFILE_PATH_ERROR = 8
ENVIRONMENT_CREDENTIALS_NOT_SET = 9
NO_CREDENTIALS = 10

CMSAPIExceptionMessages = {
    NO_LOGON_SCREEN: 'Logon screen not found.',
    WRONG_ID_OR_PW: 'LOGON unsuccessful. Incorrect userid and/or password.',
    LOGON_FAILED: 'LOGON unsuccessful',
    ALREADY_LOGGED_ON: 'The user is already logged on.',
    SSL_HANDSHAKE_ERROR: '. Please try again with the option \
                        --no-certificate-verification',
    CONNECTION_FAILED: '. Could not connect to the host.',
    LOGFILE_PATH_ERROR: 'The directory provided for the logfile \
                        does not exist.',
    ENVIRONMENT_CREDENTIALS_NOT_SET: 'The environment username and/or \
                        password are not set',
    NO_CREDENTIALS: 'No credentials have been provided.'}

HCP_ALREADY_LOGGED_ON = 'HCPLGA054E'


class TimeoutSignal(Exception):
    pass


class CMSAPIException(Exception):
    def __init__(self, error_code=None, additional_message=None):
        self.message = ''
        if additional_message is not None:
            self.message = additional_message
        if error_code is None:
            super().__init__()
        else:
            self.message = self.message + CMSAPIExceptionMessages[error_code]
            super().__init__(self.message)


def print_to_terminal(message, quiet):

    if message is None:
        return
    if quiet is False:
        print(message)
        return


def timeout(seconds=300, error_message=os.strerror(errno.ETIMEDOUT)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutSignal(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def file_parser(fileloc=None):
    '''
    The fileloc is treated either as a relative or an absolute path.
    '''

    if fileloc is None:
        raise RuntimeError("There was no file name passed as an argument.")

    dpath = os.path.normpath(fileloc)
    commands = []

    try:
        with open(dpath) as data_file:
            commands = data_file.readlines()
            return commands
    except IOError as err:
        # log the message and check what is printed
        logging.error(err)


class expandedEmulator(Emulator):

    def send_pf10(self):
        self.exec_command(b'PF(10)')

    def send_pa1(self):
        self.exec_command(b'PA(1)')

    def send_clear(self):
        self.exec_command(b'CLEAR')

    def save_screen_string(self):
        s = self.exec_command(b'PrintText(string)')
        for i in range(len(s.data)):
            s.data[i] = s.data[i].decode('utf-8')
        return s

    def return_screen(self):
        s = self.save_screen_string()  # s is an instant of the Command class
        for i in range(len(s.data)):
            # the data field is an array. Each element is a string
            # that represents one line of the screen
            print(str(i) + '   -   ' + s.data[i])
        return s

    def screen_parser(self, quiet=False):
        s = self.save_screen_string()
        non_empty = list(filter(len, s.data))
        if not quiet:
            for i in range(len(non_empty) - 2):
                # the data field is an array. Each element is a string
                # that represents one line of the screen
                print(non_empty[i])
        return non_empty[0:-1]


class console(object):

    @timeout(seconds=120)
    def __init__(self, args_dict, username, password):
        '''
        The flag attribute is for debugging purposes.
        It can be either 0 or 1.
        0 means the debugging option is completely deactivated.
        1 means that a 3270 window will be opened, allowing the user
          to see how the command execution progresses.
          CAREFUL: Before setting the debug flag to 1, make sure that
          you have installed the necessary libraries,
          or else an error message will appear.
        '''

        # self.flag = 0

        self.args = args_dict
        self.__username = username
        self.__password = password

        if self.args['no_certificate_verification'] is True:
            host = 'y:' + self.args['host']
        else:
            host = self.args['host']

        if self.args['console_on'] is True:
            self.em = expandedEmulator(visible=True)
        else:
            self.em = expandedEmulator()

        time.sleep(1)
        try:
            self.em.connect(host)
        except CommandError as err:
            if 'SSLHandshake' in str(err):
                raise CMSAPIException(
                    error_code=SSL_HANDSHAKE_ERROR,
                    additional_message=str(err))
            else:
                raise CMSAPIException(
                    error_code=CONNECTION_FAILED, additional_message=str(err))

        print_to_terminal(
            'Connection to the 3270 console succeeded. \n', self.args['quiet'])
        logging.info('Connection to the 3270 console succeeded.')

        self.em.screen_parser(quiet=self.args['quiet'])

    def reset(self):

        self.em.send_pa1()
        self.em.send_string('i zcms')
        self.em.send_enter()
        time.sleep(1)
        self.em.send_enter()
        time.sleep(1)

        i = 1
        while not self.findString(string='Ready;') and i < 5:
            time.sleep(1)
        s = self.em.screen_parser(quiet=self.args['quiet'])
        if self.args['logfile'] is not None:
            logging.debug(s)

    @timeout(seconds=60)
    def find_logon_screen(self):
        # Check we are in the correct screen
        found = False
        try:
            while not found:
                found = self.findString(string="USERID")
            return ALL_FINE
        except TimeoutSignal:
            print_to_terminal('Logon screen not found.', self.args['quiet'])
            if self.args['logfile'] is not None:
                logging.error('Logon screen not found.')
            return NO_LOGON_SCREEN

    def logon(self):
        print_to_terminal(
            'logon function called. \n', self.args['quiet'])
        # Check we are in the correct screen
        check = self.find_logon_screen()
        if check != 0:
            return check

        self.em.send_enter()
        self.em.send_string('logon ' + self.__username)
        self.em.send_enter()
        time.sleep(1)
        self.em.send_string(self.__password)
        self.em.send_enter()
        time.sleep(1)

        if self.findString(string=HCP_ALREADY_LOGGED_ON):
            s = self.em.screen_parser(quiet=self.args['quiet'])
            if self.args['logfile'] is not None:
                logging.error(s)
            return ALREADY_LOGGED_ON
        if self.findString(string='incorrect userid and/or password'):
            s = self.em.screen_parser(quiet=self.args['quiet'])
            if self.args['logfile'] is not None:
                logging.error(s)
            return WRONG_ID_OR_PW
        if self.findString(string='LOGON unsuccessful'):
            s = self.em.screen_parser(quiet=self.args['quiet'])
            if self.args['logfile'] is not None:
                logging.error(s)
            return LOGON_FAILED
        print_to_terminal('LOGON successful.', self.args['quiet'])
        logging.info('LOGON successful.')
        self.reset()

        return ALL_FINE

    # @timeout(seconds=5)
    def findStatus(self, status=None):

        if status is None:
            raise Exception(
                "No status was given as input in the findStatus method.")

        found = False
        s = self.em.save_screen_string()
        if s.data[len(s.data) - 1].find(status) != -1:
            found = True
        return found

    # @timeout(seconds=5)
    def findString(self, string=None, status=None):
        '''
        string is the primary string we are looking to find in the screen
        status is a secondary and optional string that we are looking for
                in the last line of the screen
        '''

        if string is None:
            raise Exception(
                "No string was given as input in the findString method.")

        time.sleep(1)
        s = self.em.save_screen_string()
        for i in range(len(s.data)):
            if s.data[i].find(string) != - \
                    1:  # need to adjust here for findStatus
                if status is not None:
                    try:
                        found = self.findStatus(status=status)
                    except TimeoutSignal:
                        pass
                    if found:
                        return found
                else:
                    found = True
                    return found

    def execute_all(self, commands=None):

        if commands is None or commands == []:
            raise Exception(
                'No commands have been passed in the execute_all method.')

        for c in commands:
            self.execute_command(c.rstrip())

        return

    @timeout(seconds=60)  # will have to be replaced by other kind of timeout
    def execute_command(self, command=None):

        self.em.send_clear()
        if command is None or command == [] or command == '':
            raise Exception(
                'No commands have been passed in the execute_command method.')
        self.em.send_string(command)
        self.em.send_enter()

        # check that the results are all printed before emoving on
        found = False
        while not found:
            time.sleep(1)
            try:
                s = self.em.screen_parser(quiet=self.args['quiet'])
                if self.args['logfile'] is not None:
                    logging.debug(s)
                time.sleep(1)
                if self.findStatus(status='MORE...'):
                    self.em.send_pa1()
                    self.em.send_enter()
                    continue
                if self.findStatus(status='HOLDING'):
                    self.em.send_pa1()
                    self.em.send_enter()
                    continue
                if self.findStatus(status='RUNNING'):
                    self.em.send_enter()
                    continue
                found = self.findString(string='Ready', status='VM READ')
            except TimeoutSignal:
                if found:
                    break
        return

    def logoff(self):
        self.em.send_string('logoff')
        self.em.send_enter()
        time.sleep(1)

    def ___del___(self):
        self.em.terminate()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
The cms_ext_api provides both a library and a command line interface to it, to allow connection to a 3270 terminal and through it to a z/VM, and then to execute a number of .
        '''))
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('--host', action='store', required=True)
    parser.add_argument('-u', '--username', action='store',
                        default=None, help='Give the username and then \
                            get prompted for the password.')
    parser.add_argument('-e', '--env_cred', action='store',
                        nargs=2, metavar=('username', 'password'),
                        help='Use (already set) environment variables to get \
                            the username and password.')

    parser.add_argument('-l', '--logfile', action='store', default=None,
                        help='Give the path to the file where the logging \
                            information will be stored.')
    parser.add_argument('-t', '--traceback', action='store_true',
                        default=False, help='It will show the traceback in \
                            case of an exception to facilitate debugging.')
    parser.add_argument('--no-certificate-verification', action='store_true',
                        default=False, help='Allows to overcome an SSL \
                        handshake error due to self signed certificates.')
    parser.add_argument('-q', '--quiet', action='store_true', help='It will \
                            reduce the terminal output to the minimum possible.')
    parser.add_argument('-c', '--console-on', action='store_true',
                        default=False, help='')

    args = parser.parse_args()
    args_dict = vars(args)

    if args_dict['traceback'] is False:
        sys.tracebacklimit = 0

    if args_dict['env_cred'] is not None:
        u, p = args_dict['env_cred']  # Use directly passed username & password
    elif args_dict['username'] is not None:
        u = args_dict['username']
        p = getpass.getpass()
    else:
        raise CMSAPIException(error_code=NO_CREDENTIALS)

    if args_dict['logfile'] is not None:
        logfile_path = os.path.expanduser(args_dict['logfile'])
        logfile_dir = os.path.split(logfile_path)[0]
        if not os.path.exists(logfile_dir):
            raise CMSAPIException(error_code=LOGFILE_PATH_ERROR)
        logging.basicConfig(
            filename=logfile_path,
            format='%(levelname)s:%(message)s',
            level=logging.DEBUG)
    lpars_selection = sys.argv[6]
    available_hatt_files = sys.argv[7]
    target = sys.argv[8]
    file_format = sys.argv[9]
    print( "----------file--------")
    print(file_format)
    commands = [f"chugd {target} {sys.argv[10]} ({available_hatt_files}"]
    c = console(args_dict, u, p)
    r = c.logon()
    if r != ALL_FINE:
        try:
            c.___del___()
            raise CMSAPIException(error_code=r)
        except NameError:
            pass
        exit(r)

    c.execute_all(commands=commands)

    time.sleep(1)
    try:
        c.___del___()
    except NameError:
        pass

    exit(0)
