import json

# Load the JSON file
with open('data.json', 'r') as file:
    data = json.load(file)

# Extract symbols and format as a set
symbols = {entry["SYMBOL"] for entry in data}

sorted_symbols = sorted(symbols)
# Convert the set to the desired string format
formatted_symbols = "{" + ", ".join(f'"{symbol.lower()}"' for symbol in sorted_symbols) + "}"

# Print the formatted output
print(formatted_symbols)
