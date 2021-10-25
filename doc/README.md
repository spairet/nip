User Guide
----
This brief guide will walk you through main functionality and some extended features of **nip**.

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
>also_main: *main
>```

_Note:_ **nip** is not extension sensitive, so feel free to change extension to `.yml` for syntax highlighting. **Nip** doesn't have its own highlighting yet :cry: 

### Main functions
 
 - `parse("config.nip")` - parses config into `Element` that can be used easily in your code
 - `construct(element)` - constructs element into python object
 - `load("config.nip")` - parses config and constructs python object
 - `dump("save_config.nip", element)` - dumps element to a config file
 - `dumps(element)` - return dumped element as a string
 
### Constructing custom objects
Just like PyYAML, **nip** allows you to construct your own python objects from config. But in **nip** this is a way more easier. :yum:

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

Now you are able to construct them with a config file using tag operator `!`. List or dict that lies under tagged node will be passed as args and kwargs to the fucntion or class.
```yaml
class_object: !MyCoolClass
  question: Ultimate Question of Life, The Universe, and Everything
  answer: 42

func_value: !just_func
  - 1
  c: 4
```
So `load("config.nip")` will return the following dict:
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

### Iterable configs
It is a common case in experimentation, when you want to run a number of experiments with different parameters.
For this case iterable configs will help you a lot! :yum:

Using **nip** you are able to create elements that don't have a constant values but have an iterables instead. Let's take a look at this example:
```yaml
a: &a
  const: 1
  iter: @ [1, 2, 3]

b:
  a_copy: *a
  another_iter: @ [4, 5, 6]
```
`@` operator allows you to specify values that should be iterated.
Now `parse` and `load` functions will return an iterator over this configs and constructed objects respectively.
In this example there are two iterable objects, and so Cartesian product of all this iterables will be created.
This small code:
```python
from nip import load

for obj in load('config.nip'):
    print(obj)
```
will result in:
```python
{'a': {'const': 1, 'iter': 1}, 'b': {'a_copy': {'const': 1, 'iter': 1}, 'another_iter': 4}}
{'a': {'const': 1, 'iter': 1}, 'b': {'a_copy': {'const': 1, 'iter': 1}, 'another_iter': 5}}
{'a': {'const': 1, 'iter': 1}, 'b': {'a_copy': {'const': 1, 'iter': 1}, 'another_iter': 6}}
{'a': {'const': 1, 'iter': 2}, 'b': {'a_copy': {'const': 1, 'iter': 2}, 'another_iter': 4}}
{'a': {'const': 1, 'iter': 2}, 'b': {'a_copy': {'const': 1, 'iter': 2}, 'another_iter': 5}}
{'a': {'const': 1, 'iter': 2}, 'b': {'a_copy': {'const': 1, 'iter': 2}, 'another_iter': 6}}
{'a': {'const': 1, 'iter': 3}, 'b': {'a_copy': {'const': 1, 'iter': 3}, 'another_iter': 4}}
{'a': {'const': 1, 'iter': 3}, 'b': {'a_copy': {'const': 1, 'iter': 3}, 'another_iter': 5}}
{'a': {'const': 1, 'iter': 3}, 'b': {'a_copy': {'const': 1, 'iter': 3}, 'another_iter': 6}}
```
If you need to iterate some lists synchronously you can specify iter names: `@a [1, 2, 3]`. All the iterators with the same name will be iterated together. The order of iterators is determind by the alphabetic order of thier names.

_Note:_ All the iterators works with construction of your custom objects only once and using links in the config doesn't recreates the objects. See above example to clarify.

### Additional features 
There are some small but useful features also presented in **nip**:
1. Accessing parts of your config without full construction. Once you parsed your config
   ```python
   from nip import parse, construct
   config = parse("config.nip")
   ```
    you are able to access its parts using `[]` and construct only them: 
    ```python
   part = config['main']['yaml_style_list'][2]
   inner_list = construct(part)  # ['nested list value']
    ```
   This might be useful, for example, you want to load only your machine learning model using config of full training pipeline.
2. `to_python()` method. Every element in **nip** has `to_python` method. So, you can access any parameter of the config without constructing the objects:
    ```python
    from nip import parse
    config = parse('construct_exampe.nip')
    print(config['func_value']['c'].to_python())  #  4
    ```
3. `run()` function. This function will iterate over the configs and run your function multiple times. You should specify function you want to run at the top of the document.
   ```yaml
   --- !run_experiment
   model:
       ...
       num_layers: @ [3, 4, 5]
       ...
   dataset:
       ...
   ```
   And python code will look like this:
   ```python
   from nip import nip, run
   
   @nip
   def run_experiment(model, dataset):
       # some machine learning staff here
   
   run('experiment_config.nip')
   ```
   This will result in running a number of experiments using generated configs. 
4. Strict nip. Nip can check typing while constructing objects and keys overwriting in dicts. `strict` parameter of `load` function stands for it. By default only typing warnings are generated.


Most of the functions mentioned in this short documentation have additional parameters, so feel free to look into the docstrings. :yum:
