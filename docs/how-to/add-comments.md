# Add Comments to YAML Output

Writing YAML models with comments has been
[a hotly-requested feature](https://github.com/NowanIlfideme/pydantic-yaml/issues/83),
as comments are one of the (many) features why YAML is nicer than JSON for human-facing
configuration. Comment generation is supported by both built-in
[writers](configure-readers-writers.md) - it's controlled by the `add_comments` field on whichever
writer object you pass, not a `to_yaml_str` argument.

## Adding Descriptions

The preferred way is to use `typing.Annotated` and `pydantic.Field` for fields, and just
docstrings for models:

```python
from typing import Annotated

from pydantic import BaseModel, Field

class MyModel(BaseModel):
    """My custom model."""  # This will become the header!

    c: Annotated[float, Field(description="See three?")] = 3  # description will become a comment
```

or via configuring the `model_config` to use docstrings as descriptions:

```python
class MyModel(BaseModel):
    """My custom model.""" # This will become the header!

    model_config = ConfigDict(use_attribute_docstrings=True)  # you can set this in your own BaseModel

    c: float = 3
    """See three?"""  # docstring will become description and comment; additional editor benefit!
```

Both of these options will work to create:

```python
from pydantic_yaml import RuamelWriter, to_yaml_str

mdl = MyModel(c=3.14)
print(to_yaml_str(mdl, writer=RuamelWriter(add_comments=True)))
```

with output:

```yaml
# My custom model.
c: 3.14  # See three?
```

See the Pydantic docs for more options on how to add descriptions:
[customizing the JSON schema](https://docs.pydantic.dev/latest/concepts/fields/#customizing-json-schema).

## More Options

Note that you can also export just the headers:

```python
print(to_yaml_str(mdl, writer=RuamelWriter(add_comments="models-only")))
```

```yaml
# My custom model.
c: 3.14
```

or just the fields:

```python
print(to_yaml_str(mdl, writer=RuamelWriter(add_comments="fields-only")))
```

```yaml
c: 3.14  # See three?
```

## Dumping Example Classes

If you just want to create example YAML files, you have several main options:

1. Create a fully-fledged example showing options. This might be time-consuming, but is probably
   best for your users.
2. "Construct" the example models using
   [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct)
   and use `None` for fields that are not optional but still need to be added.
   - Your docstrings and descriptions will still be used, so might be a bit confusing to users.
     Consider `RuamelWriter(add_comments="fields-only")`.
3. Create a parallel "documentation model" where you instruct users in your
   docstrings/descriptions (rather than document code) and have some examples (or `None`) as
   default values.
   - This is the most time-consuming, but gives you the most control.

Example of option 2:

```python
ex = MyModel.model_construct(c=None)
print(to_yaml_str(ex, writer=RuamelWriter(add_comments="fields-only")))
```

gives

```yaml
c:  # See three?
```

## Known limitations

Exact comment placement can differ slightly between the two built-in writers, and a field whose
*value* is a multiline string has a cosmetic placement quirk of its own - see
[Why pluggable readers and writers?](../explanation/engine-design.md#known-cross-engine-differences)
for the details.
