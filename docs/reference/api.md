# API Reference

## Reading and writing

::: pydantic_yaml
    options:
      members:
        - to_yaml_str
        - to_yaml_file
        - parse_yaml_raw_as
        - parse_yaml_file_as
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## Protocols

::: pydantic_yaml.engines
    options:
      members:
        - YamlReader
        - YamlWriter
        - YamlEngine
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## Built-in readers and writers

::: pydantic_yaml.engines
    options:
      members:
        - RuamelReader
        - RuamelWriter
        - YamlRocksReader
        - YamlRocksWriter
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## Default resolution

::: pydantic_yaml.engines
    options:
      members:
        - get_default_reader
        - set_default_reader
        - get_default_writer
        - set_default_writer
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
