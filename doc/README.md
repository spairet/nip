Documentation
----
This documentation will guide you through main features of nip.
All the corresponding code cna be found /tests directory

### Usual yaml behaviour
**NIP** inherits syntax and most of base functionality of yaml config files with a small differences.
Lets take a look at this config example.
```yaml
---

main: &main
  yaml_style_dict:
    string: "11"
    also_string: I am a string!
    float: 12.5
  yaml_style_list:
    - first item  # inline comment
    - 2
    -  
      - nested list value
  inline_list: [1, 2, 3]
  incline_dict: {'a': "123", 'b': 321}

main_copy: *main
```

Some differences from yaml:
- named list items are **forbidden**: casual yaml will create a single item dict for this code:
    ```yaml
    - nested_list
      - 1
      - 2
    ```
  And corresponding python object would be: `[{'nested_list': [1, 2]}]`
  
  In my opinion, this behaviour breaks the uniformity of nested list presentation, so this config will raise an error in **nip**.

- Keys of inline dict should be quoted. This is related to the realization detail that would be clarified later.

 