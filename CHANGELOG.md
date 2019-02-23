## Changelog

#### 1.0.0

* First stable release.
* Added installer support.

#### 0.8.2

* Fix omitted destination field in `File` being the same as an empty string - it is now `None`.
* Fix multiline text not being fully parsed.

#### 0.8.1

* Fix missing warning for missing info.xml file.

#### 0.8.0

* Added support for `moduleImage` tag as `Image`.
* Reworked warnings:
  * No longer uses the native python `warnings`;
  * Warnings are now `ValidationWarning` objects;
  * The `validate` functions return a list of these objects;
  * You can pass a list as a keyword argument to `parse` to collect the
    warnings instead of passing `quiet`;
  * The user-defined callbacks for `validate` now should return a **single**
    warnings object.

#### 0.7.0

* Added group/option type warnings:
  * SelectAtMostOne/SelectExactlyOne group with multiple required options;
  * SelectAtLeastOne/SelectExactlyOne group with no selectable options.

#### 0.6.0

* Added a `CriticalWarning` for non-explicit order attributes.

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
