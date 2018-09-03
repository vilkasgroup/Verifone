#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `verifone` package."""


import unittest
import logging
import http.client
import os
from datetime import datetime
from verifone import verifone

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
        cls._verifone_client = verifone.Verifone(os.environ.get('AGREEMENTCODE'), os.environ.get('RSAPRIVATEKEY'), os.environ.get('RSAVERIFONEPUBLICKEY'), "IntegrationTest", "6.0.37")
        cls._test_requests = os.environ.get('TESTSENDINGREQUEST')

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
        self.assertEqual(verifone_cl._currency, default_currency)

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

        with self.assertRaises(ValueError):
            self._verifone_client.currency = "abc"

        self._verifone_client._currency = "abc"
        with self.assertRaises(ValueError):
            self._verifone_client.currency

        new_value = "eur"
        self._verifone_client.currency = new_value
        self.assertEqual(self._verifone_client._currency, new_value.upper())
        self.assertEqual(self._verifone_client.currency, '978')

    def test_006_is_available(self):
        """ Test connection to Verifone server """
        if (self._test_requests):
            response = self._verifone_client.is_available()
            self.assertTrue(response['i-f-1-1_availability'] == '2')

    def test_007_get_payment_methods(self):
        """ Test to get all available payment methods """
        if (self._test_requests):
            response = self._verifone_client.list_payment_methods()
            self.assertIsNotNone(response['s-t-1-30_payment-method-code-0'])

    def test_008_list_saved_payment_methods(self):
        """ Test to get saved payment methods """
        if (self._test_requests):
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
        if (self._test_requests):
            response = self._verifone_client.remove_saved_payment_method(123456)
            self.assertEqual(response['l-t-1-10_removed-count'], '0')

    def test_010_generate_payment_data(self):
        """ Test to generate payment data """
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
            ]
        }

        data = self._verifone_client.generate_payment_data(params)
        self.assertTrue('s-t-256-256_signature-one' in data)
        self.assertIsNotNone(data['s-t-256-256_signature-one'])
        self.assertTrue('s-t-256-256_signature-two' in data)
        self.assertIsNotNone(data['s-t-256-256_signature-two'])

    def test_011_generate_payment_link(self):
        """ Test to generate payment link """
        if (self._test_requests):
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
                'i-t-1-3_delivery-address-country-code': '246',
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

    def test_012_get_payment_link_status(self):
        """ Test to get payment link status. """
        if (self._test_requests):
            with self.assertRaises(ValueError):
                self._verifone_client.get_payment_link_status(12345678)

    def test_013_reactivate_payment_link(self):
        """ Test to reactivate payment link. """
        if (self._test_requests):
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

            with self.assertRaises(ValueError):
                self._verifone_client.reactivate_payment_link(12345678, timestamp)

    def test_014_process_payment(self):
        """ Test to process payment """
        if (self._test_requests):
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

    def test_015_list_transaction_numbers(self):
        """ Test to get transaction numbers for one order. """
        if (self._test_requests):
            response = self._verifone_client.list_transaction_numbers("1234")
            self.assertTrue('l-f-1-20_transaction-number-0' in response)

    def test_016_get_payment_status(self):
        """ Test to get payment status """
        if (self._test_requests):
            response = self._verifone_client.list_transaction_numbers("1234")
            transaction_id = response['l-f-1-20_transaction-number-0']
            self.assertIsNotNone(transaction_id)

            params = {
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_transaction-number': transaction_id,
            }

            response = self._verifone_client.get_payment_status(params)
            self.assertTrue('s-f-1-30_payment-status-code' in response)

    def test_017_refund_payment(self):
        """ Test to refund payment """
        if (self._test_requests):
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

    def test_018_cancel_payment(self):
        """ Test to cancel payment. """
        if (self._test_requests):
            params = {
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_transaction-number': '123456',
            }
            with self.assertRaises(ValueError):
                self._verifone_client.cancel_payment(params)

    def test_019_process_supplementary(self):
        """ Test to process supplementary. """
        if (self._test_requests):
            params = {
                'l-f-1-20_original-transaction-number': '123456',
                's-f-1-30_payment-method-code': 'visa',
                'l-f-1-20_order-gross-amount': 500,
            }
            with self.assertRaises(ValueError):
                self._verifone_client.process_supplementary(params)

    def test_020_get_endpoint(self):
        """ Test for getting endpoints """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl.endpoint, 'https://epayment1.point.fi/pw/serverinterface')

        verifone_cl.test_mode = 1
        self.assertEqual(verifone_cl.endpoint, 'https://epayment.test.point.fi/pw/serverinterface')

    def test_021_save_test_mode(self):
        """ Test for save test mode """
        verifone_cl = verifone.Verifone('test_apikey', '1234', 'Test', 'IntegrationTest', '6.0.37', 'eur')
        self.assertEqual(verifone_cl.test_mode, 0)

        verifone_cl.test_mode = 1
        self.assertEqual(verifone_cl.test_mode, 1)

        with self.assertRaises(ValueError):
            verifone_cl.test_mode = 3

if __name__ == '__main__':
    unittest.main(verbosity=2)
