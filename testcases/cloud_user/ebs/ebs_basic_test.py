#!/usr/bin/env python





import unittest
#from eucaops import Eucaops
#from eutester import euconfig
from ebstestsuite import EbsTestSuite
import argparse
import os

ebssuite = None
zone = None
config_file = None
password = None
credpath = None
keypair = None
group = None
emi = None

class ebs_tests(unittest.TestCase):
    
    def setUp(self):
        '''
        Main function of setup is to instantiate an ebsTestSuite object. With command line args. 
        '''
        self.ebssuite = EbsTestSuite(zone= zone, 
                            config_file= config_file, 
                            password=password,
                            credpath=credpath, 
                            keypair=keypair, 
                            group=group, 
                            image=emi)
    def test_ebs_basic_test_suite(self):
        '''
        Full suite of ebs related tests
        '''
        self.ebssuite.run_ebs_basic_test_suite()
        
        
    def tearDown(self):
        '''
        Clean up resource created during test, output results
        '''
        try:
            self.ebssuite.clean_created_resources()
        finally:
            self.ebssuite.print_test_list_results()
            
    


if __name__ == "__main__":
    ## If given command line arguments, use them as test names to launch
    parser = argparse.ArgumentParser(prog="ebs_basic_test.py",
                                     version="Test Case [ebs_basic_test.py] Version 0.1",
                                     description="Attempts to tests and provide info on focused areas related to\
                                     Eucalyptus EBS related functionality.",
                                     usage="%(prog)s --credpath=<path to creds> [--xml] [--tests=test1,..testN]")
    
    
    
    parser.add_argument('--emi', 
                        help="pre-installed emi id which to execute these tests against", default=None)
    parser.add_argument('--credpath', 
                        help="path to credentials", default=None)
    parser.add_argument('--zone', 
                        help="zone to use in this test, defaults to testing all zones", default=None)
    parser.add_argument('--password', 
                        help="password to use for machine root ssh access", default='foobar')
    parser.add_argument('--keypair', 
                        help="keypair to use when launching instances within the test", default=None)
    parser.add_argument('--group', 
                        help="group to use when launching instances within the test", default=None) 
    parser.add_argument('--config',
                       help='path to config file', default='../input/2btested.lst') 
    

    parser.add_argument('--tests', nargs='+', 
                        help="test cases to be executed", 
                        default= ['test_ebs_basic_test_suite'])
    
    args = parser.parse_args()
    
    '''
    Assign parsed arguments to this testcase globals
    '''
    
    #if file was not provided or is not found
    if not os.path.exists(args.config):
        print "Error: Mandatory Config File '"+str(args.config)+"' not found."
        parser.print_help()
        exit(1)
    zone = args.zone
    config_file = args.config
    password = args.password
    credpath = args.credpath
    keypair = args.keypair
    group = args.group
    emi = args.emi
    
    for test in args.tests:
        result = unittest.TextTestRunner(verbosity=2).run( ebs_tests(test))
        if result.wasSuccessful():
            pass
        else:
            exit(1)

    
  