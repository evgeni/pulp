#!/usr/bin/python
#
# Copyright (c) 2010 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.

# Python
import base64
import sys
import os
import unittest
import logging
import web

# Pulp
srcdir = os.path.abspath(os.path.dirname(__file__)) + "/../../src/"
sys.path.insert(0, srcdir)

commondir = os.path.abspath(os.path.dirname(__file__)) + '/../common/'
sys.path.insert(0, commondir)

import testutil
testutil.load_test_config()

import pulp.cert_generator as cert_generator
from pulp.api.user import UserApi
from pulp.certificate import Certificate
from pulp.webservices.role_check import RoleCheck
from ConfigParser import ConfigParser

logging.root.addHandler(logging.StreamHandler())
logging.root.setLevel(logging.DEBUG)



class TestRoleCheck(unittest.TestCase):

    def setUp(self):
        self.config = testutil.load_test_config()
        self.uapi = UserApi()

    def tearDown(self):
        self.uapi.clean()
        
    @RoleCheck(consumer=True)
    def some_method(self, someparam, otherparam):
        print "some method executed"
        return otherparam

    @RoleCheck(admin=True)
    def some_other_method(self, someparam, otherparam):
        print "some_other_method executed"
        return otherparam

        
    def test_id_cert(self):
        consumerUid = "someconsumer.example.com"
        (temp_pk, temp_cert) = cert_generator.make_cert(consumerUid)
        self.assertTrue(temp_cert != None)
        cert = Certificate()
        cert.update(temp_cert.as_pem())
        web.ctx['headers'] = []
        web.ctx['environ'] = dict()
        web.ctx.environ['SSL_CLIENT_CERT'] = cert.toPEM()
        retval = self.some_method(consumerUid,"baz")
        print "retval %s" % retval
        self.assertEquals(retval, "baz")
        
         
    def test_role_check(self):
        my_dir = os.path.abspath(os.path.dirname(__file__))
        test_cert = my_dir + "/data/test_cert.pem"
        cert = Certificate()
        cert.read(test_cert)
        web.ctx['headers'] = []
        web.ctx['environ'] = dict()
        web.ctx.environ['SSL_CLIENT_CERT'] = cert.toPEM()
        retval = self.some_method('somevalue')
        self.assertTrue(web.ctx.status.startswith('401'))
        
    def test_uname_pass(self):
        # create a user
        login = "test_auth"
        password = "some password"
        user = self.uapi.create(login, password=password)
        web.ctx['headers'] = []
        web.ctx['environ'] = dict()
        
        # Check we can run the method with no setup in web
        retval = self.some_other_method('somevalue')
        retval = self.some_other_method('somevalue', 'baz')
        self.assertNotEqual(retval, 'baz')
        
        # Check for bad pass
        loginpass = "%s:%s" % (login, "invalid password")
        encoded = base64.encodestring(loginpass)
        web.ctx.environ['HTTP_AUTHORIZATION'] = "Basic %s" % encoded
        retval = self.some_other_method('somevalue', 'baz')
        self.assertNotEqual(retval, 'baz')
        
        # Check for bad username
        loginpass = "%s:%s" % ("non existing user", password)
        encoded = base64.encodestring(loginpass)
        web.ctx.environ['HTTP_AUTHORIZATION'] = "Basic %s" % encoded
        retval = self.some_other_method('somevalue', 'baz')
        self.assertNotEqual(retval, 'baz')
        
        # Check for a proper result
        loginpass = "%s:%s" % (login, password)
        encoded = base64.encodestring(loginpass)
        web.ctx.environ['HTTP_AUTHORIZATION'] = "Basic %s" % encoded
        retval = self.some_other_method('somevalue', 'baz')
        self.assertEquals(retval, 'baz')
         

if __name__ == '__main__':
    logging.root.addHandler(logging.StreamHandler())
    logging.root.setLevel(logging.ERROR)
    unittest.main()
