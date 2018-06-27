import verifone
import unittest
import logging
import http.client
import os
from datetime import datetime

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
        """ Set up our Verifone client for tests. It requires the following environment variables: AGREEMENTCODE, RSAPRIVATEKEY and EMAIL """
        cls._verifone_client = verifone.Verifone(os.environ.get('AGREEMENTCODE'), os.environ.get('RSAPRIVATEKEY'), os.environ.get('RSAVERIFONEPUBLICKEY'), "IntegrationTest", "6.0.37")  #TODO tyhjennä ympäristömuuttujat ennen gittiin vientiä

    def test_001_create_object_with_defaults(self):
        """ Test creating a new object with default values """
        self.assertTrue(self._verifone_client._currency == "EUR")
        self.assertTrue(self._verifone_client._test_mode == 0)
    
    def test_002_get_endpoint(self):
        """ Test to get endpoint url and change to test mode """
        self.assertEqual(self._verifone_client.endpoint, 'https://epayment1.point.fi/pw/serverinterface')

        self._verifone_client._test_mode = 1
        self.assertEqual(self._verifone_client.endpoint, 'https://epayment.test.point.fi/pw/serverinterface')
        self.assertTrue(self._verifone_client._test_mode == 1)

    def test_003_create_object_wrong_currency(self):
        """ Test creating a new object with wrong currency, so default currency should be used """
        currency = 'EUR'
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', '6.0.37', 'euro')
        self.assertEqual(verifone_cl._currency, currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', '6.0.37', 'eu1')
        self.assertEqual(verifone_cl._currency, currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', '6.0.37', '€')
        self.assertEqual(verifone_cl._currency, currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', '6.0.37', 'abc')
        self.assertEqual(verifone_cl._currency, currency)

    def test_004_create_object_currency_lower(self):
        """ Test creating a new object with currency in lower case """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', '6.0.37', 'eur')
        self.assertEqual(verifone_cl._currency, 'EUR')

    def test_005_update_currency(self):
        """ Test that currency is updated """
        newvalue = "SEK"
        self._verifone_client.currency = newvalue
        self.assertEqual(self._verifone_client._currency, newvalue)

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "Euro"

        with self.assertRaises(ValueError):
            self._verifone_client.currency = ""

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "kr3"

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "€"

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "abc"
        
        self._verifone_client._currency = "abc"
        with self.assertRaises(ValueError):
            self._verifone_client.currency

        newvalue = "eur"
        self._verifone_client.currency = newvalue
        self.assertEqual(self._verifone_client._currency, newvalue.upper())
        self.assertEqual(self._verifone_client.currency, '978')

    def test_006_is_available(self):
        """ Test connection to Verifone server """
        response = self._verifone_client.is_available()
        self.assertTrue(response['i-f-1-1_availability'] == '2')

        verifone_cl = verifone.Verifone("123", os.environ.get('RSAPRIVATEKEY'), "IntegrationTest", "6.0.37")
        with self.assertRaises(ValueError):
            verifone_cl.is_available()

    def test_007_get_payment_methods(self):
        """ Test to get all available payment methods """
        response = self._verifone_client.list_payment_methods()
        self.assertIsNotNone(response['s-t-1-30_payment-method-code-0']) 

    def test_008_list_saved_payment_methods(self):       
        """ Test to get saved payment methods """

        params = {
            's-f-1-30_buyer-first-name': 'Test',
            's-f-1-30_buyer-last-name': 'Tester',
            's-f-1-100_buyer-email-address': os.environ.get('EMAIL'),
            's-t-1-30_buyer-phone-number': '123456789',
            's-t-1-255_buyer-external-id': 'B6A8D7C77477494D046BA708045323C9',  #TODO luo tämä
        }
        response = self._verifone_client.list_saved_payment_methods(params)
        self.assertTrue('l-t-1-20_payment-method-id-0' in response)
    
    def test_009_remove_saved_payment_method(self):       
        """ Test to remove saved payment method """
    
        response = self._verifone_client.remove_saved_payment_method(11586932) #TODO käytä tässä edellä testeissä luotua id:tä
        self.assertEqual(response['l-t-1-10_removed-count'], '1')
    
    def test_010_refund_payment(self):       
        """ Test to refund payment """

        params = {
            'l-f-1-20_refund-amount': '7982', #TODO summa edellisestä maksusta
            's-f-1-30_payment-method-code': 'nordea-e-payment', #TODO käytä tässä edellä testeissä luotua maksua
            'l-f-1-20_transaction-number': '2102129013', #TODO käytä tässä edellä testeissä luotua id:tä
        }
        
        with self.assertRaises(ValueError):
            response = self._verifone_client.refund_payment(params)
            self.assertTrue('s-f-1-30_error-message' in response)

    def test_011_get_payment_status(self):       
        """ Test to get payment status """

        params = {
            's-f-1-30_payment-method-code': 'nordea-e-payment', #TODO käytä tässä edellä testeissä luotua maksua
            'l-f-1-20_transaction-number': '2098350513', #TODO käytä tässä edellä testeissä luotua id:tä
        }
        
        response = self._verifone_client.get_payment_status(params)
        self.assertTrue('s-f-1-30_payment-status-code' in response)
    
    def test_012_list_transaction_numbers(self):       
        """ Test to get transaction numbers for one order. """        
        response = self._verifone_client.list_transaction_numbers("54607")  #TODO käytä tässä edellä testeissä luotua id:tä
        self.assertTrue('s-f-1-30_payment-status-code' in response)
    
    def test_013_cancel_payment(self):       
        """ Test to cancel payment. """        
        params = {
            's-f-1-30_payment-method-code': 'nordea-e-payment', #TODO käytä tässä edellä testeissä luotua maksua
            'l-f-1-20_transaction-number': '2098350513', #TODO käytä tässä edellä testeissä luotua id:tä
        }
        response = self._verifone_client.cancel_payment(params)  
        self.assertTrue('s-f-1-30_payment-status-code' in response)
    
    def test_014_process_payment(self):       
        """ Test to process payment """
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

        params = {
            'locale-f-2-5_payment-locale': 'fi_FI',
            's-f-1-36_order-number': '1234',
    #         't-f-14-19_order-timestamp': '2018-05-15 05:43:36', #TODO timestamp,
    #         't-f-14-19_payment-timestamp': '2018-05-15 05:43:36', #TODO perlissä tämäkin
            #'s-t-1-36_order-note': 'Test payment',
            'l-f-1-20_order-gross-amount': 2391,
            's-f-1-30_buyer-first-name': "Test",
            's-f-1-30_buyer-last-name': "Tester",
            's-t-1-30_buyer-phone-number': 123456789,
            's-f-1-100_buyer-email-address': os.environ.get('EMAIL'), 
    #         #'s-t-1-255_buyer-external-id': 12345, # TODO random luku
           's-t-1-30_delivery-address-line-one': "Test Street 3",
            #'s-t-1-30_delivery-address-line-two': "Apartment 10",
            #'s-t-1-30_delivery-address-line-three': "Room 1",
            's-t-1-30_delivery-address-city': "Tampere",
            's-t-1-30_delivery-address-postal-code': "33210",
            'i-t-1-3_delivery-address-country-code': 'FI',  # TODO testaa väärällä maalla
            #'l-t-1-20_saved-payment-method-id': '', #TODO testaa tälläkin
            #'i-t-1-1_recurring-payment': '', #TODO
            #'i-t-1-1_deferred-payment': , #TODO
            #'s-f-1-30_payment-method-code': 'visa', #TODO testaa tälläkin
            's-t-1-30_bi-name-0': 'Test Product',  # can be 0-50 items
            'l-t-1-20_bi-unit-gross-cost-0': 2391,
            'i-t-1-11_bi-unit-count-0': 1,
            'l-t-1-20_bi-gross-amount-0': 2391,
            'l-t-1-20_bi-net-amount-0': 1928,
            'i-t-1-4_bi-vat-percentage-0': 2400,
            'i-t-1-4_bi-discount-percentage-0': 0,
            's-t-1-255_buyer-external-id': 'B6A8D7C77477494D046BA708045323C9',  #TODO nämä luotava jotenkin
            'l-t-1-20_saved-payment-method-id': '11586932',   #TODO nämä luotava jotenkin
        }
        self._verifone_client.process_payment(params)
    #     #self.assertTrue(self._verifone_client.language == 'FI' and self._verifone_client.currency == "EUR") 

    def test_015_generate_payment_data(self):
        """ Test to generate payment data """
        params = {
            'order_number': '54719',
            'locale': 'fi_FI',
            'amount_gross': 79.82,
            'amount_net': 64.37,
            'vat_amount': 15.45,
            'first_name': 'Test',
            'last_name': 'Tester',
            'email': os.environ.get('EMAIL'),
            'phone': '1234567890',
            'address': 'Test Street 1',
            'postal_code': 33210,
            'city': 'Tampere',
            'country': 'fi',
            # #'style': 'test style',
            'cancel_url': 'https://cancel.url',
            'error_url': 'https://error.url',
            'expired_url': 'https://expired.url',
            'rejected_url': 'https://rejected.url',
            'success_url': 'https://success.url',
            'success_url_server': 'https://server.success.url',
            #'note': 'Test payment',
            'save_method': 3,
            #'customer_id': '1234567890',
            'payment_method': 'visa',
            'products': [
                {
                    'name': 'Product 1',
                    'pieces': 1,
                    'discount': 0,
                    'vat': 24.00,
                    'amount_gross': 76.02,
                    'amount_net': 61.31,
                    'unit_cost_gross': 76.02,
                },
                {
                    'name': 'Shipping cost',
                    'pieces': 1,
                    'discount': 0,
                    'vat': 24.00,
                    'amount_gross': 3.80,
                    'amount_net': 3.06,
                    'unit_cost_gross': 3.80,
                }
            ]
        }
        
        data = self._verifone_client.generate_payment_data(params)
        self.assertTrue('s-t-256-256_signature-one' in data)
        self.assertIsNotNone(data['s-t-256-256_signature-one']) 

    def test_016_generate_payment_link(self):     
        """ Test to generate payment link """
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

        params = {
            'locale-f-2-5_payment-locale': 'fi_FI',
            't-f-14-19_order-expiry-timestamp': timestamp,
            's-f-1-36_order-number': '1234',
            't-f-14-19_order-timestamp': timestamp, #TODO timestamp,
            's-t-1-36_order-note': 'Test payment',
            'i-f-1-3_order-currency-code': '978',
            'l-f-1-20_order-gross-amount': '7602',
            'l-f-1-20_order-net-amount': '6131',
            'l-f-1-20_order-vat-amount': '1471',
            's-t-1-30_payment-method-code': 'visa',
            's-t-1-36_payment-link-number': '1234567',
            's-f-1-32_payment-link-delivery-mode': 'email',
            's-f-1-30_buyer-first-name': "Test",
            's-f-1-30_buyer-last-name': "Tester",
            's-t-1-30_buyer-phone-number': '1234567890',
            's-f-1-100_buyer-email-address': os.environ.get('EMAIL'), 
            #'s-t-1-255_buyer-external-id': 12345, # TODO random luku
            's-t-1-30_delivery-address-line-one': "Test Street 3",
            #'s-t-1-30_delivery-address-line-two': "Apartment 10",
            #'s-t-1-30_delivery-address-line-three': "Room 1",
            's-t-1-30_delivery-address-city': "Tampere",
            's-t-1-30_delivery-address-postal-code': "20100",
            'i-t-1-3_delivery-address-country-code': '246',  # TODO testaa väärällä maalla
            #'l-t-1-20_saved-payment-method-id': koodi,
            #'i-t-1-1_deferred-payment,
            #'s-t-1-160_additional-delivery-text
            #'s-t-1-128_sender-email
            's-t-1-30_bi-name-0': 'Test Product',  # can be 0-50 items
            #'l-t-1-20_bi-unit-cost-0'
            'l-t-1-20_bi-unit-gross-cost-0': '7602',
            'i-t-1-11_bi-unit-count-0': '1',
            'l-t-1-20_bi-gross-amount-0': '7602',
            'l-t-1-20_bi-net-amount-0': '6131',
            'i-t-1-4_bi-vat-percentage-0': '2400',
            'i-t-1-4_bi-discount-percentage-0': 0,
        }
        self._verifone_client.generate_payment_link(params)

    def test_017_get_payment_link_status(self):       
        """ Test to get payment link status. """        
        response = self._verifone_client.get_payment_link_status(12345678)  #TODO käytä tässä edellä testeissä luotua id:tä
        #self.assertTrue('s-f-1-30_payment-status-code' in response)
    
    def test_018_reactivate_payment_link(self):       
        """ Test to reactivate payment link. """   
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

        response = self._verifone_client.reactivate_payment_link(12345678, timestamp)  #TODO käytä tässä edellä testeissä luotua id:tä
        self.assertTrue('s-f-1-30_payment-status-code' in response)
    
    def test_019_get_payment_link_status(self):       
        """ Test to get payment link status. """        
        params = {
            'l-f-1-20_original-transaction-number': '2101902713',
            's-f-1-30_payment-method-code': 'visa',
            'l-f-1-20_order-gross-amount': 500,
        }
        response = self._verifone_client.process_supplementary(params)  #TODO käytä tässä edellä testeissä luotua id:tä
        #self.assertTrue('s-f-1-30_payment-status-code' in response)

if __name__ == '__main__':
    unittest.main(verbosity=2)
