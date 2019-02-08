"""
a common testsetup module to perform common test setup for rdma related tests
"""
import os
import sys
import logging
from collections import namedtuple
import yaml
from netmiko import ConnectHandler
sys.path.append(os.environ['PEN_SYSTEST'])
from lib import *

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
logging.root.setLevel(logging.INFO)
log = logging.getLogger(__name__)


class TestBedSetup:
    """
    class to parse RDMA test related inputs and return a dictionary of all variables
    """
    def __init__(self, physical_topo_file, input_file, mapping_file,
                 rdma_file, host1_name, host1_intf, host2_name,
                 host2_intf):
        """
        setup the instance of the class
        :param physical_topo_file:
        :param input_file:
        :param mapping_file:
        :param rdma_file:
        :param host1_name:
        :param host1_intf:
        :param host2_name:
        :param host2_intf:
        :return rdma_testbed_params: a dictionary of all RDMA testbed related variables
        """
        self.physical_topo = physical_topo_file
        self.input = input_file
        self.mapping = mapping_file
        self.rdma = rdma_file
        self.h1_name = host1_name
        self.h1_intf = host1_intf
        self.h2_name = host2_name
        self.h2_intf = host2_intf
        self.rdma_testbed_params = {}

        with open(self.physical_topo, 'r+') as file_pointer:
            phy_dict = yaml.load(file_pointer)

        with open(self.input, 'r+') as file_pointer:
            input_dict = yaml.load(file_pointer)

        with open(self.mapping, 'r+') as file_pointer:
            mapping_dict = yaml.load(file_pointer)

        with open(self.rdma, 'r+') as file_pointer:
            rdma_dict = yaml.load(file_pointer)['endpoint']['profile1']

        self.HostDetail = namedtuple('HostDetail', ['ipv4addr', 'ipv4mask', 'ipv6addr',
                                                    'ipv6mask', 'intf_name', 'mgmt_ip',
                                                    'username', 'password'])

        self.host1_io_name = mapping_dict[self.h1_name]['workload-name']
        self.host1_io_intf = mapping_dict[self.h1_name][self.h1_intf]
        self.host2_io_name = mapping_dict[self.h2_name]['workload-name']
        self.host2_io_intf = mapping_dict[self.h2_name][self.h2_intf]

        self.host1_mgmt_ip = phy_dict['DEVICES'][self.host1_io_name]['mgmt_ip']
        self.host1_username = phy_dict['DEVICES'][self.host1_io_name]['username']
        self.host1_passwd = phy_dict['DEVICES'][self.host1_io_name]['password']
        self.host1_os_type = phy_dict['DEVICES'][self.host1_io_name]['os_type']
        self.host1_ib_dev = input_dict['endpoint'][self.h1_name][self.h1_intf]['ib_dev']
        self.host1_ib_port = input_dict['endpoint'][self.h1_name][self.h1_intf]['ib_port']




        self.host2_mgmt_ip = phy_dict['DEVICES'][self.host2_io_name]['mgmt_ip']
        self.host2_username = phy_dict['DEVICES'][self.host2_io_name]['username']
        self.host2_passwd = phy_dict['DEVICES'][self.host2_io_name]['password']
        self.host2_os_type = phy_dict['DEVICES'][self.host2_io_name]['os_type']
        self.host2_ib_dev = input_dict['endpoint'][self.h2_name][self.h2_intf]['ib_dev']
        self.host2_ib_port = input_dict['endpoint'][self.h2_name][self.h2_intf]['ib_port']


        self.host1_io_v4 = input_dict['endpoint'][self.h1_name][self.h1_intf]['ipv4addr']
        self.host1_io_v4mask = input_dict['endpoint'][self.h1_name][self.h1_intf]['ipv4mask']
        self.host2_io_v4 = input_dict['endpoint'][self.h2_name][self.h2_intf]['ipv4addr']
        self.host2_io_v4mask = input_dict['endpoint'][self.h2_name][self.h2_intf]['ipv4mask']

        self.host1_io_v6 = input_dict['endpoint'][self.h1_name][self.h1_intf]['ipv6addr']
        self.host1_io_v6mask = input_dict['endpoint'][self.h1_name][self.h1_intf]['ipv6mask']
        self.host2_io_v6 = input_dict['endpoint'][self.h2_name][self.h2_intf]['ipv6addr']
        self.host2_io_v6mask = input_dict['endpoint'][self.h2_name][self.h2_intf]['ipv6mask']

        self.host1_tuple = self.HostDetail(ipv4addr=self.host1_io_v4, ipv4mask=self.host1_io_v4mask,
                                           ipv6addr=self.host1_io_v6, ipv6mask=self.host1_io_v6mask,
                                           intf_name=self.host1_io_intf, mgmt_ip=self.host1_mgmt_ip,
                                           username=self.host1_username, password=self.host1_passwd)

        self.host2_tuple = self.HostDetail(ipv4addr=self.host2_io_v4, ipv4mask=self.host2_io_v4mask,
                                           ipv6addr=self.host2_io_v6, ipv6mask=self.host2_io_v6mask,
                                           intf_name=self.host2_io_intf, mgmt_ip=self.host2_mgmt_ip,
                                           username=self.host2_username, password=self.host2_passwd)
        self.host1_config_dict = input_dict['endpoint'][self.h1_name][self.h1_intf]
        self.host2_config_dict = input_dict['endpoint'][self.h2_name][self.h2_intf]

        self.default_size = rdma_dict['perf_test_default_size']
        self.atomic_default_size = rdma_dict['atomic_default_size']
        self.latency_default_size = rdma_dict['latency_default_size']
        self.custom_size1 = rdma_dict['custom_size1']
        self.custom_size2 = rdma_dict['custom_size2']
        self.custom_size3 = rdma_dict['custom_size3']
        self.custom_size4 = rdma_dict['custom_size4']
        self.custom_size5 = rdma_dict['custom_size5']
        self.custom_size6 = rdma_dict['custom_size6']

        self.expected_bw = {str(self.default_size): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.default_size]}
        self.expected_bw1 = {
            str(self.custom_size1): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size1]}
        self.expected_bw2 = {
            str(self.custom_size2): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size2]}
        self.expected_bw3 = {
            str(self.custom_size3): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size3]}
        self.expected_bw4 = {
            str(self.custom_size4): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size4]}
        self.expected_bw5 = {
            str(self.custom_size5): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size5]}
        self.expected_bw6 = {
            str(self.custom_size6): rdma_dict['host2']['expected_bw_sweep']['non_atomic']['bytes'][self.custom_size6]}

        self.expected_bw_atomic = {str(self.atomic_default_size): rdma_dict['host2']['expected_bw_sweep']['atomic']['bytes'][self.atomic_default_size]}
        self.expect_bw_unit = rdma_dict['host2']['expected_units']['bandwidth']
        self.expect_lat_unit = rdma_dict['host2']['expected_units']['latency']
        self.expected_lat_write = {str(self.latency_default_size): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.latency_default_size]}
        self.expected_lat_write1 = {str(self.custom_size1): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size1]}
        self.expected_lat_write2 = {
            str(self.custom_size2): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size2]}
        self.expected_lat_write3 = {
            str(self.custom_size3): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size3]}
        self.expected_lat_write4 = {
            str(self.custom_size4): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size4]}
        self.expected_lat_write5 = {
            str(self.custom_size5): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size5]}
        self.expected_lat_write6 = {
            str(self.custom_size6): rdma_dict['host2']['expected_lat_sweep']['write']['bytes'][self.custom_size6]}
        self.expected_lat_read = {str(self.latency_default_size): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.latency_default_size]}
        self.expected_lat_read1 = {str(self.custom_size1): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size1]}
        self.expected_lat_read2 = {
            str(self.custom_size2): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size2]}
        self.expected_lat_read3 = {
            str(self.custom_size3): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size3]}
        self.expected_lat_read4 = {
            str(self.custom_size4): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size4]}
        self.expected_lat_read5 = {
            str(self.custom_size5): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size5]}
        self.expected_lat_read6 = {
            str(self.custom_size6): rdma_dict['host2']['expected_lat_sweep']['read']['bytes'][self.custom_size6]}
        self.expected_lat_atomic = {str(self.atomic_default_size): rdma_dict['host2']['expected_lat_sweep']['atomic']['bytes'][self.atomic_default_size]}
        self.size = rdma_dict['size']
        self.count = rdma_dict['count']

        self.rdma_testbed_params['phy_dict'] = phy_dict
        self.rdma_testbed_params['input_dict'] = input_dict
        self.rdma_testbed_params['mapping_dict'] = mapping_dict
        self.rdma_testbed_params['rdma_dict'] = rdma_dict
        self.rdma_testbed_params['host1_io_name'] = self.host1_io_name
        self.rdma_testbed_params['host1_io_intf'] = self.host1_io_intf
        self.rdma_testbed_params['host2_io_name'] = self.host2_io_name
        self.rdma_testbed_params['host2_io_intf'] = self.host2_io_intf
        self.rdma_testbed_params['host1_mgmt_ip'] = self.host1_mgmt_ip
        self.rdma_testbed_params['host1_username'] = self.host1_username
        self.rdma_testbed_params['host1_passwd'] = self.host1_passwd
        self.rdma_testbed_params['host1_ib_dev'] = self.host1_ib_dev
        self.rdma_testbed_params['host1_ib_port'] = self.host1_ib_port
        self.rdma_testbed_params['host2_mgmt_ip'] = self.host2_mgmt_ip
        self.rdma_testbed_params['host2_username'] = self.host2_username
        self.rdma_testbed_params['host2_passwd'] = self.host2_passwd
        self.rdma_testbed_params['host2_ib_dev'] = self.host2_ib_dev
        self.rdma_testbed_params['host2_ib_port'] = self.host2_ib_port
        self.rdma_testbed_params['host1_io_v4'] = self.host1_io_v4
        self.rdma_testbed_params['host1_io_v4mask'] = self.host1_io_v4mask
        self.rdma_testbed_params['host2_io_v4'] = self.host2_io_v4
        self.rdma_testbed_params['host2_io_v4mask'] = self.host2_io_v4mask
        self.rdma_testbed_params['host1_io_v6'] = self.host1_io_v6
        self.rdma_testbed_params['host1_io_v6mask'] = self.host1_io_v6mask
        self.rdma_testbed_params['host2_io_v6'] = self.host2_io_v6
        self.rdma_testbed_params['host2_io_v6mask'] = self.host2_io_v6mask

        self.rdma_testbed_params['expected_bw'] = self.expected_bw
        self.rdma_testbed_params['expected_bw1'] = self.expected_bw1
        self.rdma_testbed_params['expected_bw2'] = self.expected_bw2
        self.rdma_testbed_params['expected_bw3'] = self.expected_bw3
        self.rdma_testbed_params['expected_bw4'] = self.expected_bw4
        self.rdma_testbed_params['expected_bw5'] = self.expected_bw5
        self.rdma_testbed_params['expected_bw6'] = self.expected_bw6
        self.rdma_testbed_params['expected_bw_atomic'] = self.expected_bw_atomic
        self.rdma_testbed_params['expected_bw_units'] = self.expect_bw_unit
        self.rdma_testbed_params['expected_lat_write'] = self.expected_lat_write
        self.rdma_testbed_params['expected_lat_write1'] = self.expected_lat_write1
        self.rdma_testbed_params['expected_lat_write2'] = self.expected_lat_write2
        self.rdma_testbed_params['expected_lat_write3'] = self.expected_lat_write3
        self.rdma_testbed_params['expected_lat_write4'] = self.expected_lat_write4
        self.rdma_testbed_params['expected_lat_write5'] = self.expected_lat_write5
        self.rdma_testbed_params['expected_lat_write6'] = self.expected_lat_write6
        self.rdma_testbed_params['expected_lat_atomic'] = self.expected_lat_atomic
        self.rdma_testbed_params['expected_lat_read'] = self.expected_lat_read
        self.rdma_testbed_params['expected_lat_read1'] = self.expected_lat_read1
        self.rdma_testbed_params['expected_lat_read2'] = self.expected_lat_read2
        self.rdma_testbed_params['expected_lat_read3'] = self.expected_lat_read3
        self.rdma_testbed_params['expected_lat_read4'] = self.expected_lat_read4
        self.rdma_testbed_params['expected_lat_read5'] = self.expected_lat_read5
        self.rdma_testbed_params['expected_lat_read6'] = self.expected_lat_read6
        self.rdma_testbed_params['expected_lat_units'] = self.expect_lat_unit
        self.rdma_testbed_params['size'] = self.size
        self.rdma_testbed_params['count'] = self.count
        self.rdma_testbed_params['host1_tuple'] = self.host1_tuple
        self.rdma_testbed_params['host2_tuple'] = self.host2_tuple
        self.rdma_testbed_params['host1_os_type'] = self.host1_os_type
        self.rdma_testbed_params['host2_os_type'] = self.host2_os_type

    def login_to_servers(self):
        """
        login to hosts provided for RDMA test. return 0 if login fails, test case failure show be handled in setup script
        :return:
        """
        cobj1 = connect(log, connect_type='NETMIKO', hostip=self.host1_tuple.mgmt_ip, username=self.host1_tuple.username, password=self.host1_tuple.password)
        if cobj1.connect_to_node():
            msg = "Failed to connect to node {}".format(self.host1_io_name)
        cobj1.hostip = self.host1_mgmt_ip
        cobj1.hostname = self.host1_io_name
        cobj1.username = self.host1_username
        cobj1.password = self.host1_passwd
        cobj1.os_type = self.host1_os_type
        cobj1.io_intf = self.host1_io_intf

        cobj2 = connect(log, connect_type='NETMIKO', hostip=self.host2_tuple.mgmt_ip, username=self.host2_tuple.username, password=self.host2_tuple.password)
        if cobj2.connect_to_node():
            msg = "Failed to connect to node {}".format(self.host2_io_name)
        cobj2.hostip = self.host2_mgmt_ip
        cobj2.hostname = self.host2_io_name
        cobj2.username = self.host2_username
        cobj2.password = self.host2_passwd
        cobj2.os_type = self.host2_os_type
        cobj2.io_intf = self.host2_io_intf
        self.rdma_testbed_params['hdl1'] = cobj1
        self.rdma_testbed_params['hdl2'] = cobj2

        for hdl in [self.rdma_testbed_params['hdl1'], self.rdma_testbed_params['hdl2']]:
            if hdl.os_type == 'linux':
                hdl.execute('export PATH="$PATH:/root/drivers-linux/rdma-core/build/bin"')
                hdl.execute('export PATH="$PATH:/root/drivers-linux/perftest"')
                hdl.execute('rmmod ionic.ko')
                hdl.execute('insmod /root/drivers-linux/drivers/eth/ionic/ionic.ko')
                hdl.execute('modprobe ib_uverbs')
                hdl.execute('insmod /root/drivers-linux/drivers/rdma/drv/ionic/ionic_rdma.ko xxx_haps=1')
            elif hdl.os_type == 'freebsd':
                hdl.execute('kldload drivers-freebsd/sys/modules/ionic/ionic.ko')
                hdl.execute('kldload drivers-freebsd/sys/modules/ionic_rdma/ionic_rdma.ko')
            else:
                return 0


        host1_intf_obj = Interface(self.rdma_testbed_params['hdl1'], self.rdma_testbed_params['hdl1'].io_intf, log)
        host2_intf_obj = Interface(self.rdma_testbed_params['hdl2'], self.rdma_testbed_params['hdl2'].io_intf, log)
        host1_intf_obj.configure(self.host1_config_dict)
        host2_intf_obj.configure(self.host2_config_dict)
        if cobj1.os_type == 'linux':
            host1_gid = rdma_utils.GetgidIndex(self.rdma_testbed_params['hdl1'], log)
            host1_gid_index = host1_gid.getGidIndex(self.host1_io_v4)
            self.rdma_testbed_params['host1_gid_index'] = host1_gid_index
        if cobj1.os_type == 'freebsd':
            host1_gid_index = "1"
            self.rdma_testbed_params['host1_gid_index'] = host1_gid_index
        if cobj2.os_type == 'linux':
            host2_gid = rdma_utils.GetgidIndex(self.rdma_testbed_params['hdl2'], log)
            host2_gid_index = host2_gid.getGidIndex(self.host2_io_v4)
            self.rdma_testbed_params['host2_gid_index'] = host2_gid_index
        if cobj2.os_type == 'freebsd':
            host2_gid_index = "1"
            self.rdma_testbed_params['host2_gid_index'] = host2_gid_index

        ping_obj = verifyPing(self.rdma_testbed_params['hdl2'], log)
        ping_obj.ping(self.host1_io_v4)

        return self.rdma_testbed_params
