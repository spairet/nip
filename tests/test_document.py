from nip import load, parse
import builders

print(parse("configs/document.yaml"))

result = load("configs/document.yaml")
print(result)
