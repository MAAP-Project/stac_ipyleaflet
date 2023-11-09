=======
History
=======

0.1.0 (2023-01-19)
------------------

* First release (beta).


0.2.0 (2023-05-19)
------------------

* First public release (beta).


0.3.0 (2023-08-30)
----------------------

* Added automatic COG filter to narrow down available collection (Issue #66)
* Added interact by point tool to get coordinates and raster values at a location (Issue #64)

0.3.1 (2023-08-31)
----------------------

* Patch to split STAC_CATALOG environment variable up to STAC_CATALOG_NAME and STAC_CATALOG_URL

0.3.2 (2023-09-01)
----------------------

* Bug fix to add dotenv to install_requires

0.3.3 (2023-09-06)
----------------------

* Bug fix to return collections even when non-compliant STAC collections and items exist

0.3.4 (2023-09-27)
----------------------

* Bug fix, agnostic parsing of STAC_BROWSER_URL (Issue #116)

0.3.5 (2023-09-27)
----------------------

* Bug fix, error in manifest of files to include in python package (#120)

Unreleased
----------------------

* Updated datasets for MAAP STAC
* Removed NASA JPL Biomass Layer
