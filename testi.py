import verifone
import unittest
import logging
import http.client
import os
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA512, SHA
from Crypto.Signature import PKCS1_v1_5
import binascii
import hashlib
from datetime import datetime
import rsa
from base64 import b64encode, b64decode

# logging
http.client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


class TestVerifone(unittest.TestCase):
    """ Test for Verifone package. """

    @classmethod
    def setUpClass(cls):
        """ Set up our Verifone client for tests. It requires the following environment variables: test_apikey TODO """
        cls._verifone_client = verifone.Verifone(os.environ.get('AGREEMENTCODE'), os.environ.get('RSAPRIVATEKEY'), os.environ.get('RSAVERIFONEPUBLICKEY'), "IntegrationTest", "6.0.37", test_mode=1)  #TODO tyhjennä ympäristömuuttujat ennen gittiin vientiä


    def test_006_is_availableTODO(self):
        """ Test connection to Verifone server """
        #response = self._verifone_client.is_available()
        #self.assertTrue(response['i-f-1-1_availability'] == '2')

        print("+++++++++++++++testi alkaa+++++++++++")
        #print(response)

        data = {
            't-f-14-19_response-timestamp': '2018-06-12+11%3A03%3A10',
            's-f-1-30_operation': 'is-available',
            's-f-1-10_software-version': '1.71.1.125',
            'i-f-1-11_interface-version': '5', 
            'i-f-1-1_availability': '2', 
            'l-f-1-20_request-id': '2018061214031073563', 
            'l-f-1-20_response-id': '2018061214031073563', 
        }

        sign1 = self._verifone_client.generate_signature(data, 'SHA1')
        print(sign1)

        #msg1 = b"Hello Tony, I am Jarvis!"
        #msg2 = "Hello Toni, I am Jarvis!"
        #keysize = 2048
        #private = RSA.importKey(os.environ.get('RSAPRIVATEKEY'))
        public = RSA.importKey(os.environ.get('TODOTEsti')) 
        signer = PKCS1_v1_5.new(public) 

        name_key_pairs = [] 

        # needed format is "key=value"
        for key, value in (sorted(data.items())):
            name_key_pairs.append(key + "=" + str(value))
        
        #logs.debug(name_key_pairs)

        plaintext =  ';'.join(name_key_pairs) + ';'
        plaintext = plaintext.encode('utf-8')
        print("Plaintext for signature verifying: " + str(plaintext))
        digest = SHA.new(plaintext) 
        
        result = signer.verify(digest, binascii.unhexlify(sign1))
        print(result)
        #return True
        print("+++++++###################### toimi tähän asti")
        #TODO yllä oleva toimii, 
        #TODO mutta miksi ei toimi verifonen avaimella


        publicverifone = RSA.importKey(os.environ.get('RSAVERIFONEPUBLICKEY')) 
        print(os.environ.get('RSAVERIFONEPUBLICKEY'))

        data2 = {
            'i-f-1-11_interface-version':'5',
            'i-f-1-3_order-currency-code':'978',
            'l-f-1-20_order-gross-amount':'1766',
            'l-f-1-20_transaction-number':'2103985313',
            's-f-1-10_software-version':'1.71.1.125',
            's-f-1-30_payment-method-code':'master-card',
            's-f-1-36_order-number':'55613',
            's-t-1-26_filing-code':'180612125511',
            's-t-1-6_card-expected-validity':'122037',
            't-f-14-19_order-timestamp':'2018-06-12 11:14:53',
        }
        name_key_pairs2 = [] 

        # needed format is "key=value"
        for key, value in (sorted(data2.items())):
            name_key_pairs2.append(key + "=" + str(value))
        
        #logs.debug(name_key_pairs)

        plaintext2 =  ';'.join(name_key_pairs2) + ';'
        plaintext2 = plaintext2.encode('utf-8')
        print("Plaintext for signature verifying: " + str(plaintext2))

        digest2 = SHA.new(plaintext2) 
        signature = '8265524018B82808C17F51824D6A94D4B935CE2090E450F4841DC1774A7CDA8C3430D24F5243A05A10E5F4699C45A9F45D7B6D0F21F128D83FC75B8E47BD9BB64FC6B3CF313BA9AB679DDD62104BA0581DD8E218F4561FD2188960CD84CD1CB47D4C1FC80F7A5E6D9780D60CFDED99B460382851130EBD349EB9B075296C0717'
        
        result2 = signer.verify(digest2, binascii.unhexlify(signature))
        print(result2)
        result2 = signer.verify(digest2, signature)
        print(result2)

        signature = signature.lower()
        print(signature)
        result2 = signer.verify(digest2, binascii.unhexlify(signature))
        print(result2)

        signature = '8FF85E6A4DF5C6747CC9C15C05E974E3CBFA3E1521CAD0D2018FFBD88B0B02D9EA2ADC7EFEC0B8EA7A0900C6BE3625635A50C835E196FEB0364B545D06D827610E259278D9EDA6E57B201C138549DB1A72F89A6D6AF80A1BE49C5B39CBC086FA80884EDCF98D8CE2D70E69088DCAD3C497ED974CD9A7A5C11ACD18B9800A603F'
        
        result2 = signer.verify(digest2, binascii.unhexlify(signature))
        print(result2)









if __name__ == '__main__':
    unittest.main(verbosity=2)
