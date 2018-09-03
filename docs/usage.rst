=====
Usage
=====

To use Verifone in a project::

    import verifone


Using Verifone class
--------------------

.. code-block:: python

    from verifone import verifone

    # Create object
    verifone_client = Verifone('Agreement_code', 'Private_key', 'Verifone_public_key', 'software_name, 'version')

    # Test agreement code and keys. Check value in i-f-1-1_availability element (if 0 then no access to server).
    response = verifone_client.is_available()

    # If method needs a parameters, define them in dictionary
    params = {
        's-f-1-30_buyer-first-name': 'Test',
        's-f-1-30_buyer-last-name': 'Tester',
        's-f-1-100_buyer-email-address': 'tester@tester.email,
        's-t-1-30_buyer-phone-number': '123456789',
        's-t-1-255_buyer-external-id': '123456,
    }

    # Call method with parameters
    response = verifone_client.list_saved_payment_methods(params)

