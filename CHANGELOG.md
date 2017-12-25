## Changelog

#### 0.3.1

* Updated custom fomod schema to be inline with the changes in 5.1

#### 0.3.0

* Added full fomod installer.
* General fomod metadata is now accessible in the `Root` object via properties.
* Improved `check_for_errors`'s output.
* `get_installer_files` now correctly raises `FileNotFoundError` instead of
  the generic `IOError`.

#### 0.2.0

* Added low-level API that allows for better control over the xml tree than
  plain lxml.

#### 0.1.0

* Initial release.
