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
