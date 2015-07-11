# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2014, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Tony Beckham tony@eucalyptus.com
#

import time
from eucaops import Eucaops
from eucaops import ELBops
from boto.ec2.elb import LoadBalancer
from eutester.eutestcase import EutesterTestCase
import os
import random


class StickinessBasics(EutesterTestCase):
    def __init__(self, extra_args=None):
        self.setuptestcase()
        self.setup_parser()
        if extra_args:
            for arg in extra_args:
                self.parser.add_argument(arg)
        self.get_args()

        # Setup basic eutester object
        if self.args.region:
            self.tester = ELBops(credpath=self.args.credpath, region=self.args.region)
        else:
            self.tester = Eucaops(credpath=self.args.credpath, config_file=self.args.config,
                                  password=self.args.password)
        self.tester.poll_count = 120

        ### Add and authorize a group for the instance
        self.group = self.tester.add_group(group_name="group-" + str(int(time.time())))
        self.tester.authorize_group_by_name(group_name=self.group.name)
        self.tester.authorize_group_by_name(group_name=self.group.name, port=-1, protocol="icmp")
        ### Generate a keypair for the instance
        self.keypair = self.tester.add_keypair("keypair-" + str(int(time.time())))
        self.keypath = '%s/%s.pem' % (os.curdir, self.keypair.name)

        ### Get an image
        self.image = self.args.emi
        if not self.image:
            self.image = self.tester.get_emi()

        ### Populate available zones
        zones = self.tester.ec2.get_all_zones()
        self.zone = random.choice(zones).name

        self.load_balancer_port = 80

        (self.web_servers, self.filename) = self.tester.create_web_servers(keypair=self.keypair,
                                                                           group=self.group,
                                                                           zone=self.zone,
                                                                           port=self.load_balancer_port,
                                                                           filename='instance-name',
                                                                           image=self.image)

        self.load_balancer = self.tester.create_load_balancer(zones=[self.zone],
                                                              name="test-" + str(int(time.time())),
                                                              load_balancer_port=self.load_balancer_port)
        assert isinstance(self.load_balancer, LoadBalancer)
        self.tester.register_lb_instances(self.load_balancer.name,
                                          self.web_servers.instances)


    def clean_method(self):
        self.tester.cleanup_artifacts()

    def GenerateRequests(self):
        """
        This will test the most basic use case for a load balancer.
        Uses to backend instances with httpd servers.
        """
        dns = self.tester.service_manager.get_enabled_dns()
        lb_ip = dns.resolve(self.load_balancer.dns_name)
        lb_url = "http://{0}:{1}/instance-name".format(lb_ip, self.load_balancer_port)
        return self.tester.generate_http_requests(url=lb_url, count=100, worker_threads=1)

    def session_affinity_test(self):
        lbpolicy = "LB-Policy"
        self.tester.create_lb_cookie_stickiness_policy(cookie_expiration_period=300,
                                                       lb_name=self.load_balancer.name,
                                                       policy_name=lbpolicy)
        acpolicy = "AC-Policy"
        self.tester.create_app_cookie_stickiness_policy(name="test-cookie",
                                                        lb_name=self.load_balancer.name,
                                                        policy_name=acpolicy)
        """test lb stickiness"""
        self.tester.sleep(2)
        self.debug("Testing LB cookie stickiness")
        self.tester.set_lb_policy(lb_name=self.load_balancer.name, lb_port=80, policy_name=lbpolicy)
        responses = self.GenerateRequests()
        host = responses[0]
        for response in responses:
            if response != host:
                raise Exception(
                    "Expected same response due to load balancer stickiness policy. Got initial response: " + host +
                    " subsequent response: " + response)

        """test app cookie stickiness"""
        self.tester.set_lb_policy(lb_name=self.load_balancer.name, lb_port=80, policy_name=acpolicy)
        self.debug("Testing App Cookie stickiness")
        responses = self.GenerateRequests()
        # since we use the same cookie name on the backing elb instances, the first contacts with the ELB can possibly
        # result in hitting different back ends. After the first 2 calls they should all ony go to 1 backend.
        host = responses[2]
        for response in responses[2:]:
            if response != host:
                raise Exception(
                    "Expected same response due to app cookie stickiness policy. Got initial response: " + host +
                    " subsequent response: " + response)
        return


if __name__ == "__main__":
    testcase = StickinessBasics()
    ### Use the list of tests passed from config/command line to determine what subset of tests to run
    ### or use a predefined list
    list = testcase.args.tests or ["session_affinity_test"]

    ### Convert test suite methods to EutesterUnitTest objects
    unit_list = []
    for test in list:
        unit_list.append(testcase.create_testunit_by_name(test))

    ### Run the EutesterUnitTest objects
    result = testcase.run_test_case_list(unit_list, clean_on_exit=True)
    exit(result)