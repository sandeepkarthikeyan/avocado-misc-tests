#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# See LICENSE for more details.
#
# Copyright: 2016 IBM
# Author: Sandeep K <sandeep@linux.vnet.ibm.com>
#
# Based on code by Lucas Meneghel Rodrigues
# https://github.com/autotest/autotest-client-tests/tree/master/pktgen

import os
import re
from avocado import Test
from avocado import main
from avocado.utils import process


class Pktgen(Test):

    '''
    Pktgen is software based traffic generator powered by
    DPDK fast packet processing framework
    '''

    def setUp(self):
        self.eth = self.params.get("eth", default="eth0")
        self.count = self.params.get("count", default="50000")
        self.clone_skb = self.params.get("clone_skb", default="1")
        self.dst_ip = self.params.get("dst_ip", default="")
        self.dst_mac = self.params.get("dst_mac", default="")
        self.resultsdir = self.params.get("resultsdir", default="/root/")

        if not os.path.exists('/proc/net/pktgen'):
            process.system("modprobe pktgen", shell=True)
        if not os.path.exists('/proc/net/pktgen'):
            self.error("pktgen not loaded")

        # validating the dst_ip and network interface
        self.validate_net_interface()
        self.ping_test()

        # Adding the devices
        self.log.info("Adding devices")
        self.pgdev = '/proc/net/pktgen/kpktgend_0'
        self.pgset('rem_device_all')
        self.pgset('add_device ' + self.eth)
        self.pgset('max_before_softirq 10000')

        # configure the individual devices
        self.log.info("Configuring the individual devices")
        self.ethdev = '/proc/net/pktgen/' + self.eth
        self.pgdev = self.ethdev
        if self.clone_skb:
            self.pgset('clone_skb %s' % (self.count))
        self.pgset('min_pkt_size 60')
        self.pgset('max_pkt_size 60')
        self.pgset('dst ' + self.dst_ip)
        self.pgset('dst_mac ' + self.dst_mac)
        self.pgset('count %s' % (self.count))

    def test_pktgen(self):
        self.pgdev = '/proc/net/pktgen/pgctrl'
        self.pgset('start')
        output = os.path.join(self.resultsdir, self.eth)
        process.system("cp %s %s" % (self.ethdev, output), shell=True)

    def pgset(self, command):
        file_name = open(self.pgdev, 'w')
        file_name.write(command + '\n')
        file_name.close()

        if not self.match_string('Result: OK', self.pgdev):
            if not self.match_string('Result: NA', self.pgdev):
                process.system("cat " + self.pgdev, shell=True)

    def match_string(self, pattern, file_name):
        with open(file_name) as f:
            for line in f:
                if re.search("\b{0}\b".format(pattern), line):
                    return True
            return False

    def validate_net_interface(self):
        interfaces = process.system_output(
            "ip -o link show | awk -F': ' '{print $2}'", shell=True)
        if self.eth not in interfaces:
            self.skip("%s is not available" % self.eth)

    def ping_test(self):
        ping_response = process.system("ping -c 1 " + self.dst_ip, shell=True)
        self.log.info("Ping response value is %d" % ping_response)
        if ping_response != 0:
            self.skip("Host not reachable")

if __name__ == "__main__":
    main()