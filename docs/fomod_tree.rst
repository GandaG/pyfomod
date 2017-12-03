##############
The Fomod Tree
##############

The tree API is useful for users who require more control over the installer
or need to do things with the installer that are not allowed in the higher-level API.

This API deals directly with the xml tree so `knowledge of xml is required <https://www.w3schools.com/xml/xml_whatis.asp>`_.
It is also an extension of `lxml's API <http://lxml.de/tutorial.html>`_ so familiarity with it is also necessary.

For a complete reference of the API, see the :doc:`generated API documentation <api/index>`

To start off, we'll import *pyfomod* as such::

    >>> import pyfomod


**********************
The FomodElement class
**********************

If you've followed the :doc:`tutorial <tutorial>`, then all the classes you've been handling
are actually real xml elements. They're all subclasses of the :class:`~pyfomod.tree.FomodElement`
class and each specializes in something related to their function in the installer.

Here we'll be talking about the API specific to this class and how to use it to get much
better control over your installers.


**************
Accessing data
**************

First, create a root element::

    >>> root = pyfomod.new()

This *root* is the root of the *ModuleConfig.xml* xml tree. We need to get the root of the
*info.xml* and rename *root* accordingly::

    >>> conf_root = root
    >>> info_root = conf_root.info_root

Looking up the element's children is done with the :meth:`~pyfomod.tree.FomodElement.children`
instead of lxml's ``list()``::

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>]

Looking at the xml tag::

    >>> conf_root.tag
    'config'

Now for something more interesting - let's see what the schema docs says about an element::

    >>> mod_name = conf_root[0]
    >>> mod_name.tag
    'moduleName'

    >>> mod_name.doc
    'The name of the module.'


**************************
Looking at predictive data
**************************

You can predict what data will be accepted by using predictive methods.

The maximum amount of times an element can be repeated::

    >>> mod_name.max_occurences
    1

The minimum amount an element has to be repeated::

    >>> mod_name.min_occurences  # this means it can't be removed!
    1

The acceptable text of an element::

    >>> print(conf_root.type)  # accepts no text!
    None

    >>> mod_name.type
    'string'

There are a few more methods that will be discussed in their appropriate sections.


********
Comments
********

*pyfomod* handles comments in a special way - each element can have an associated comment
that exists right before itself in the tree::

    <!--root's comment-->
    <root>
        <!--child's comment-->
        <child/>
    </root>

This also applies when parsing - comments that occur before an element are automatically applied
as its comment. Now for writing a comment::

    >>> conf_root.comment  # no comment present!
    ''

    >>> conf_root.comment = 'a comment for root'
    >>> conf_root.comment
    'a comment for root'

    >>> mod_name.comment = 'name comment'
    >>> _, conf_str = pyfomod.to_string(conf_root)
    >>> print(conf_str.decode('utf8'))
    <?xml version='1.0' encoding='utf-8'?>
    <!--a comment for root-->
    <config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
      <!--name comment-->
      <moduleName/>
    </config>

    >>> conf_root.comment = None  # remove the comment
    >>> _, conf_str = pyfomod.to_string(conf_root)
    >>> print(conf_str.decode('utf8'))
    <?xml version='1.0' encoding='utf-8'?>
    <config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
      <!--name comment-->
      <moduleName/>
    </config>


***************
Modifying trees
***************

The only way to create a new tree is with the :func:`~pyfomod.new` function.
However with the :meth:`~pyfomod.tree.FomodElement.add_child` you can create and add
new children to an element::

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>]

    >>> conf_root.add_child('installSteps')
    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element installSteps at 0x007c3644c2e5>]

    >>> conf_root.add_child('mychild')
    Traceback (most recent call last):
     ...
    ValueError: Child mychild can't be added to this element.

As you can see only a limited subset of children are acceptable within the schema. You can check if you can add a specific child::

    >>> conf_root.can_add_child('mychild')
    False

To fully list which ones you can add beforehand::

    >>> conf_root.valid_children()  # pretty printed for clarity
    OrderIndicator(type='sequence',
                   element_list=[ChildElement(tag='moduleName',
                                              max_occ=1,
                                              min_occ=1),
                                 ChildElement(tag='moduleImage',
                                              max_occ=1,
                                              min_occ=0),
                                 ChildElement(tag='moduleDependencies',
                                              max_occ=1,
                                              min_occ=0),
                                 ChildElement(tag='requiredInstallFiles',
                                              max_occ=1,
                                              min_occ=0),
                                 ChildElement(tag='installSteps',
                                              max_occ=1,
                                              min_occ=0),
                                 ChildElement(tag='conditionalFileInstalls',
                                              max_occ=1,
                                              min_occ=0)],
                   max_occ=1,
                   min_occ=1)

This may seem like a lot but it's actually pretty simple and it's also a good time to review
:data:`~pyfomod.tree.OrderIndicator` and :data:`~pyfomod.tree.ChildElement` if you haven't yet.

