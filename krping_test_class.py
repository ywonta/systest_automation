class KrpingTest(aetest.Testcase):
    def __init__(self, srv_hdl, server_addr, cli_hdl, log):
        """
        create krping class instance with server handle, client handle and target ip address for krping test
        :param srv_hdl:
        :param server_addr:
        :param cli_hdl:
        :param log:
        """
        log.info("krping test for between hosts {} and {}".format(srv_hdl.hostname, cli_hdl.hostname))
        self.srv_hdl = srv_hdl
        self.cli_hdl = cli_hdl
        self.log = log
        self.server = server_addr
        self.krping_server_result = ""
        self.krping_client_result = ""
        if self.srv_hdl.os_type != self.cli_hdl.os_type:
            self.log.error("different os type detected for client and server")
            self.failed("Krping test will only run between similar host os types")

    def _load_krping_module(self, hdl, compat=False):
        """
        function to load krping module for linux and freebsd type hosts
        :param hdl: handle of the remote host
        :param compat: netapp specific, if krping_compat is enabled, it will load old krping
        :return: 1 on success, 0 on failure
        """
        if hdl.os_type == "freebsd":
            if compat:
                krping_ko = "/usr/src/sys/modules/rdma/krping_compat/krping_compat.ko"
                if "No such file or directory" in hdl.execute("ls {}".format(krping_ko)):
                    self.log.error("krping compat module is not found at the specified location")
                    self.log.error("krping module load will not be attempted")
                    self.failed("unable to locate krping module on %s" % hdl.hostname)
            elif hdl.os_type == "freebsd":
                krping_ko = "krping.ko"
            if "No such file or directory" in hdl.execute("kldload {}".format(krping_ko)):
                self.log.error("unable to load krping module on %s" % hdl.hostname)
                self.failed("unable to load krping module on %s" % hdl.hostname)
            return 1
        krping_ko = "/root/krping/rdma_krping.ko"
        if "No such file or directory" in hdl.execute("ls {}".format(krping_ko)):
            self.log.error("krping compat module is not found at the specified location")
            self.log.error("krping module load will not be attempted")
            self.failed("unable to locate krping module on %s" % hdl.hostname)
        if "No such file or directory" in hdl.exeute("insmod {}".format(krping_ko)):
            self.log.error("unable to load krping module on %s" % hdl.hostname)
            self.failed("unable to load krping module on %s" % hdl.hostname)
        return 1

    def _verify_krping_loaded(self, hdl, compat=False):
        """
        verify if krping module is loaded on hosts, tests can be failed preemptively if there is no krping module loaded
        :param hdl:
        :param compat:
        :return: 1 on success, 0 on failure
        """
        if hdl.os_type == "freebsd":
            if compat:
                krping_ko = "krping_compat.ko"
            else:
                krping_ko = "krping.ko"
            if krping_ko in hdl.execute("kldstat | grep {}".format(krping_ko)):
                self.log.info("krping is already loaded %s" % hdl.hostname)
                return 1
            return 0
        krping_ko = "rdma_krping"
        if krping_ko in hdl.execute("insmod | grep ^{}".format(krping_ko)):
            self.log.info("krping is already loaded on host %s" % hdl.hostname)
            return 1
        return 0

    def _start_krping_server(self, hdl, args, qps, port=9991):
        """
        start krping server on server designated to act as krping server
        :param hdl:
        :param args: multiple krping args, coming from start test function
        :param qps: number of qps for this specific test, not to exceed 1000
        :param port:
        :return:
        """
        cmd = args + "server,"
        if hdl.os_type == "linux":
            krping_dev = "/proc/krping"
        elif hdl.os_type == "freebsd":
            krping_dev = "/dev/krping"
        else:
            self.log.error("unknown os type, failing the test before starting krping server")
            self.failed("os type is not specified")
        server_file = "krping_server.sh"
        dst_server_file = "/root/" + server_file
        with open(server_file, "w") as sf:
            sf.write('')
        with open(server_file, "w") as sf:
            for i in range(int(qps)):
                cmd1 = "echo \"" + cmd + "port=" + str(port+i) + "\" > " + krping_dev + " &\n"
                sf.write(cmd1)
        self.log.info("copying server script file to %s" % hdl.hostname)
        self._copy_krping_script(hdl, server_file, dst_server_file)
        time.sleep(1)
        self.log.info("Starting krping server on %s" % hdl.hostname)
        hdl.execute(dst_server_file + " &")
        server_start = hdl.execute("cat {}".format(krping_dev))
        if not bool(len(server_start)):
            self.log.error("Failed to start krping sessions on the server %s" % hdl.hostname)
            dmesg = hdl.execute("dmesg | tail -10")
            self.log.error(dmesg)
            self.failed("krping failed to start on server")
        return server_start

    def _start_krping_client(self, hdl, args, qps, port=9991):
        """
        start krping client on server designated for krping client
        :param hdl:
        :param args: args must be the same as the server except of keyword client
        :param qps: number of qps must be the same as on the server side
        :param port: port number must be the same as on the server side
        :return:
        """
        cmd = args + "client,"
        if hdl.os_type == "linux":
            krping_dev = "/proc/krping"
        elif hdl.os_type == "freebsd":
            krping_dev = "/dev/krping"
        else:
            self.log.error("unkown os type, failing the test before starting krping client")
            self.faile("os type is not specified or not valid")
        client_file = "krping_client.sh"
        dst_client = "/root/" + client_file
        with open(client_file, "w") as cf:
            cf.write('')
        with open(client_file, "w") as cf:
            for i in range(int(qps)):
                cmd1 = "echo \"" + cmd + "port=" + str(port+i) + "\" > " + krping_dev + " &\n"
                cf.write(cmd1)
        self.log.info("Copying client script to %s" % hdl.hostname)
        self._copy_krping_script(hdl, client_file, dst_client)
        time.sleep(1)
        self.log.info("Starting krping client on %s" % hdl.hostname)
        hdl.execute(dst_client + " &")

    def _copy_krping_script(self, handle, src_script, dst_script):
        """
        function to copy generated server and client krping shell files to remote machines and ready them for exec
        :param handle:
        :param src_script:
        :param dst_script:
        :return:
        """
        transfer_script = linux_utils.scp(src_script, handle.hostip+":"+dst_script, handle.username, handle.password)

    def _verify_krping(self, sleep):
        for hdl in [self.srv_hdl, self.cli_hdl]:
            if hdl.os_type == "linux":
                krping_dev = "/proc/krping"
            elif hdl.os_type == "freebsd":
                krping_dev = "/dev/krping"
            try:
                while hdl.execute("cat {}".format(krping_dev), timeout=900):
                    self.log.info("Krping process still running on host %s" % hdl.hostname)
                    time.sleep(sleep)
            except:
                self.log.info("unable to get krping session status after 15min wait")

        KRPING_FAIL_CONDITIONS = [" error",
                                  "Received connection request in wrong state",
                                  "cma detected device removal",
                                  "oof bad type",
                                  "Received bogus data",
                                  " failed",
                                  "Fastreg not supported",
                                  "txdepth must be > ",
                                  "unknown fr test",
                                  "data mismatch",
                                  "Couldn't post send",
                                  "Unkown frtest num",
                                  "bad addr string",
                                  "Invalid size",
                                  "Invalid count",
                                  "unknown mem mode",
                                  "unknown opt",
                                  "must be either client or server",
                                  "Pick only one test",
                                  "server_invalidate only valid with",
                                  "read_inv only valid with"
                                  ]
        SRV_PASS = True
        CLI_PASS = True
        self.log.info("analyzing log file on client and sever for proper completion of test")
        if self.cli_hdl.os_type == "linux" and (int(self.cli_hdl.execute("ls /var/log/ | grep syslog* | wc -l")) > 8):
            LOG_FILE = "/var/log/syslog"
        else:
            LOG_FILE = "/var/log/messages"
        for condition in KRPING_FAIL_CONDITIONS:
            self.log.info("checing for %s on client logs" % condition)
            cli_logs = self.cli_hdl.execute("grep -i \"{}\" {}".format(condition,LOG_FILE), timeout=600).splitlines()
            if len(cli_logs):
                for line in cli_logs:
                    if condition in line:
                        CLI_PASS = False
                        self.log.error(cli_logs)
                        self.failed("error on client side observerd")
                        return 0

        for condition in KRPING_FAIL_CONDITIONS:
            self.log.info("checking for %s on server logs" % condition)
            srv_logs = self.srv_hdl.execute("grep -i \"{}\" {}".format(condition,LOG_FILE), timeout=600).splitlines()
            if "error" in condition and len(srv_logs):
                for line in srv_logs:
                    if "cq completion in ERROR state" in line:
                        continue
                    else:
                        SRV_PASS = False
                        self.log.info(srv_logs)
                        self.failed("error on server side observerd")
                        return 0
            else:
                for line in srv_logs:
                    if condition in line:
                        SRV_PASS = False
                        self.log.info(srv_logs)
                        self.failed("error on server side observerd")
                        return 0
        self.passed("Krping test passed without error on client and server")

    def start_krping_test(self, size="65536", count="100", verbose=True, validate=True, server_inv=False,
                          local_dma_lkey=False,read_inv=False, txdepth="64", qps=1, ipv6=False, mem_mode="dma"):
        """
        main method to run krping test, responsible for validating krping module, starting server and starting client
        :param size: message size for krping transacitons, default is 64K
        :param count: number of iterations for the test, default is 100
        :param verbose: enable verbose output
        :param validate: validate send and received data
        :param server_inv: server invalidate, only allowed with fastreg
        :param local_dma_lkey: local dma lkey
        :param read_inv: read invalidate
        :param txdepth: transmit queue depth (limit is 1021 for Naples)
        :param qps: number of QPs to test (limit is 1000 for Naples)
        :param ipv6: run the test over ipv6, users addr6 flag instead of addr
        :param mem_mode: fastreg or dma
        :return:
        """
        SLEEP_TIME = 5
        if qps*int(count) > 10000:
            SLEEP_TIME = 10
        if ipv6 == True:
            command = "addr6={},count={},size={},txdepth={},"
        else:
            command = "addr={},count={},size={},txdepth={},"
        if verbose:
            command = command + "verbose,"
        if validate:
            command = command + "validate,"
        if mem_mode == "fastreg":
            if server_inv and local_dma_lkey:
                command = command + "server_inv,local_dma_lkey,mem_mode=fastreg,"
        elif mem_mode == "dma" and local_dma_lkey:
            command = command + "local_dma_lkey,"
        if read_inv:
            command = command + "read_inv,"
        if int(txdepth) < 64:
            txdepth = 64
        kport = random.randint(9000, 20000)

        for hdl in [self.srv_hdl, self.cli_hdl]:
            if self._verify_krping_loaded(hdl):
                continue
            else:
                self._load_krping_module(hdl, compat=True)

        self.log.info("Rotating logs on client before start of test")
        for hdl in [self.srv_hdl, self.cli_hdl]:
            if hdl.os_type == "linux":
                hdl.send_command_expect('logrotate -f /etc/logrotate.conf')
            elif hdl.os_type == "freebsd":
                hdl.send_command_expect('newsyslog -R "new krping test starting" /var/log/messages')
            else:
                self.log.warning("unkown os type, unable to do logrotate before start of test")

        self.log.info("Executing krping server")
        srv_state = self._start_krping_server(self.srv_hdl, command.format(self.server, count, size, txdepth), qps, kport)
        if srv_state:
            self.log.info("Krping server started successfully")
            self.log.info("Executing krping client")
            cli_state = self._start_krping_client(self.cli_hdl, command.format(self.server, count, size, txdepth), qps, kport)

        self.log.info("Starting krping verify")
        self._verify_krping(SLEEP_TIME)



