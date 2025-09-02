"""Source URL conversion and formatting utilities."""

def convert_source_to_url(source_path: str) -> str:
    """Convert source file path to website URL."""
    # Handle both full paths and relative paths
    if "src/content/" not in source_path:
        return ""
    
    # Extract the src/content/ portion and remove .mdx extension
    content_index = source_path.find("src/content/")
    path_parts = source_path[content_index + len("src/content/"):].replace(".mdx", "").replace(".md", "")
    
    # Build URL based on content type
    if path_parts.startswith("posts/"):
        # posts/post-2025-06-23 -> /posts/post-2025-06-23
        slug = path_parts.replace("posts/", "")
        return f"https://tcheiner.com/posts/{slug}"
    elif path_parts.startswith("projects/"):
        # projects/openai-chatbot -> /projects/openai-chatbot  
        slug = path_parts.replace("projects/", "")
        return f"https://tcheiner.com/projects/{slug}"
    elif path_parts.startswith("experiences/"):
        # experiences/manaburn -> /experiences/manaburn
        slug = path_parts.replace("experiences/", "")
        return f"https://tcheiner.com/experiences/{slug}"
    elif path_parts.startswith("books/"):
        # books/clear-thinking -> /books/clear-thinking
        slug = path_parts.replace("books/", "")
        return f"https://tcheiner.com/books/{slug}"
    elif path_parts.startswith("recipes/"):
        # recipes/beef-stew -> /recipes/beef-stew
        slug = path_parts.replace("recipes/", "")
        return f"https://tcheiner.com/recipes/{slug}"
    
    return ""

def format_sources_as_links(sources) -> str:
    """Convert source documents to formatted clickable links."""
    if not sources:
        return ""
    
    unique_sources = {}
    for doc in sources:
        source_path = doc.metadata.get("source", "")
        if source_path and source_path not in unique_sources:
            url = convert_source_to_url(source_path)
            if url:
                # Extract a display name from the path
                filename = source_path.split("/")[-1].replace(".mdx", "").replace(".md", "")
                # Convert post-2025-06-23 to readable format
                if filename.startswith("post-"):
                    display_name = "Blog Post"
                elif "manaburn" in filename.lower():
                    display_name = "ManaBurn Experience"
                elif "myndsens" in filename.lower():
                    display_name = "Myndsens Experience" 
                elif "stealth" in filename.lower():
                    display_name = "Stealth Startup Experience"
                elif "chatbot" in filename.lower():
                    display_name = "AI Chatbot Project"
                else:
                    # Default to title-case filename
                    display_name = filename.replace("-", " ").title()
                
                unique_sources[source_path] = f'• <a href="{url}" target="_blank">{display_name}</a>'
    
    if unique_sources:
        return "\n\n**Sources:**\n" + "\n".join(unique_sources.values())
    return ""