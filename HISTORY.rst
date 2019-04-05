=======
History
=======

0.1.14 (2019-04-05)
-------------------

* Updated Pipfile.lock and requirements.

0.1.13 (2019-04-01)
-------------------

* Updated Pipfile.lock and dev requirements.

0.1.12 (2019-03-26)
-------------------

* Updated Pipfile.lock and requirements.

0.1.11 (2019-02-28)
-------------------

* Modified Verifone class. New parameter "return_error_dict" was added.
* Updated test cases.

0.1.10 (2019-02-28)
-------------------

* Modified method "send_request". It does not throw anymore error if 's-f-1-30_error-message' is returned.
* Updated Pipfile.lock.

0.1.9 (2019-02-20)
------------------

* Updated Pipfile.lock.

0.1.8 (2019-01-07)
------------------

* Updated Pipfiles and requirement files. There was security issue in PyYAML module.

0.1.7 (2018-12-17)
------------------

* Length of 'dynamic_feedback' parameter in method 'generate_payment_data'.

0.1.6 (2018-12-17)
------------------

* Added 'dynamic_feedback' to method 'generate_payment_data'.

0.1.5 (2018-12-14)
------------------

* Changes in pycountry module which needed some changes also to Verifone's country and currency methods.

0.1.4 (2018-11-12)
------------------

* Fixed length of extra data fields. External id can be 255 characters and note 36 characters.

0.1.3 (2018-10-26)
------------------

* Remove s-t-1-40_shop-order__phase from signature verification.

0.1.2 (2018-09-12)
------------------

* Changes in generate_payment_data feature.


0.1.1 (2018-09-06)
------------------

* Added post urls for hosted pages.


0.1.0 (2018-08-31)
------------------

* First release on PyPI.
