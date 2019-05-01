"""
a module to validate if core files exist on naples or not
"""
import os
import re
import sys
import time
import telnetlib
from pyats import aetest

sys.path.append(os.environ["PEN_SYSTEST"])
from lib.connect_lib import connect


class NaplesCoreFileCheck:
    """
    naples core file that will handle logging in to naples and running show core command, parsing output and returning result
    """

    def __init__(
        self,
        log,
        naples_ip,
        connection_port="22",
        naples_user="root",
        naples_password="pen123",
        conn_mode="ssh",
        core_dir="/data/core/",
    ):
        """
        init method to inititalize naples connection mode, directory to look for core, connection method, etc
        :param naples_ip - if connection is via console, this is the console switch ip: e.g. chamber-ts5, 
        otherwise this is the naples oob_ip
        :param connection_port - if connectin is via console, this is console port - 2006, default is oob, and port is 22
        :param naples_user - naples console login user name
        :param naples_password - naples console login password
        :param conn_mode - telnet or ssh, default is ssh assumed for oob
        :param core_dir - default directory to look core files for - change is core directory changes in the future 
        usage example:
         - ssh:
            naples = validate_core_on_naples.NaplesCoreFileCheck(log, "192.168.129.244", conn_mode="ssh")
        - telnet:
            naples = validate_core_on_naples.NaplesCoreFileCheck(log, "192.168.71.167", "2026", conn_mode="telnet")
        hdl = naples.connect_to_naples()
        list_core_files = naples.get_core_files(hdl)
        core_file_time_stampped = naples.timestamp_core_file(hdl, core_files)
        """
        self.log = log
        self.server = naples_ip
        if conn_mode.lower() == "ssh":
            self.connection_port = "22"
            self.conn_mode = "ssh"
        elif conn_mode.lower() == "telnet":
            self.conn_mode = "telnet"
            self.connection_port = connection_port
        self.naples_user = naples_user
        self.naples_password = naples_password
        self.conn_mode = conn_mode
        self.core_dir = core_dir

    def _clear_console_line(self, term_server, port):
        """
        if connecting via console, clear the line first before issuing commands to naples
        returns success if line is cleared faiilure if not, subsequent telnet commands should stop executing, 
        if this method returns failure. this must be run first if connection method is via telnet
        """
        console_conn = telnetlib.Telnet(term_server)
        # log.info("clearing console line for port {telnet_port} on terminal server {term_server}".
        # format(telnet_port=port, term_server=term_server))
        login_prompt = console_conn.expect(
            [str.encode("Username: "), str.encode("Password: ")], timeout=30
        )
        if (
            login_prompt[0] == 0
        ):  # means Username prompt is matched... need to send the user name for console server
            console_conn.write(b"admin\n")
            password_prompt = console_conn.expect([b"Password :"], timeout=30)
        console_conn.write(b"N0isystem$\n")
        console_prompt = console_conn.expect([b"#"])
        cmd = "clear line {port}\n".format(port=str(int(port) % 2000))
        cmd = str.encode(cmd)
        try:
            console_conn.write(cmd)
            console_conn.expect([b"confirm"], timeout=30)
            console_conn.write(b"y\n")
            console_conn.expect([b"#"])
            console_conn.write(b"exit\n")
            console_conn.close()
            return "SUCCESS"
        except:
            # log.error("Unable to clear port {port} on terminal server {server}".
            # format(port=port, server=term_server))
            console_conn.close()
            return "FAIL"

    def connect_to_naples(self):
        """
        connect to naples either via ssh or telnet
        return hadle is connection is successful, telnet handle or ssh handle
        if conn_mode is telnet, call clear_console_line first
        """
        if self.conn_mode == "telnet":
            if self._clear_console_line(
                self.server, self.connection_port
            ) == str.upper("success"):
                naples_conn = telnetlib.Telnet(
                    self.server, self.connection_port
                )
                naples_prompt = ("", "")
                time.sleep(1)
                naples_conn.write(b"\r\n")
                naples_login = naples_conn.expect(
                    [
                        str.encode("login:"),
                        str.encode("Password:"),
                        str.encode("# "),
                    ],
                    timeout=30,
                )
                if naples_login[0] == 0:
                    try:
                        naples_conn.write(
                            str.encode(
                                "{user}\n".format(user=self.naples_user)
                            )
                        )
                        naples_prompt = naples_conn.expect(
                            [str.encode("Password: ")], timeout=30
                        )
                    except:
                        # log.error("Unable to login to naples located at {server} {port}".
                        # format(server=self.server, port=self.connection_port))
                        return 0
                if naples_login[0] == 1 or naples_prompt[0] == 0:
                    try:
                        naples_conn.write(
                            str.encode(
                                "{password}\n".format(
                                    password=self.naples_password
                                )
                            )
                        )
                        naples_prompt = naples_conn.expect(
                            [str.encode("# ")], timeout=30
                        )
                    except:
                        # log.error("Unable to login to naples located at {server} {port}".
                        # format(server=self.server, port=self.connection_port))
                        return 0
                return naples_conn
        cobj1 = connect(
            self.log,
            connect_type="NETMIKO",
            hostip=self.server,
            username=self.naples_user,
            password=self.naples_password,
        )
        if cobj1.connect_to_node():
            msg = "Failed to connect to node {}".format(self.server)
            self.log.error(msg)
            return None
        return cobj1

    def get_core_files(self, hdl):
        """
        if there are core files, return list of core files name
        """
        core_cmd = "ls {cores_location} | grep core\n".format(
            cores_location=self.core_dir
        )
        if self.conn_mode == "telnet":
            hdl.write(str.encode(core_cmd))
            core_output = hdl.expect([str.encode("# ")], timeout=30)
            core_list = core_output[2]
            core_list = core_list.decode()
            core_list = core_list.split("\r\n")
            return core_list
        error, core_output = hdl.execute(core_cmd)
        if error:
            return None
        return core_output.split("\n")

    # def _get_current_naples_time(self, hdl):
    #    """
    #    get naples time to analyze core files relative to "now"
    #    """
    #    if self.conn_mode == "telnet":
    #        hdl.write(str.encode("date\n"))
    #        naples_time_now = hdl.expect([str.encode("# ")], timeout=30)
    #        return naples_time_now[2].decode()
    #    error, naples_time_now = hdl.execute("date")
    #    if error:
    #        return None
    #    return naples_time_now

    def timestamp_core_file(self, hdl, core_files):
        """
        extract the time stamp information from naples core files
        and print when and how long ago the core occured
        get current naples time from _get_current_naples_time method
        """
        escape_char_codes = re.compile(r"\x1b[^m]*m")
        # naples_time = self._get_current_naples_time(hdl).split("\r\n")[1]
        core_dict = dict()
        print(core_files)
        if core_files:
            for core in core_files:
                core = core.replace(".", "_")
                core = escape_char_codes.sub("", core)
                if not "core_" in core:
                    continue
                if core.endswith("_gz"):
                    # core_tm = core.split("_")[-1].strip(".gz")
                    core_tm = core.split("_")[-2]
                else:
                    core_tm = core.split("_")[-1]
                # core_tm = core.split("_")[-2]
                core_time = (
                    core_tm[:4]
                    + "-"
                    + core_tm[4:6]
                    + "-"
                    + core_tm[6:8]
                    + "-"
                    + core_tm[8:10]
                    + "-"
                    + core_tm[10:12]
                )
                core_name = (
                    re.search(r"(.*?)[0-9]", core)[1]
                    .rstrip("_")
                    .replace("core_", "")
                )
                core_dict[core_time] = core_name
        if bool(core_dict):
            return core_dict
        return None
        