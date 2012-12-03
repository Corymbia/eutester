#!/usr/bin/env python
#
#
# Description:  This script upgrades a Eucalyptus cloud
import re
from testcases.cloud_admin.install_euca import Install

class Upgrade(Install):
    def __init__(self):
        super(Upgrade, self).__init__(download_creds=True)
        self.clc_service = self.tester.service_manager.get("eucalyptus")[0]
        self.zones = self.tester.get_zones()
        machine = self.tester.get_component_machines("clc")[0]
        self.old_version = machine.sys("cat /etc/eucalyptus/eucalyptus-version")[0]

    def upgrade_packages(self):
        for machine in self.tester.config["machines"]:
            if machine.distro.name is "vmware":
                continue
            if self.args.nogpg:
                machine.upgrade(nogpg=True)
            else:
                machine.upgrade()
            ## IF its a CLC and we have a SAN we need to install the san package after upgrade before service start
            if re.search("^3.1", self.old_version):
                if hasattr(self.args, 'ebs_storage_manager'):
                    if re.search("SANManager" ,self.args.ebs_storage_manager):
                        if re.search("clc", " ".join(machine.components)):
                            if hasattr(self.args, 'san_provider'):
                                if re.search("EquallogicProvider", self.args.san_provider):
                                    pass # Nothing to install on CLC for this case
                                if re.search("NetappProvider", self.args.san_provider):
                                    machine.install("eucalyptus-enterprise-storage-san-netapp-libs")
                                if re.search("EmcVnxProvider", self.args.san_provider):
                                    machine.install("eucalyptus-enterprise-storage-san-emc-libs")
                        if re.search("sc", " ".join(machine.components)):
                            if hasattr(self.args, 'san_provider'):
                                if re.search("EquallogicProvider", self.args.san_provider):
                                    machine.install("eucalyptus-enterprise-storage-san-equallogic")
                                if re.search("NetappProvider", self.args.san_provider):
                                    machine.install("eucalyptus-enterprise-storage-san-netapp")
                                if re.search("EmcVnxProvider", self.args.san_provider):
                                    machine.install("eucalyptus-enterprise-storage-san-emc")
            new_version = machine.sys("cat /etc/eucalyptus/eucalyptus-version")[0]
            if not self.args.nightly and re.match( self.old_version, new_version):
                raise Exception("Version before (" + self.old_version +") and version after (" + new_version + ") are the same")

    def UpgradeAll(self):
        self.add_euca_repo()
        if self.args.enterprise_url:
            self.add_enterprise_repo()
        self.upgrade_packages()
        self.start_components()
        if re.search("^3.1", self.old_version):
            self.set_block_storage_manager()


if __name__ == "__main__":
    testcase = Upgrade()
    ### Either use the list of tests passed from config/command line to determine what subset of tests to run
    list = testcase.args.tests or [ "UpgradeAll"]
    ### Convert test suite methods to EutesterUnitTest objects
    unit_list = [ ]
    for test in list:
        unit_list.append( testcase.create_testunit_by_name(test) )
        ### Run the EutesterUnitTest objects

    result = testcase.run_test_case_list(unit_list,clean_on_exit=True)
    exit(result)