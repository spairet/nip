Documentation
----
This documentation will guide you through main features of nip.
All the corresponding code cna be found /tests directory

### Usual yaml behaviour
**NIP** inherits syntax and most of base functionality of yaml config files with a small differences.
Lets take a look at this config example.
> config.nip
>```yaml
>---
>
>main: &main
>  yaml_style_dict:
>    string: "11"
>    also_string: I am a string!
>    float: 12.5
>  yaml_style_list:
>    - first item  # inline comment
>    - 2
>    -  
>      - nested list value
>  inline_list: [1, 2, 3]
>  incline_dict: {'a': "123", 'b': 321}
>
>main_copy: *main
>```

Some differences from yaml:
- named list items are **forbidden**: casual yaml will create a single item dict for this code:
    ```yaml
    - nested_list
      - 1
      - 2
    ```
  And corresponding python object would be: `[{'nested_list': [1, 2]}]`
  
  In my opinion, this behaviour breaks the uniformity of nested list presentation, so this config will raise an error in **nip**.

- Keys of inline dict should be quoted. This is related to the realization detail that would be clarified a bit later.

_Note:_ **nip** is not extension sensitive, so feel free to change extension to `.yml` for syntax highlighting. **Nip** doesn't have its own highlighting yet :cry: 

### Main functions
 
 - `parse("config.nip")` - parses config into `Element` that can be used easily in your code
 - `construct(element)` - constructs element into python object
 - `load("config.nip")` - parses config and constructs python object
 - `dump("save_config.nip", element)` - dumps element to a config file
 - `dumps(element)` - return dumped element as a string
 
### Constructing custom objects
Just like PyYAML, **nip** allows you to construct your own python objects from config. But in **nip** this is a way more easier.

First of all, you need to wrap you function or class with `@nip` decorator. For example:
```python
from nip import nip


@nip
class MyCoolClass:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer


@nip('just_func')
def MyCoolFunc(a, b=2, c=3):
    return a + b * 2 + c * 3
```

From now you are able to construct them with a config file using `!` operator:
```yaml
class_object: !MyCoolClass
  question: Ultimate Question of Life, The Universe, and Everything
  answer: 42

func_value: !just_func
  - 1
  c: 4
```
So `load("config.nip")` will return dict:
```yaml
{
  'class_object': <__main__.MyCoolClass object at 0x000001F6E13F1988>,
  'func_value': 17
}
```
_Note:_ if you specify your wrapped objects in other `.py` file, you have to import it before calling `load()`.


There is a number of features for this functionality:
1. `@nip` decorator allows you to specify name for the object to be used in config file (`just_func` in the example)
2. You can combine `args` and `kwargs` in the config. (`just_func` creation).

    _Actually you are able to create this combined element anywhere in the config, and it will be loaded as a tuple of list and dict._
3. You can  automatically wrap everything under module.
   Here are two variants of wrapping `source` module:
   ```python
   from nip import nip
   
   import source
   nip(source)
   ```
    ```python
    from nip import wrap_module
    
    wrap_module("source")
    ``` 
