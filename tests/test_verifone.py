#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `verifone` package."""


import unittest
import logging
import os
from datetime import datetime
from verifone import verifone

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

# logging
http_client.HTTPConnection.debuglevel = 1
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
        cls._verifone_client = verifone.Verifone(os.environ.get('AGREEMENTCODE'), os.environ.get('RSAPRIVATEKEY'), os.environ.get('RSAVERIFONEPUBLICKEY'), "IntegrationTest", "6.0.37")
        cls._test_requests = os.environ.get('TESTSENDINGREQUEST')
        cls._verifone_client_2 = verifone.Verifone(os.environ.get('AGREEMENTCODE'), os.environ.get('RSAPRIVATEKEY'), os.environ.get('RSAVERIFONEPUBLICKEY'), "IntegrationTest", "6.0.37", return_error_dict=1)

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
        default_currency = 'EUR'
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'euro')
        self.assertEqual(verifone_cl._currency, default_currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eu1')
        self.assertEqual(verifone_cl._currency, default_currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', '€')
        self.assertEqual(verifone_cl._currency, default_currency)

        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'abc')
        self.assertNotEqual(verifone_cl._currency, default_currency)

    def test_004_create_object_currency_lower(self):
        """ Test creating a new object with currency in lower case """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl._currency, 'EUR')

    def test_005_update_currency(self):
        """ Test that currency is updated """
        new_value = "SEK"
        self._verifone_client.currency = new_value
        self.assertEqual(self._verifone_client._currency, new_value)

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "Euro"

        with self.assertRaises(ValueError):
            self._verifone_client.currency = ""

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "kr3"

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "€"

        new_value = "abc"
        self._verifone_client.currency = new_value
        self.assertEqual(self._verifone_client._currency, new_value.upper())

        self._verifone_client._currency = "abc"
        with self.assertRaises(ValueError):
            self._verifone_client.currency

        new_value = "eur"
        self._verifone_client.currency = new_value
        self.assertEqual(self._verifone_client._currency, new_value.upper())
        self.assertEqual(self._verifone_client.currency, '978')

    def test_006_is_available(self):
        """ Test connection to Verifone server """
        if (self._test_requests == "1"):
            response = self._verifone_client.is_available()
            self.assertTrue(response['i-f-1-1_availability'] == '2')

            self._verifone_client._test_mode = 1
            response = self._verifone_client.is_available()
            self.assertTrue(response['i-f-1-1_availability'] == '2')

    def test_007_get_payment_methods(self):
        """ Test to get all available payment methods """
        if (self._test_requests == "1"):
            response = self._verifone_client.list_payment_methods()
            self.assertIsNotNone(response['s-t-1-30_payment-method-code-0'])

    def test_008_list_saved_payment_methods(self):
        """ Test to get saved payment methods """
        if (self._test_requests == "1"):
            params = {
                's-f-1-30_buyer-first-name': 'Test',
                's-f-1-30_buyer-last-name': 'Tester',
                's-f-1-100_buyer-email-address': os.environ.get('EMAIL'),
                's-t-1-30_buyer-phone-number': '123456789',
                's-t-1-255_buyer-external-id': os.environ.get('EXTERNALID'),
            }
            response = self._verifone_client.list_saved_payment_methods(params)
            self.assertTrue('l-t-1-20_payment-method-id-0' in response)

    def test_009_remove_saved_payment_method(self):
        """ Test to remove saved payment method when saved payment method is wrong """
        if (self._test_requests == "1"):
            response = self._verifone_client.remove_saved_payment_method(123456)
            self.assertEqual(response['l-t-1-10_removed-count'], '0')

    def test_010_generate_payment_data(self):
        """ Test to generate payment data """
        customer_id = '1234567890asdfghjklp-1234567890zxcvbnmklo'
        note = "Note"

        params = {
            'order_number': '58459',
            'order_timestamp': '2018-08-02 09:14:12',
            'payment_timestamp': '2018-08-02 11:59:16',
            'locale': 'fi_FI',
            'amount_gross': 1.51,
            'amount_net': 1.22,
            'vat_amount': 0.29,
            'first_name': 'Test',
            'last_name': 'Tester',
            'email': 'test@test.test',
            'phone': '1212121212121212',
            'address': 'Test Street 4',
            'postal_code': 33200,
            'city': 'Tampere',
            'country': 'fi',
            'style': '',
            'cancel_url': 'https://cancel.url',
            'error_url': 'https://error.url',
            'expired_url': 'https://expired.url',
            'rejected_url': 'https://rejected.url',
            'success_url': 'https://success.url',
            'success_url_server': 'https://server.success.url',
            'save_method': 3,
            'payment_method': 'nordea-e-payment',
            'customer_id': customer_id,
            'note': note,
            'products': [
                {
                    'name': 'er_7142303001',
                    'pieces': 1,
                    'discount': 0,
                    'vat': 24.00,
                    'amount_gross': 1.51,
                    'amount_net': 1.22,
                    'unit_cost_gross': 1.51,
                },
            ],
            'dynamic_feedback': 's-t-1-4_error-code,i-t-6-6_card-pan-first6,i-t-4-4_card-pan-last4',
        }

        data = self._verifone_client.generate_payment_data(params)
        self.assertTrue('s-t-256-256_signature-one' in data)
        self.assertIsNotNone(data['s-t-256-256_signature-one'])
        self.assertTrue('s-t-256-256_signature-two' in data)
        self.assertIsNotNone(data['s-t-256-256_signature-two'])

        self.assertEqual(data['l-f-1-20_order-gross-amount'], 151)
        self.assertEqual(data['l-f-1-20_order-net-amount'], 122)
        self.assertEqual(data['l-f-1-20_order-vat-amount'], 29)
        self.assertEqual(data['s-t-1-255_buyer-external-id'], customer_id)
        self.assertEqual(data['s-t-1-36_order-note'], note)
        self.assertIsNotNone(data['s-t-1-1024_dynamic-feedback'])

    def test_011_generate_payment_data(self):
        """ Test to generate payment data when all data is not defined """
        params = {
            'order_number': '58459',
            'locale': 'fi_FI',
            'first_name': 'Test',
            'last_name': 'Tester',
            'email': 'test@test.test',
            'cancel_url': 'https://cancel.url',
            'error_url': 'https://error.url',
            'expired_url': 'https://expired.url',
            'rejected_url': 'https://rejected.url',
            'success_url': 'https://success.url',
            'success_url_server': 'https://server.success.url',
            'skip_confirmation': 1,
            'country': '246',
            'products': [
                {
                    'name': 'er_7142303001',
                    'pieces': 1,
                    'vat': 24.00,
                },
            ]
        }

        data = self._verifone_client.generate_payment_data(params)
        self.assertTrue('s-t-1-30_style-code' in data)
        self.assertTrue('i-t-1-1_skip-confirmation-page' in data)
        self.assertEqual(data['i-t-1-1_skip-confirmation-page'], 1)
        self.assertEqual(data['i-t-1-3_delivery-address-country-code'], '246')

    def test_012_generate_payment_link(self):
        """ Test to generate payment link """
        if (self._test_requests == "1"):
            params = {
                'locale-f-2-5_payment-locale': 'fi_FI',
                't-f-14-19_order-expiry-timestamp': '2018-10-02 09:14:12',
                's-f-1-36_order-number': '1234',
                't-f-14-19_order-timestamp': '2018-08-03 04:58:22',
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
                's-t-1-30_delivery-address-line-one': "Test Street 3",
                's-t-1-30_delivery-address-city': "Tampere",
                's-t-1-30_delivery-address-postal-code': "33210",
                'i-t-1-3_delivery-address-country-code': 'fi',
                's-t-1-30_bi-name-0': 'Test Product',  # can be 0-50 items
                'l-t-1-20_bi-unit-gross-cost-0': '7602',
                'i-t-1-11_bi-unit-count-0': '1',
                'l-t-1-20_bi-gross-amount-0': '7602',
                'l-t-1-20_bi-net-amount-0': '6131',
                'i-t-1-4_bi-vat-percentage-0': '2400',
                'i-t-1-4_bi-discount-percentage-0': 0,
            }
            with self.assertRaises(ValueError):
                self._verifone_client.generate_payment_link(params)

            result = self._verifone_client_2.generate_payment_link(params)
            self.assertTrue('s-f-1-30_error-message' in result)

    def test_013_get_payment_link_status(self):
        """ Test to get payment link status. """
        if (self._test_requests == "1"):
            with self.assertRaises(ValueError):
                self._verifone_client.get_payment_link_status(12345678)
            
            result = self._verifone_client_2.get_payment_link_status(12345678)
            self.assertTrue('s-f-1-30_error-message' in result)

    def test_014_reactivate_payment_link(self):
        """ Test to reactivate payment link. """
        if (self._test_requests == "1"):
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

            with self.assertRaises(ValueError):
                self._verifone_client.reactivate_payment_link(12345678, timestamp)
            
            result = self._verifone_client_2.reactivate_payment_link(12345678, timestamp)
            self.assertTrue('s-f-1-30_error-message' in result)

    def test_015_process_payment(self):
        """ Test to process payment """
        if (self._test_requests == "1"):
            params = {
                's-f-1-30_buyer-first-name': 'Test',
                's-f-1-30_buyer-last-name': 'Tester',
                's-f-1-100_buyer-email-address': os.environ.get('EMAIL'),
                's-t-1-30_buyer-phone-number': '123456789',
                's-t-1-255_buyer-external-id': os.environ.get('EXTERNALID'),
            }
            response = self._verifone_client.list_saved_payment_methods(params)
            saved_payment_id = response['l-t-1-20_payment-method-id-0']
            self.assertIsNotNone(saved_payment_id)

            params = {
                'locale-f-2-5_payment-locale': 'fi_FI',
                's-f-1-36_order-number': '1234',
                'l-f-1-20_order-gross-amount': 2391,
                's-f-1-30_buyer-first-name': "Test",
                's-f-1-30_buyer-last-name': "Tester",
                's-t-1-30_buyer-phone-number': 123456789,
                's-f-1-100_buyer-email-address': os.environ.get('EMAIL'),
                's-t-1-30_delivery-address-line-one': "Test Street 3",
                's-t-1-30_delivery-address-city': "Tampere",
                's-t-1-30_delivery-address-postal-code': "33210",
                'i-t-1-3_delivery-address-country-code': 'FI',
                's-t-1-30_bi-name-0': 'Test Product',
                'l-t-1-20_bi-unit-gross-cost-0': 2391,
                'i-t-1-11_bi-unit-count-0': 1,
                'l-t-1-20_bi-gross-amount-0': 2391,
                'l-t-1-20_bi-net-amount-0': 1928,
                'i-t-1-4_bi-vat-percentage-0': 2400,
                'i-t-1-4_bi-discount-percentage-0': 0,
                's-t-1-255_buyer-external-id': os.environ.get('EXTERNALID'),
                'l-t-1-20_saved-payment-method-id': saved_payment_id,
            }
            response = self._verifone_client.process_payment(params)
            self.assertTrue('l-f-1-20_transaction-number' in response)
            self.assertIsNotNone(response['l-f-1-20_transaction-number'])

    def test_016_list_transaction_numbers(self):
        """ Test to get transaction numbers for one order. """
        if (self._test_requests == "1"):
            response = self._verifone_client.list_transaction_numbers("1234")
            self.assertTrue('l-f-1-20_transaction-number-0' in response)

    def test_017_get_payment_status(self):
        """ Test to get payment status """
        if (self._test_requests == "1"):
            response = self._verifone_client.list_transaction_numbers("1234")
            transaction_id = response['l-f-1-20_transaction-number-0']
            self.assertIsNotNone(transaction_id)

            params = {
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_transaction-number': transaction_id,
            }

            response = self._verifone_client.get_payment_status(params)
            self.assertTrue('s-f-1-30_payment-status-code' in response)

    def test_018_refund_payment(self):
        """ Test to refund payment """
        if (self._test_requests == "1"):
            response = self._verifone_client.list_transaction_numbers("1234")
            transaction_id = response['l-f-1-20_transaction-number-0']
            self.assertIsNotNone(transaction_id)

            params = {
                'l-f-1-20_refund-amount': 1,
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_transaction-number': transaction_id,
            }

            response = self._verifone_client.refund_payment(params)
            self.assertTrue('l-f-1-20_transaction-number' in response)

    def test_019_cancel_payment(self):
        """ Test to cancel payment. """
        if (self._test_requests == "1"):
            params = {
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_transaction-number': '123456',
            }
            with self.assertRaises(ValueError):
                self._verifone_client.cancel_payment(params)
            
            result = self._verifone_client_2.cancel_payment(params)
            self.assertTrue('s-f-1-30_error-message' in result)

    def test_020_process_supplementary(self):
        """ Test to process supplementary. """
        if (self._test_requests == "1"):
            params = {
                'l-f-1-20_original-transaction-number': '123456',
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_order-gross-amount': 500,
            }
            with self.assertRaises(ValueError):
                self._verifone_client.process_supplementary(params)

            result = self._verifone_client_2.process_supplementary(params)
            self.assertTrue('s-f-1-30_error-message' in result)
            self.assertEqual(result['s-f-1-30_error-message'],'invalid-transaction-number')


    def test_021_get_endpoint(self):
        """ Test for getting endpoints """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl.endpoint, 'https://epayment1.point.fi/pw/serverinterface')
        self.assertEqual(verifone_cl.endpoint2, 'https://epayment2.point.fi/pw/serverinterface')

        verifone_cl.test_mode = 1
        self.assertEqual(verifone_cl.endpoint, 'https://epayment.test.point.fi/pw/serverinterface')
        self.assertEqual(verifone_cl.endpoint2, 'https://epayment.test.point.fi/pw/serverinterface')

    def test_022_save_test_mode(self):
        """ Test for save test mode """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl.test_mode, 0)

        verifone_cl.test_mode = 1
        self.assertEqual(verifone_cl.test_mode, 1)

        with self.assertRaises(ValueError):
            verifone_cl.test_mode = 3

        verifone_cl.test_mode = None
        self.assertEqual(verifone_cl.test_mode, 0)

    def test_023_get_endpoint(self):
        """ Test for getting post urls """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl.posturl, 'https://epayment1.point.fi/pw/payment')

        self.assertEqual(verifone_cl.posturl1, 'https://epayment1.point.fi/pw/payment')
        self.assertEqual(verifone_cl.posturl2, 'https://epayment2.point.fi/pw/payment')

        verifone_cl.test_mode = 1
        self.assertEqual(verifone_cl.posturl, 'https://epayment.test.point.fi/pw/payment')
        self.assertEqual(verifone_cl.posturl1, 'https://epayment.test.point.fi/pw/payment')
        self.assertEqual(verifone_cl.posturl2, 'https://epayment.test.point.fi/pw/payment')

    def test_024_build_product_data(self):
        """ Test building product data """
        params = [{
            'name': 'er_7142303001',
            'pieces': 1,
            'discount': 10,
            'vat': 24.00,
            'amount_net': 1.22,
            'unit_cost_gross': 1.51,
        }]
        response = self._verifone_client.build_product_data(params)
        self.assertTrue('l-t-1-20_bi-unit-gross-cost-0' in response)
        self.assertTrue('l-t-1-20_bi-net-amount-0' in response)
        self.assertEqual(response['i-t-1-4_bi-discount-percentage-0'], 1000)

        params = [{
            'name': 'er_7142303001',
            'pieces': 1,
            'vat': 24.00,
        }]
        response = self._verifone_client.build_product_data(params)
        self.assertEqual(response['i-t-1-4_bi-discount-percentage-0'], 0)
        self.assertEqual(response['i-t-1-4_bi-vat-percentage-0'], 2400)
        self.assertEqual(response['i-t-1-11_bi-unit-count-0'], 1)

    def test_025_verify_response(self):
        """ Test to verify response with extra data. """
        response = {
            'i-f-1-11_interface-version': '5',
            'l-f-1-20_request-id': '2018102613094825567',
            'l-f-1-20_response-id': '2018102613094825567',
            'l-f-1-20_transaction-number': '2110929913',
            's-f-1-10_software-version': '1.74.1.238',
            's-f-1-30_operation': 'refund-payment',
            's-f-1-30_payment-method-code': 'visa',
            's-t-256-256_signature-one': '79C10BC83D94746C2A0859645EB476A73DBE2653C6B24C403CEB9017A759A330F7488AFF549E5AA861E8B6A8962B752B5066651F9C530277ABCAC04C25731EA17B220A638567403035B4A82D6C4CB96DE3F68DF0A089761030CF6766D7811B6895064C90DEC59A796BB3531D5F7C4C3E60B052D3642D35513D29EB89919F8434',
            's-t-256-256_signature-two': 'ACB93737CB1DB0D0C7DDCA62DFC921095D2465A751F39F95A9E660B423A4DBF83C7C50914E803019B9884388D336340E18D028F4D58B4C0320EBBC069D0F1402B028ECCB04AD615340670C200062A4C7BDBD2293C44B091E6379B253866BA751BACA133BA58A89125E58DF92E7ABE0E548521565DE05DBAFE5A487F9C9E451B7',
            't-f-14-19_response-timestamp': '2018-10-26 10:09:48',
            's-t-1-40_shop-order__phase': 'Takaisin tilaukseen'
        }

        result = self._verifone_client.verify_response(response) 
        self.assertTrue(result)

    def test_026_verify_incorrect_signature(self):
        """ Test to verify incorrect signature """
        result = self._verifone_client.verify_signature("signature", 'SHA123', "Test")
        self.assertFalse(result)

    def test_027_check_currency(self):
        """ Test that currency is valid """
        current_currency = self._verifone_client._currency 
        new_value = "123"
        currency = self._verifone_client.check_currency(new_value)
        self.assertEqual(current_currency, currency)


if __name__ == '__main__':
    unittest.main(verbosity=2)
