.. image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================
CarePoint Connector
===================

This module provides CarePoint connector functionality.

The following two-way sync logic is implemented:

* Odoo Patient / CarePoint Patient

The following logic is impented on a one-way (CarePoint to Odoo) basis:

* Odoo Pharmacy / CarePoint Store
* Odoo Physician / CarePoint Doctor
* Odoo Prescription & Line / CarePoint Prescription
* Odoo Order / CarePoint Order
* Odoo Order Line / CarePoint Order Line
* Odoo NDC / FDB NDC
* Odoo GCN / FDB GCN
* Odoo Drug Form / FDB Form
* Odoo Dosage / FDB Unit
* Odoo Unit of Measure / FDB Strength
* Odoo Drug Route / FDB Route


Installation
============

To install this module, you need to:

* Install Python CarePoint library -
  ``pip install git+https://github.com/laslabs/Python-Carepoint.git``
* Install Vertical Medical v9 or above - https://github.com/OCA/vertical-medical
* Install OCA Connector module - https://github.com/OCA/connector
* Install Carepoint Connector module
* Restart Odoo (requirement of any new connector to set proper DB triggers)


Configuration
=============

To configure this module, you need to:

* Go to ``Connectors => [CarePoint] Backends``


Usage
=====

To use this module, you need to:

* Go to ...


Known Issues / Roadmap
======================

* More intelligent PK handling, and allowance of searches without
* Multiple DB connections not currently supported (namespace isolation required)
* Have to reboot server after reinstall to kill dup namespaces
* Medicament creation in NDC is bad & should use medicament importer instead
* Medicament category setting is not enforced - also need Rx/OTC delineation
* Add Rx/OTC Tax delineation
* ``import_dependency`` usage in ``_after_import`` should be replaced for delay
* Needs to be split into multiple modules to isolate dependencies


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/laslabs/odoo-connector-carepointissues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
please help us smash it by providing a detailed and welcomed feedback.


Credits
=======

Images
------

* LasLabs: `Icon <https://repo.laslabs.com/projects/TEM/repos/odoo-module_template/browse/module_name/static/description/icon.svg?raw>`_.

Contributors
------------

* Dave Lasley <dave@laslabs.com>

Maintainer
----------

.. image:: https://laslabs.com/logo.png
   :alt: LasLabs Inc.
   :target: https://laslabs.com

This module is maintained by LasLabs Inc.
