## Changelog

#### 0.5.0

* `CriticalWarning`'s no longer have the extra little message at the end.
* Detected comments warning is now a `CriticalWarning`.
* Added a `CriticalWarning` for when *info.xml* is missing.
* Added a kwarg to `parse`, `lineno`, that when true provides the source
  line numbers to each element object at the cost of performance.

#### 0.4.0

* Complete project and API rework.
* Previous API has been entirely deprecated.

#### 0.3.3

* Removed second argument to `can_reorder_child` - movement is no longer
  restricted.
* Fixed installer module's documentation.

#### 0.3.2

* `FomodElement.add_child` now returns the added element.
* `FomodElement.add_child` should now create *type* element instead
  of *dependencyType* under *typeDescriptor* element.
* Added setters to metadata properties in `Root`.
* Attributes should now be handled correctly.

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
