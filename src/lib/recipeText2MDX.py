import re

def parse_recipe(input_file, output_file):
    # Read the input text file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Initialize variables
    title = ""
    description = ""
    ingredients = []
    preparation = []
    yields = ""
    duration = 0
    slug = ""
    tags = []

    # Parsing state
    section = None

    # Parse each line
    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Determine section
        if line.lower().startswith("ingredients:"):
            section = "ingredients"
            continue
        elif line.lower().startswith("yield:"):
            section = "yield"
            yields = re.search(r"\d+", line).group()  # Extract servings
            continue
        elif line.lower().startswith("step"):
            section = "preparation"
            continue

        # Parse based on section
        if section == "ingredients":
            if line.lower() != "ingredients":
                ingredients.append(line)
        elif section == "preparation":
            preparation.append(line)
        elif section == "yield":
            # Already handled above
            pass

    # Generate metadata
    title = "Classic Beef Stew"
    description = "A hearty and comforting beef stew with tender meat, carrots, and potatoes simmered in a flavorful broth."
    slug = title.lower().replace(" ", "-")
    tags = ["beef", "stew", "comfort food"]
    duration = 150  # Approximate duration in minutes

    # Write to MDX file
    with open(output_file, 'w') as file:
        file.write(f"---\n")
        file.write(f"slug: \"{slug}\"\n")
        file.write(f"title: \"{title}\"\n")
        file.write(f"description: \"{description}\"\n")
        file.write(f"postDate: 2025-03-26\n")
        file.write(f"course: [\"main\"]\n")
        file.write(f"cuisine: [\"american\"]\n")
        file.write(f"duration: {duration}\n")
        file.write(f"yields: [{yields}]\n")
        file.write(f"ingredients: [\n")
        for ingredient in ingredients:
            file.write(f"    \"{ingredient}\",\n")
        file.write(f"]\n")
        file.write(f"preparation: [\n")
        for step in preparation:
            file.write(f"    \"{step}\",\n")
        file.write(f"]\n")
        file.write(f"tags: {tags}\n")
        file.write(f"---\n")

# Input and output file paths
input_file = "recipe.txt"  # Replace with your input file path
output_file = "recipe.mdx"  # Replace with your desired output file path

# Run the parser
parse_recipe(input_file, output_file)