Essentially, it says the root element must be present one and only one time (the usual), that an
element tagged ``moduleName`` must be present one and only one time and at the start and that the
following element maybe be present at most once in the following order: ``moduleImage``,
``moduleDependencies``, ``requiredInstallFiles``, ``installSteps``, ``conditionalFileInstalls``.

This is incredibly useful if, for example, you're giving your users a choice in which elements to
add.

``installSteps`` was appended to the root element. So what if we need to add ``moduleDependencies``
now?

.. code-block:: python

   >>> conf_root.add_child('moduleDependencies')
   >>> conf_root.children()
   [<Element moduleName at 0x7f8498183ec8>,
    <Element moduleDependencies at 0x96fcdb69de4e>,
    <Element installSteps at 0x007c3644c2e5>]

*pyfomod* will automatically insert the new child in the approppriate index!

And now for the great thing about *pyfomod* - remember when we added ``installSteps``? This is
what really happened::

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element installSteps at 0x007c3644c2e5>]

    >>> _, conf_str = pyfomod.to_string(conf_root)
    >>> print(conf_str.decode('utf8'))
	<?xml version='1.0' encoding='utf-8'?>
	<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
	  <moduleName/>
	  <installSteps>
		<installStep name="">
		  <optionalFileGroups>
			<group name="" type="SelectAtLeastOne">
			  <plugins>
				<plugin name="">
				  <description/>
				  <files/>
				  <typeDescriptor>
					<dependencyType>
					  <defaultType name="Required"/>
					  <patterns>
						<pattern>
						  <dependencies>
							<fileDependency file="" state="Missing"/>
						  </dependencies>
						  <type name="Required"/>
						</pattern>
					  </patterns>
					</dependencyType>
				  </typeDescriptor>
				</plugin>
			  </plugins>
			</group>
		  </optionalFileGroups>
		</installStep>
	  </installSteps>
	</config>

*pyfomod* will keep validity at all costs - if you add a child that has required children or
required attributes then *pyfomod* will create those as well, fill them in to the best of its
knowledge, do same to their children and so on.

To remove a child::

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element moduleDependencies at 0x96fcdb69de4e>,
     <Element installSteps at 0x007c3644c2e5>]

    >>> moduleDependencies = conf_root[1]
    >>> moduleDependencies
    <Element moduleDependencies at 0x96fcdb69de4e>

    >>> conf_root.remove_child(moduleDependencies)
    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element installSteps at 0x007c3644c2e5>]

    >>> mod_name = conf_root[0]
    >>> mod_name
    <Element moduleName at 0x7f8498183ec8>

    >>> conf_root.remove_child(mod_name)
    Traceback (most recent call last):
     ...
    ValueError: Child cannot be removed by schema restrictions.

Oops, can't remove that one. We could have checked before::

    >>> conf_root.can_remove_child(mod_name)
    False

We could also have looked at the output from :meth:`~pyfomod.tree.FomodElement.valid_children`
to see which children are needed (those with minimum occurences > 0) but here it's simpler to
just check which ones are required::

    >>> conf_root.required_children()
    [('moduleName', 1)]

The ouput here is simply a list of tuples as (tag, minimum number of element), so you can see
we need at least one ``moduleName``.

Finally, we can replace children with children from other elements, including other trees::

    >>> new_tree = pyfomod.new()
    >>> new_tree.add_child('moduleImage')
    >>> new_tree.children()
    [<Element moduleName at 0x7f7864213bd8>,
     <Element moduleImage at 0x7f7864213d68>]

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element installSteps at 0x007c3644c2e5>]

    >>> conf_root.can_replace_child(conf_root[1], new_tree[1])
    True

    >>> conf_root.replace_child(conf_root[1], new_tree[1])
    >>> new_tree.children()
    [<Element moduleName at 0x7f7864213bd8>]

    >>> conf_root.children()
    [<Element moduleName at 0x7f8498183ec8>,
     <Element moduleImage at 0x7f7864213d68>]


***********************
Working with attributes
***********************

Much like with elements, you can check which attributes you can safely use::

    >>> root = pyfomod.new()
    >>> root.add_child('moduleImage')
    >>> root.children()
    [<Element moduleName at 0x7fd4fc04db88>,
     <Element moduleImage at 0x7fd4fc04dd68>]

    >>> mod_image = root.children()[1]
    >>> mod_image.valid_attributes()
    [Attribute(name='path',
               doc="The path to the image in the FOMod. If omitted the FOMod's screenshot is used.",
               default=None,
               type='string',
               use='optional',
               restriction=None),
     Attribute(name='showImage',
               doc='Whether or not the image should be displayed.',
               default='true',
               type='boolean',
               use='optional',
               restriction=None),
     Attribute(name='showFade',
               doc='Whether or not the fade effect should be displayed. This value is ignored if showImage is false.',
               default='true',
               type='boolean',
               use='optional',
               restriction=None),
     Attribute(name='height',
               doc="The height to use for the image. Note that there is a minimum height that is enforced based on the user's settings.",
               default='-1',
               type='int',
               use='optional',
               restriction=None)]

