"""Editor API.

The intent is to allow in-place edits of YAML files while keeping the same file structure,
comments (if possible), ...

This is super tricky! Consider - if you want to edit a YAML file in-place,
you have to know what character span each value corresponds to.
That's a lot of metadata to track for each value... or computation to execute.
"""
