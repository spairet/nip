# Features of NIP
All features examples will be presented in the following structure:
1. small description of the feature.
2. side by side config and additional python file with classes or functions.
3. python script that uses this config along with its output. 

### Inline python
Sometimes you may want to add some small python expression to your config.
You can use inline with backticks ``.
It also works with variables created in the config.
Actually it allows you to write all your code in config file

<table><tr><th>config.nip</th></tr>
<tr><td>

```yaml
const: &const 1
base: &base @ [2, 3, 4]
power: &power 2
value: `const * base ** power`
```
</td></tr></table>

>```python
>import nip
>
>for obj in nip.load("config.nip"):
>    print(obj['value'], end=' ')
>```
>4 9 16

### Non sequential construction
You don't need to worry about order of the variables in the config with this option.
Currently it is used by default but you can turn it off by passing `nonsequential=False` to `load` or `construct` functions.
All objects are constructed only once and passed by reference. You can see it in the example below.

<table><tr><th>config.nip</th><th>builder.py</th></tr>
<!-- <tr><td> -->


</td><td>

```yaml
some_list: &list
  - 1
  - 2
  - *number
  - 4

some_dict:
  also_list: *list
  secret_number: &number !get_secret_number
```
</td><td>

```python
from nip import nip


@nip
def get_secret_number():
    print("Getting secret number.")
    return 3

```
</td></tr></table>

>```python
>import nip
>import builders
>
>result = nip.load("config.nip")
>assert result["some_list"][2] is result["some_dict"]["secret_number"]
>assert result["some_list"] is result["some_dict"]["also_list"]
>print(result)
>
>```
> Getting secret number.
> 
> {'some_list': [1, 2, 3, 4], 'some_dict': {'also_list': [1, 2, 3, 4], 'secret_number': 3}}


### Args and kwargs in the same node.
You can use args and kwargs in the same node. They will be passed correspondingly upon object construction. 
The node will be constructed as tuple of list and dict if it is not used under some Tag.
<table>
<tr><th>config.nip</th><th>builders.py</th></tr>
<tr><td>

```yaml
class: !MyCoolClass
    - class_name
    value: 123
simple_construction:
    - simple_name
    value: 321
``` 
</td><td>

```python
from nip import nip

@nip
class MyCoolClass:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name}: {self.value}"
```
</td></tr></table>

> main.py
>```python
>import builders
>import nip
>
>result = nip.load("config.nip")
>assert isinstance(result["class"], builders.MyCoolClass)
>print(result)
>```
> class_name: 123
> 
> {'class': <builders.MyCoolClass object at 0x0000014CB1CED160>, 'simple_construction': (['simple_name'], {'value': 321})}

