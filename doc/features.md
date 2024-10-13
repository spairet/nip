# Features of NIP
All features examples will be presented in the following structure:
1. small description of the feature.
2. side by side config and additional python file with classes or functions.
3. python script that uses this config along with its output. 

### Inline python
Sometimes you may want to add some small python expression to your config.
It also works with variables created in the config.
Actually it allows you to write all your code in config file

<table><tr><th>config.nip</th><th>builders.py</th></tr>
<tr><td>

```yaml
const: &const 0.5
base: &base @ [2, 3, 4]
power: &power 2
value: `const * base ^ power`
``` 
</td><td>

```python

```
</td></tr></table>

### Non sequential construction
You don't need to worry about order of the variables in the config with this option.




### Args and kwargs in the same node.
You can use args and kwargs in the same node. They will be passed correspondingly upon object construction. 
The node will be constructed as tuple of list and dict if not used as arguments of some Tag.
<table>
<tr><th>config.nip</th><th>builders.py</th></tr>
<tr><td>

```yaml
!MyCoolClass
- some_name
value: 123
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
</td></tr>


</table>



> main.py
>    ```python
>    import builders
>    import nip
>    
>    obj = nip.load("config.nip")
>    assert isinstance(obj, builders.MyCoolClass)
>    print(obj)  # some_name: 123
>    ```
> some_name: 123

