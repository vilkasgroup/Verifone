# -*- coding: utf-8 -*-

"""Main module."""
import logging
from datetime import datetime
from random import randrange
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA512, SHA, SHA256
from Crypto.Signature import PKCS1_v1_5
import binascii
import requests
import pycountry

try:
    import urllib.parse
except ImportError:
    import urllib

logs = logging.getLogger(__name__)


class Verifone(object):
    """ Class for Verifone payment API.

    Following packages need to be installed:
     - pycryptodome
     - pycountry
     - requests

    :param agreement_code: merchant agreement code, string with length of 1-36 characters
    :param RSA_private_key: RSA private key, string
    :param RSA_verifone_public_key: Verifone's RSA public key, string
    :param currency: currency code with three letters, default is EUR, string
    :param software_name: name of the web shop software, string with length of 1-30 characters
    :param version: version of the web shop software, string with length of 1-10 characters
    :param interface_version: version of the payment interface, string with length of 1-11 numeric characters
    :param test_mode: 1 if use test server, default is 0, boolean
    :param return_error_dict: if 1 then returns data received from Verifone also when error occurs. 
        If value is 0, then raise an error. Default is 0, boolean
    :rtype: object
    """
    _default_currency = 'EUR'

    def __init__(self, agreement_code, RSA_private_key, RSA_verifone_public_key, software_name, version, currency=_default_currency, interface_version='5', test_mode=0, return_error_dict=0):
        """ Initialize Verifone client. """
        currency = self.check_currency(currency)

        self._agreement_code = agreement_code
        self._RSA_private_key = RSA_private_key
        self._RSA_verifone_public_key = RSA_verifone_public_key
        self._software_name = software_name
        self._version = version
        self._interface_version = interface_version
        self._currency = currency
        self._test_mode = test_mode
        self._return_error_dict = return_error_dict

    @property
    def endpoint(self):
        """ Return endpoint.

        :return: endpoint, string
        """
        if self._test_mode:
            return 'https://epayment.test.point.fi/pw/serverinterface'
        return 'https://epayment1.point.fi/pw/serverinterface'

    @property
    def endpoint2(self):
        """ Return endpoint (node2). Verifone has 2 production environment URLs 
        so if first one does not answer, this can be used instead.

        :return: endpoint, string
        """
        if self._test_mode:
            return 'https://epayment.test.point.fi/pw/serverinterface'
        return 'https://epayment2.point.fi/pw/serverinterface'

    @property
    def posturl1(self):
        """ Return post url (Verifone node 1).

        :return: post url, string
        """
        if self._test_mode:
            return 'https://epayment.test.point.fi/pw/payment'
        return 'https://epayment1.point.fi/pw/payment'

    @property
    def posturl2(self):
        """ Return post url (Verifone node 2).

        :return: post url, string
        """
        if self._test_mode:
            return 'https://epayment.test.point.fi/pw/payment'
        return 'https://epayment2.point.fi/pw/payment'

    @property
    def posturl(self):
        """ Return post url. If production mode is used, then check that endpoint is available.
        If not use another endpoint.

        :return: post url, string
        """
        if self._test_mode:
            return 'https://epayment.test.point.fi/pw/payment'

        url = self.posturl1
        response = requests.post(url)
        logs.debug("Ping response from Verifone: %s", response)

        if response.status_code != 200:
            url = self.posturl2
            response = requests.post(url)
            logs.debug("Ping response from Verifone: %s", response)

        return url

    @property
    def test_mode(self):
        """ Return 1 if client is in test mode.

        :return: 1 if is in test mode, integer
        """
        return self._test_mode

    @test_mode.setter
    def test_mode(self, value):
        """ Method saves a new test_mode value.

        :param value: test mode, value can be 1 (test mode) or 0 (production), integer

        :return: None
        """
        if not value:
            value = 0
        elif value != 0 and value != 1:
            logs.debug("Wrong value for test mode")
            raise ValueError("Test mode can be 1 or 0")
        self._test_mode = value

    @property
    def currency(self):
        """ Method returns currency code.

        :return: currency, numeric ISO 4217 currency code
        """
        try:
            currency_data = pycountry.currencies.get(alpha_3 = self._currency)
        except KeyError:
            logs.debug("Wrong currency saved: " + self._currency)
            raise ValueError("Incorrect currency")

        if currency_data is None:
            raise ValueError("Incorrect currency")

        return currency_data.numeric

    @currency.setter
    def currency(self, value):
        """ Method saves a new currency code if value is defined and it is in a correct format.

        :param value: new currency code, with three letters
        :return: None
        """
        if not value:
            logs.debug("Mandatory currency can not be empty.")
            raise ValueError("Mandatory currency can not be empty")
        elif len(value) != 3:
            logs.debug("The length of the currency code is not 3.")
            raise ValueError("The length of the currency code is not 3")
        elif not value.isalpha():
            logs.debug("Only letters are allowed.")
            raise ValueError("Only letters are allowed")

        value = value.upper()

        try:
            pycountry.currencies.get(alpha_3 = value)
        except:
            raise ValueError("Incorrect currency")

        self._currency = value

    def check_currency(self, currency):
        """ Method checks that currency is a valid currency code. If not then
        default currency code is used.

        :param currency: new currency code, with three letters
        :return: currency code, with three letters
        """
        if (not currency) or (len(currency) != 3) or (not currency.isalpha()):
            logs.debug("Default currency is used instead of " + currency)
            currency = self._default_currency

        currency = currency.upper()

        try:
            pycountry.currencies.get(alpha_3 = currency)
        except KeyError:
            logs.debug("Default currency is used instead of " + currency)
            currency = self._default_currency

        return currency

    def is_available(self):
        """ Method can be used to test connectivity, signatures and requesting availability status of server interface.

        :return: response from Verifone, dictionary
            - i-f-1-1_availability: 0 = No access to Server Interface has been granted by Verifone
                                    1 = Express level access to Server Interface
                                    2 = Advanced level access to Server Interface
        """
        options = {
            "s-f-1-30_operation": "is-available",
        }

        return self.send_request(options)

    def list_payment_methods(self):
        """ Method gets available payment methods and their amount limits.

        :return: available payment methods, dictionary
            - s-t-1-30_payment-method-code-<N>: the payment method code
            - l-t-1-20_payment-method-min-<N>: minimum amount for the payment method
            - l-t-1-20_payment-method-max-<N>: maximum amount for the payment method
            - s-t-1-30_payment-method-type-<N>: type of the payment method
        """
        options = {
            "s-f-1-30_operation": "list-payment-methods",
            "i-f-1-3_currency-code": self.currency,
        }

        return self.send_request(options)

    def cancel_payment(self, data):
        """ Method cancels the payment

        :param data: data for cancelling, dictionary
            - s-f-1-30_payment-method-code: the used payment method code, string
            - l-f-1-20_transaction-number: transaction number identifying the payment transaction, string
            - s-t-1-1024_dynamic-feedback: list of parameters to be added to response if available (optional)
        :return: status for cancelling, dictionary
        """
        options = {
            "s-f-1-30_operation": "cancel-payment",
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def list_saved_payment_methods(self, data):
        """ Method gets saved payment methods for given buyer.

        :param data: data for search saved payment methods, dictionary
            - s-f-1-30_buyer-first-name: first name
            - s-f-1-30_buyer-last-name: last name
            - s-f-1-100_buyer-email-address: email address
            - s-t-1-30_buyer-phone-number: phone number (optional)
            - s-t-1-255_buyer-external-id: buyer's external id (optional)
            - s-t-1-30_delivery-address-line-one: street, 1-30 characters (optional)
            - s-t-1-30_delivery-address-line-two: delivery address extension, 1-30 characters (optional)
            - s-t-1-30_delivery-address-line-three: delivery address extension, 1-30 characters (optional)
            - s-t-1-30_delivery-address-city: city, 1-30 characters (optional)
            - s-t-1-30_delivery-address-postal-code: postal code, 1-30 characters (optional)
            - i-t-1-3_delivery-address-country-code: country code with 1-3 characters, ISO 3166 (optional)
            - s-t-1-30_recurring-payment-subscription: subscription code for recurring payment, 1-30 characters (optional)
        :return: available payment methods, dictionary
            - s-t-1-30_payment-method-code-<N>: the payment method code
            - l-t-1-20_payment-method-id-<N>: payment method id
            - s-t-1-30_payment-method-title-<N>: title for the payment method
            - s-t-1-6_card-expected-validity-<N>: card validity
        """
        options = {
            "s-f-1-30_operation": "list-saved-payment-methods",
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def remove_saved_payment_method(self, payment_id):
        """ Method removes saved payment method.

        :param payment_id: payment method id, integer
        :return: status for removing, dictionary
            - l-t-1-10_removed-count: 0 = Payment method not removed,
                                      1 = Payment method removed
        """
        options = {
            "s-f-1-30_operation": "remove-saved-payment-method",
            "l-t-1-20_saved-payment-method-id": payment_id,
        }

        return self.send_request(options)

    def refund_payment(self, data):
        """ Method refunds payment. Refund is supported for card, electronic and invoice payments.

        :param data: data for refunding, dictionary
            - l-f-1-20_refund-amount: amount to refund, integer
            - s-f-1-30_payment-method-code: the used payment method code, string
            - l-f-1-20_transaction-number: transaction number identifying the payment transaction, string
            - s-t-1-36_order-note: note for the payment, 1-36 characters (optional)
            - s-t-1-1024_dynamic-feedback: list of parameters to be added to response if available (optional)
        :return: status for refunding, dictionary
        """
        options = {
            "s-f-1-30_operation": "refund-payment",
            "i-f-1-3_refund-currency-code": self.currency,
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def process_payment(self, data):
        """ Method sends payment data to Verifone.

        :param data: data added to payment request, dictionary
            - locale-f-2-5_payment-locale: locale for the customer, string
            - t-f-14-19_payment-timestamp: UTC timestamp defining the payment start time, format is yyyy-MM-dd HH:mm:ss, string (optional)
            - s-f-1-36_order-number: order number, length is 1-36 characters, string
            - t-f-14-19_order-timestamp: UTC time defining orders time in format yyyy-MM-dd HH:mm:ss, string (optional)
            - s-t-1-36_order-note: note, 1-36 characters (optional)
            - l-f-1-20_order-gross-amount: total amount including taxes and discount with two decimal precision (for example 100 means 1 EUR), integer
            - s-f-1-30_buyer-first-name: the first name of the customer with 1-30 characters, string
            - s-f-1-30_buyer-last-name: the last name of the customer with 1-30 characters, string
            - s-t-1-30_buyer-phone-number: the phone number of the customer with 1-30 characters, string (optional)
            - s-f-1-100_buyer-email-address: the email of the customer with 1-100 characters, string
            - s-t-1-255_buyer-external-id: identifier for the customer with 1-255 characters, string (optional)
            - s-t-1-30_delivery-address-line-one: delivery address, string (optional)
            - s-t-1-30_delivery-address-line-two: delivery address, string (optional)
            - s-t-1-30_delivery-address-line-three: delivery address, string (optional)
            - s-t-1-30_delivery-address-city: city for the delivery address, string (optional)
            - s-t-1-30_delivery-address-postal-code: postal code for the delivery address, string (optional)
            - i-t-1-3_delivery-address-country-code: country code of the delivery address, string with 2 character or numeric ISO 3166  (optional)
            - l-t-1-20_saved-payment-method-id: ID of the saved payment method with 1-20 characters, string (optional)
            - i-t-1-1_recurring-payment: is payment recurring payment, integer (optional)
                0: Not recurring payment
                1: Recurring payment
            - i-t-1-1_deferred-payment: is payment deferred payment, integer (optional)
                0: Not deferred payment
                1: Deferred payment
            - s-f-1-30_payment-method-code: used payment method, string
            - 0-50 basket items are supported
        :return: payment information returned from Verifone, dictionary
        """
        options = {
            "s-f-1-30_operation": "process-payment",
            "i-f-1-3_order-currency-code": self.currency,
        }

        current_datetime = datetime.utcnow()
        timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        if not 't-f-14-19_payment-timestamp' in data:
            data['t-f-14-19_payment-timestamp'] = timestamp

        if not 't-f-14-19_order-timestamp' in data:
            data['t-f-14-19_order-timestamp'] = timestamp

        if 'i-t-1-3_delivery-address-country-code' in data and data['i-t-1-3_delivery-address-country-code'].isalpha():
            country_data = pycountry.countries.get(alpha_2 = data['i-t-1-3_delivery-address-country-code'])
            data['i-t-1-3_delivery-address-country-code'] = country_data.numeric

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def process_supplementary(self, data):
        """ Method trigger process supplementary.

        :param data: data added request, dictionary
            - l-f-1-20_original-transaction-number: transaction number for which supplementary will be initiated
            - s-f-1-30_payment-method-code: payment method code
            - l-f-1-20_order-gross-amount: amount for which supplementary auth will be triggered
            - s-t-1-36_order-note: note (optional)
        :return: information returned from Verifone, dictionary
            - l-t-1-20_transaction-number: transaction number
            - s-t-1-30_payment-method-code: payment method code
            - i-t-1-3_order-currency-code: currency code
            - l-t-1-20_order-gross-amount: gross amount including tax with two decimal
        """
        options = {
            "s-f-1-30_operation": "process-supplementary",
            "i-f-1-3_order-currency-code": self.currency,
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def get_payment_status(self, data):
        """ Method gets payment status.

        :param data: data for status inquiry, dictionary
            - s-f-1-30_payment-method-code: the used payment method code, string
            - l-f-1-20_transaction-number: transaction number identifying the payment transaction, string
        :return: status for the payment, dictionary
        """
        options = {
            "s-f-1-30_operation": "get-payment-status",
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def list_transaction_numbers(self, order_number):
        """ Method lists transaction numbers of one order.

        :param order_number: order number, string
        :return: transaction information, dictionary
            - l-f-1-20_transaction-number-<N>: transaction number
            - s-f-1-30_payment-method-code-<N>: payment method code
        """
        options = {
            "s-f-1-30_operation": "list-transaction-numbers",
            "s-f-1-36_order-number": order_number,
        }

        return self.send_request(options)

    def generate_payment_link(self, data):
        """ Method generates payment link.

        :param data: parameters for request, dictionary
            - locale-f-2-5_payment-locale: locale for the customer, string
            - t-f-14-19_order-expiry-timestamp: UTC time when the payment link expires in format yyyy-MM-dd HH:mm:ss, string
            - s-f-1-36_order-number: order number, length is 1-36 characters, string
            - t-f-14-19_order-timestamp:  UTC time defining orders time in format yyyy-MM-dd HH:mm:ss, string
            - s-t-1-36_order-note: note, 1-36 characters (optional)
            - l-f-1-20_order-gross-amount: total amount including taxes and discount with two decimal precision (for example 100 means 1 EUR), integer
            - l-f-1-20_order-net-amount: amount without discount or taxes, integer
            - l-f-1-20_order-vat-amount: VAT amount, integer
            - s-t-1-30_payment-method-code: used payment method, string (optional)
            - s-t-1-36_payment-link-number: number of the payment link in 1-36 characters, string (optional)
            - s-f-1-32_payment-link-delivery-mode: delivery mode of the payment link, supported values are sms or email, string
            - s-f-1-30_buyer-first-name: the first name of the customer with 1-30 characters, string
            - s-f-1-30_buyer-last-name: the last name of the customer with 1-30 characters, string
            - s-t-1-30_buyer-phone-number: the phone number of the customer with 1-30 characters, string (optional)
            - s-f-1-100_buyer-email-address: the email of the customer with 1-100 characters, string
            - s-t-1-255_buyer-external-id: identifier for the customer with 1-255 characters, string (optional)
            - s-t-1-30_delivery-address-line-one: delivery address, string (optional)
            - s-t-1-30_delivery-address-line-two: delivery address, string (optional)
            - s-t-1-30_delivery-address-line-three: delivery address, string (optional)
            - s-t-1-30_delivery-address-city: city for the delivery address, string (optional)
            - s-t-1-30_delivery-address-postal-code: postal code for the delivery address, string (optional)
            - i-t-1-3_delivery-address-country-code: country code of the delivery address, string with 2 character or numeric ISO 3166  (optional)
            - l-t-1-20_saved-payment-method-id: ID of the saved payment method with 1-20 characters, string (optional)
            - i-t-1-1_deferred-payment: is payment deferred payment, integer (optional)
                0: Not deferred payment
                1: Deferred payment
            - s-t-1-160_additional-delivery-text: text included in link email or SMS with 1-160 characters, string (optional)
            - s-t-1-128_sender-email: This address will be shown as sender in the link email, 1-128 characters, string (optional)
            - 0-50 basket items are supported
        :return: payment link information, dictionary
            - s-t-1-36_payment-link-number: created payment-link-number
        """
        if 'i-t-1-3_delivery-address-country-code' in data and data['i-t-1-3_delivery-address-country-code'].isalpha():
            country_data = pycountry.countries.get(alpha_2 = data['i-t-1-3_delivery-address-country-code'].upper())
            data['i-t-1-3_delivery-address-country-code'] = country_data.numeric

        options = {
            "s-f-1-30_operation": "generate-payment-link",
            "i-f-1-3_order-currency-code": self.currency,
        }

        # merge data to request options
        options.update(data)

        return self.send_request(options)

    def get_payment_link_status(self, link_number):
        """ Method get payment link status.

        :param link_number: payment link number with 1-36 characters
        :return: payment link information, dictionary
            - s-t-1-36_payment-link-number: payment link number
            - s-t-1-36_payment-link-status: payment link status (new, used, expired, canceled)
            - t-f-14-19_order-expiry-timestamp: expiry time
            - t-f-14-19_payment-timestamp: payment timestamp when link was used or canceled
        """
        options = {
            "s-f-1-30_operation": "get-payment-link-status",
            "s-t-1-36_payment-link-number": link_number,
        }

        return self.send_request(options)

    def reactivate_payment_link(self, link_number, expiry_date):
        """ Method reactivates payment link or changes the expiry date. Note that Verifone sends an email to the payer.

        :param link_number: payment link number with 1-36 characters
        :param expiry_date: expiration timestamp in format yyyy-MM-dd HH:mm:ss
        :return: payment link information, dictionary
            - s-t-1-36_payment-link-number: payment link number
        """
        options = {
            "s-f-1-30_operation": "reactivate-payment-link",
            "s-t-1-36_payment-link-number": link_number,
            "t-f-14-19_order-expiry-timestamp": expiry_date,
        }

        return self.send_request(options)

    def generate_payment_data(self, data):
        """ Method generates payment data which can be used in html form for showing payment button.

        :param data: data for the new payment, dictionary
            - order_number: order number, string
            - locale: locale for the customer. Supported: fi_FI, sv_SE, no_NO, dk_DK, sv_FI and en_GB. Other are redirected to en_GB
            - amount_gross: total amount including taxes with two decimal
            - amount_net: total amount without taxes, with two decimal
            - vat_amount: tax amount with two decimal
            - first_name: customer's first name, 1-30 characters, string
            - last_name: customer's last name, 1-30 characters, string
            - email: customer's email, 1-100 characters, string
            - phone: customer's phone number, max length is 30 character (optional)
            - address: line one of the delivery address, max length is 30 character (optional)
            - address2: line two of the delivery address, max length is 30 character (optional)
            - address3: line three of the delivery address, max length is 30 character (optional)
            - city: city of the delivery address, max length is 30 character (optional)
            - postal_code: postal code of the delivery address, max length is 30 character (optional)
            - country: country of the delivery address, with 2 letters or numeric ISO 3166 country code (optional)
            - style: code for the style sheet used in payment page, max length is 30 character (optional)
            - cancel_url: return URL if payment is cancelled, max length is 256 characters
            - error_url: return URL after error, max length is 256 characters
            - expired_url: return URL after expired situation, max length is 256 characters
            - rejected_url: return URL if payment is rejected, max length is 256 characters
            - success_url: return URL after success payment, max length is 256 characters
            - success_url_server: URL of the delayed success, max length is 256 characters
            - note: custom parameter reserved for shop system to use, max length is 36 characters (optional)
            - save_method: is customer's payment method saved (optional)
                0: normal payment. If customer uses credit card, 'save payment' button is shown on Verifone's page.
                1: payment method is saved if payment is succesful. If payment method is not given in request, only cards are shown to customer.
                2: payment method is only saved, so any payment is not charged.
                3: disable save payment options
            - customer_id: identifier for the customer (optional)
            - payment_method: selected payment method (optional)
            - products: product data, there can be 1-50 basket items
                - name: name of the basket item, max length is 30 character
                - pieces: number of units in the item, integer or float
                - discount: item discount percentage tax with two decimal, float or integer
                - vat: tax percentage with two decimal, float or integer
                - amount_gross: item gross amount including tax and discount with two decimal, float or integer
                - amount_net: item net amount calculated from unit cost times unit count with two decimal, float or integer
                - unit_cost_gross: unit cost with two decimal, with discount and tax
                - unit_cost: unit cost with two decimal and without tax and discounts, this must be filled if
                    unit gross cost is not filled, otherwise must not be used (optional)
            - payment_timestamp: the payment start time, format is yyyy-MM-dd HH:mm:ss (optional)
            - order_timestamp: the orders time from web shop point of view, format is yyyy-MM-dd HH:mm:ss (optional)
            - dynamic_feedback: comma separated list of optional parameters to be added to the response if available, string (optional)

        :return: generated payment data, dictionary
        """
        if data:
            current_datetime = datetime.utcnow()
            timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            if not 'payment_timestamp' in data:
                data['payment_timestamp'] = timestamp

            if not 'order_timestamp' in data:
                data['order_timestamp'] = timestamp

            payment_token = self.generate_token(data['order_number'], data['payment_timestamp'])

            if 'style' in data:
                style_code = data['style']
            else:
                style_code = ''

            if 'skip_confirmation' in data:
                skip_confirmation = data['skip_confirmation']
            else:
                skip_confirmation = 0

            values = {
                's-f-32-32_payment-token': payment_token,
                'locale-f-2-5_payment-locale': data['locale'],
                't-f-14-19_payment-timestamp': data['payment_timestamp'],
                't-f-14-19_order-timestamp': data['order_timestamp'],
                's-f-1-36_merchant-agreement-code': self._agreement_code,
                's-f-1-36_order-number': data['order_number'],
                'i-f-1-3_order-currency-code': self.currency,
                'i-t-1-4_order-vat-percentage': '', # set empty because there can be multiple VAT percentages in one payment
                's-f-1-30_buyer-first-name': self.get_substring(data['first_name'], 30),
                's-f-1-30_buyer-last-name': self.get_substring(data['last_name'], 30),
                's-f-1-100_buyer-email-address': self.get_substring(data['email'], 100),
                's-t-1-30_style-code': style_code,
                's-f-5-256_cancel-url':data['cancel_url'],
                's-f-5-256_error-url': data['error_url'],
                's-f-5-256_expired-url': data['expired_url'],
                's-f-5-256_rejected-url': data['rejected_url'],
                's-f-5-256_success-url': data['success_url'],
                's-t-5-256_change-server-to-server-success-url': data['success_url_server'],
                's-f-1-30_software': self._software_name,
                's-f-1-10_software-version': self._version,
                'i-f-1-11_interface-version': self._interface_version,
                'i-t-1-1_skip-confirmation-page': skip_confirmation,
            }

            if 'amount_gross' in data:
                values['l-f-1-20_order-gross-amount'] = self.format_to_integer(data['amount_gross'])

            if 'amount_net' in data:
                values['l-f-1-20_order-net-amount'] = self.format_to_integer(data['amount_net'])

            if 'vat_amount' in data:
                values['l-f-1-20_order-vat-amount'] = self.format_to_integer(data['vat_amount'])

            # Check optional fields, max length is 30 characters
            extra_fields = {
                'phone': 's-t-1-30_buyer-phone-number',
                'address': 's-t-1-30_delivery-address-line-one',
                'address2': 's-t-1-30_delivery-address-line-two',
                'address3': 's-t-1-30_delivery-address-line-three',
                'city': 's-t-1-30_delivery-address-city',
                'postal_code': 's-t-1-30_delivery-address-postal-code',
                'save_method': 'i-t-1-1_save-payment-method',
                'payment_method': 's-t-1-30_payment-method-code',
            }

            for key, field in extra_fields.items():
                if key in data:
                    values[field] = self.get_substring(data[key], 30)

            if 'country' in data:
                if data['country'].isalpha():
                    country_data = pycountry.countries.get(alpha_2 = data['country'].upper())
                    values['i-t-1-3_delivery-address-country-code'] = country_data.numeric
                else:
                    values['i-t-1-3_delivery-address-country-code'] = data['country']

            if 'customer_id' in data:
                values['s-t-1-255_buyer-external-id'] = self.get_substring(data['customer_id'], 255)

            if 'note' in data:
                values['s-t-1-36_order-note'] = self.get_substring(data['note'], 36)

            if 'dynamic_feedback' in data:
                values['s-t-1-1024_dynamic-feedback'] = self.get_substring(data['dynamic_feedback'], 1024)

            products = self.build_product_data(data['products'])
            values.update(products)

            # get signatures
            signature  = self.generate_signature(values, 'SHA1')
            signature2 = self.generate_signature(values, 'SHA512')
            values['s-t-256-256_signature-one'] = signature
            values['s-t-256-256_signature-two'] = signature2
            logs.debug("Values for payment: %s", values)

            return values

    def send_request(self, options):
        """ Method sends a request to Verifone and returns response.

        :param options: options for the request, dictionary
        :return: response from Verifone, dictionary
        """
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
        request_id = str(current_time.strftime('%Y%m%d%H%M%S'))+str(randrange(99999))

        data = {
            "l-f-1-20_request-id": request_id,
            "t-f-14-19_request-timestamp": timestamp,
            "s-f-1-36_merchant-agreement-code": self._agreement_code,
            "s-f-1-30_software": self._software_name,
            "s-f-1-10_software-version": self._version,
            "i-f-1-11_interface-version": self._interface_version,
        }

        # merge options to request data
        data.update(options)

        # get signatures
        signature  = self.generate_signature(data, 'SHA1')
        signature2 = self.generate_signature(data, 'SHA512')
        data['s-t-256-256_signature-one'] = signature
        data['s-t-256-256_signature-two'] = signature2
        logs.debug("Data for Verifone request: %s", data)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        url = self.get_endpoint_url()
        logs.debug('URL: ' + url)

        response = requests.post(url, headers=headers, data=data)
        logs.debug("Response from Verifone: %s", response)
        logs.debug("Content of Verifone response: %s", response.content)

        if response.status_code != 200:
            raise ConnectionError(str(response.content))
        elif not response.content:
            raise ValueError("No content returned")

        parsed_response = self.parse_response(response.content)

        if 's-f-1-30_error-message' in parsed_response:
            if self._return_error_dict:
                return parsed_response
            else:
                raise ValueError(parsed_response['s-f-1-30_error-message'])

        self.verify_response(parsed_response)

        return parsed_response
    
    def get_endpoint_url(self):
        """ Method returns endpoint url for server to server calls. Verifone has 2 production environment so 
        check first which one production server is available.

        :return: endpoint url, string
        """
        url = self.endpoint
        response = requests.post(url)
        logs.debug("Ping response from Verifone: %s", response)

        if response.status_code != 200:
            url = self.endpoint2
            response = requests.post(url)
            logs.debug("Ping response from Verifone: %s", response)

        return url

    def generate_signature(self, data, signature_type):
        """ Method generates digital signature from the given values.
        Algorithm is RSA with SHA1 or RSA with SHA512

        :param data: data for the request, dictionary
        :param signature_type: signature type, value can be "sha1" or "sha512, string
        :return: signature, 128 byte signature converted to upper case hexadecimal string
        """
        private_key = RSA.importKey(self._RSA_private_key)
        plaintext =  self.get_plaintext(data)

        digest = ''

        if signature_type == 'SHA512':
            digest = SHA512.new(plaintext)
        elif signature_type == 'SHA1':
            digest = SHA.new(plaintext)
        else:
            raise ValueError('WrongSignatureType')

        signer = PKCS1_v1_5.new(private_key)
        signature = signer.sign(digest)
        hex_signature = binascii.hexlify(signature)

        return hex_signature.upper()

    def get_plaintext(self, data):
        """ Method creates plaintext from dictionary.
        Algorithm is RSA with SHA1 or RSA with SHA512

        :param data: data for the request, dictionary
        :return: plain text, string
        """
        name_key_pairs = []

        # needed format is "key=value"
        for key, value in (sorted(data.items())):
            name_key_pairs.append(key + "=" + str(value))

        logs.debug("Names and keys for signature: %s", name_key_pairs)

        plaintext =  ';'.join(name_key_pairs) + ';'
        plaintext = plaintext.encode('utf-8')
        logs.debug("Plaintext for signature: " + str(plaintext))

        return plaintext

    def parse_response(self, content):
        """ Method parses response content returned from Verifone.

        :param content: response from Verifone, string
        :return: result, result from Verifone in dictionary
        """
        logs.debug("Content before parsing: %s", content)

        params = content.decode().split('&')
        result = {}

        for param in params:
            key, value = param.split('=')
            value = urllib.parse.unquote_plus(value) # for example times are in format: 2018-08-03+06%3A59%3A52
            result[key] = value

        logs.debug("Parsed content: %s", result)
        return result

    def generate_token(self, order_no, payment_timestamp):
        """ Method generates token for the payment.

        :param order_no: order number, string
        :param payment_timestamp: payment time stamp, string
        :return: generated token, string
        """
        elements = (self._agreement_code, order_no, payment_timestamp)
        plaintext = ';'.join(elements)
        logs.debug("Plaintext for generate token: %s", plaintext)

        plaintext = plaintext.encode('utf-8')
        token = SHA256.new(plaintext)
        token = token.hexdigest()
        logs.debug("Token: %s", token)

        return self.get_substring(token, 32).upper()

    def get_substring(self, string, length):
        """ Method returns substring from string if string is too length.

        :param string: string which length is checked, string
        :param length: max length, integer
        :return: substring, string
        """
        if type(string) != str:
            string = str(string)

        if len(string) > length:
            return string[0:length]

        return string

    def format_to_integer(self, number):
        """ Method formats number: 1.23 > 123.

        :param number: float or integer
        :return: formatted, integer
        """
        return int(round(number * 100))

    def build_product_data(self, data):
        """ Method build and returns product data.

        :param data: product items, dictionary
            - name: name of the basket item, max length is 30 character
            - pieces: number of units in the item, integer or float
            - discount: item discount percentage tax with two decimal, float or integer
            - vat: tax percentage with two decimal, float or integer
            - amount_gross: item gross amount including tax and discount with two decimal, float or integer
            - amount_net: item net amount calculated from unit cost times unit count with two decimal, float or integer
            - unit_cost_gross: unit cost with two decimal, with discount and tax, this must be filled if
                unit cost is not filled, otherwise must not be used (optional)
            - unit_cost: unit cost with two decimal and without tax and discounts, this must be filled if
                unit gross cost is not filled, otherwise must not be used (optional)
        :return: product data, dictionary
        """
        product_data = {}

        for i in range(len(data)):
            if 'discount' in data[i]:
                discount = data[i]['discount']
            else:
                discount = 0

            product_data['s-t-1-30_bi-name-'+ str(i)] = data[i]['name']
            product_data['i-t-1-11_bi-unit-count-'+ str(i)] = data[i]['pieces']
            product_data['i-t-1-4_bi-vat-percentage-'+ str(i)] = self.format_to_integer(data[i]['vat'])
            product_data['i-t-1-4_bi-discount-percentage-'+ str(i)] = self.format_to_integer(discount)

            if 'amount_net' in data[i]:
                product_data['l-t-1-20_bi-net-amount-'+ str(i)] = self.format_to_integer(data[i]['amount_net'])

            if 'amount_gross' in data[i]:
                product_data['l-t-1-20_bi-gross-amount-'+ str(i)] = self.format_to_integer(data[i]['amount_gross'])

            if 'unit_cost_gross' in data[i]:
                product_data['l-t-1-20_bi-unit-gross-cost-'+ str(i)] = self.format_to_integer(data[i]['unit_cost_gross'])

            if 'unit_cost' in data[i]:
                product_data['l-t-1-20_bi-unit-cost-'+ str(i)] = self.format_to_integer(data[i]['unit_cost'])

        return product_data

    def verify_response(self, data):
        """ Method verifies response from Verifone.

        :param data: parsed content from Verifone, dictionary
        :return: true if response is valid, boolean
        """
        values = data.copy()
        sign1 = values['s-t-256-256_signature-one']
        sign2 = values['s-t-256-256_signature-two']
        del values['s-t-256-256_signature-one']
        del values['s-t-256-256_signature-two']

        if 's-t-1-40_shop-order__phase' in values:
            del values['s-t-1-40_shop-order__phase']

        plaintext = self.get_plaintext(values)
        result = self.verify_signature(sign1, 'SHA1', plaintext)
        if not result:
            logs.debug("SHA1 verification failed for plaintext: " + str(plaintext))
            raise ValueError('SignatureVerificationFailed')

        result = self.verify_signature(sign2, 'SHA512', plaintext)
        if not result:
            logs.debug("SHA512 verification failed for plaintext: " + str(plaintext))
            raise ValueError('SignatureVerificationFailed')

        return True

    def verify_signature(self, signature, signature_type, plaintext):
        """ Method verifies Verifone's signature.

        :param signature: signature, string
        :param signature_type: signature type, supported are SHA1 and SHA512, string
        :param plaintext: plaintext, string
        :return: true if response is valid, boolean
        """
        digest = ''
        public_verifone = RSA.importKey(self._RSA_verifone_public_key)
        signer = PKCS1_v1_5.new(public_verifone)
        logs.debug("Plaintext for verifying: " + str(plaintext))

        if (signature_type == 'SHA1'):
            digest = SHA.new(plaintext)
        elif (signature_type == 'SHA512'):
            digest = SHA512.new(plaintext)

        if digest:
            return signer.verify(digest, binascii.unhexlify(signature))

        return False
