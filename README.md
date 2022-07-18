# Pylogic


## Example

```python
a = Literal("P", True)
b = Literal("Q", True)

print(a | b)
print(~a | b)
print(~(a | b ))
```

Output:

```
P v Q
¬P v Q
¬P ^ ¬Q
```
