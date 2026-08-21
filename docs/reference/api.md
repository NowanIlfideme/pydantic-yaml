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

## Engines

::: pydantic_yaml.engines
    options:
      members:
        - YamlEngine
        - RuamelEngine
        - YamlRocksEngine
        - get_default_engine
        - set_default_engine
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