As you can see ``moduleImage`` has several attributes we can experiment with::

    >>> mod_image.set_attribute('path', 'random/image.png')
    >>> mod_image.get_attribute('path')
    'random/image.png'

    >>> mod_image.set_attribute('height', 'one')  # be careful with attribute type!
    Traceback (most recent call last):
     ...
    ValueError: value is not of an acceptable type.

    >>> mod_image.set_attribute('height', '1')
    >>> mod_image.get_attribute('height')
    '1'

    >>> mod_image.set_attribute('height', 1)  # you can pass integers directly
    >>> mod_image.get_attribute('height')
    '1'

    >>> mod_image.set_attribute('height', None)  # remove the attribute
    >>> mod_image.get_attribute('height')  # you'll get the default!
    '-1'

    >>> mod_image.set_attribute('boop', 'yay')  # not a valid attribute
    Traceback (most recent call last):
     ...
    ValueError: Attribute boop is not allowed by the schema.


*******************
Reordering elements
*******************

Whenever multiple children have the same tag they can be reordered::

    >>> root = pyfomod.new()
    >>> root.add_child('conditionalFileInstalls')
    >>> cond_file_inst = root.children()[1]
    >>> cond_file_inst
    <Element conditionalFileInstalls at 0x7f3108429ef8>

    >>> patterns = cond_file_inst.children()[0]
    >>> patterns
    <Element patterns at 0x7f3108429b38>

    >>> cond_file_inst.can_reorder_child(patterns, 0)  # pass 0 to simply check whether it can be reordered at all
    False

    >>> patterns.valid_children()
    OrderIndicator(type='sequence',
                   element_list=[ChildElement(tag='pattern',
                                              max_occ=None,
                                              min_occ=1)],
                   max_occ=1,
                   min_occ=1)

    >>> patterns.children()
    [<Element pattern at 0x7f3108269bd8>]

    >>> patterns.add_child('pattern')
    >>> patterns.add_child('pattern')
    >>> patterns.children()
    [<Element pattern at 0x7f3108269bd8>,
     <Element pattern at 0x7f3108281818>,
     <Element pattern at 0x7f3108281ea8>]

    >>> patterns.can_reorder_child(patterns.children()[0], 0)
    True

    >>> patterns.can_reorder_child(patterns.children()[0], 2)  # what about moving two spaces down?
    True

    >>> patterns.can_reorder_child(patterns.children()[0], 3)  # oops, 3 is too much! There's only two other children below
    False

    >>> patterns.reorder_child(patterns.children()[0], 1)  # move one down
    >>> patterns.children()  # compare the order with the previous call to .children() !!
    [<Element pattern at 0x7f3108281818>,
     <Element pattern at 0x7f3108269bd8>,
     <Element pattern at 0x7f3108281ea8>]


*************
Copying trees
*************

Much like *lxml*, :func:`~copy.copy` and :func:`~copy.deepcopy` do the same
thing - return a full copy of the copied element. This copy is orphaned, it
has no parent element and therefore has some limitations while orphaned:

- Cannot add children (:meth:`~pyfomod.tree.FomodElement.add_child`)
- Cannot access children (:meth:`~pyfomod.tree.FomodElement.children`,
  :meth:`~pyfomod.tree.FomodElement.remove_children`,
  :meth:`~pyfomod.tree.FomodElement.replace_children`,
  :meth:`~pyfomod.tree.FomodElement.reorder_children`)

Obviously this does not apply when copying the root element.

Whenever the orphaned element is reintegrated (for example, by adding it via
:meth:`~pyfomod.tree.FomodElement.add_child`) back into a proper tree all these
limiations no longer apply.


********************
Modifying the schema
********************

*pyfomod* packages the fomod schema and uses it by default. You can access the
schema using the :attr:`~pyfomod.tree.FomodElement._schema` attribute and the
schema element associated with the current element using
:attr:`~pyfomod.tree.FomodElement._schema_element`::

    >>> root = pyfomod.new()
    >>> root._schema
    <Element {http://www.w3.org/2001/XMLSchema}schema at 0x7f310871cd48>

    >>> root._schema_element
    <Element {http://www.w3.org/2001/XMLSchema}element at 0x7f310a08cf08>

    >>> from lxml import etree
    >>> print(etree.tostring(root._schema_element, pretty_print=True, encoding='unicode'))
    <xs:element xmlns:xs="http://www.w3.org/2001/XMLSchema" name="config" type="moduleConfiguration">
        <xs:annotation>
            <xs:documentation>The main element containing the module configuration info.</xs:documentation>
        </xs:annotation>
    </xs:element>

