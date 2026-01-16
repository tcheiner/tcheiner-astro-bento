"""Source URL conversion and formatting utilities."""

def convert_source_to_url(source_path: str, custom_slug: str = None) -> str:
    """Convert source file path to website URL.

    Args:
        source_path: File path of the source document
        custom_slug: Optional custom slug from frontmatter (overrides filename)
    """
    import os
    import urllib.parse

    # Handle both full paths and relative paths
    if "src/content/" not in source_path:
        return ""

    # Extract the src/content/ portion and remove .mdx extension
    content_index = source_path.find("src/content/")
    path_parts = source_path[content_index + len("src/content/"):].replace(".mdx", "").replace(".md", "")

    # Determine base URL based on environment
    # Check if running in development (localhost) or production
    is_development = os.environ.get("NODE_ENV") == "development" or os.environ.get("ENVIRONMENT") == "development"
    base_url = "http://localhost:4321" if is_development else "https://tcheiner.com"

    # Build URL based on content type
    if path_parts.startswith("posts/"):
        # posts/post-2025-06-23 -> /posts/2025-06-23/
        slug = custom_slug or path_parts.replace("posts/", "")
        # Remove "post-" prefix if present and no custom slug
        if not custom_slug and slug.startswith("post-"):
            slug = slug[5:]  # Strip "post-"
        return f"{base_url}/posts/{urllib.parse.quote(slug)}/"
    elif path_parts.startswith("projects/"):
        # Use custom slug if available, otherwise use filename
        slug = custom_slug or path_parts.replace("projects/", "")
        return f"{base_url}/projects/{urllib.parse.quote(slug)}/"
    elif path_parts.startswith("experiences/"):
        slug = custom_slug or path_parts.replace("experiences/", "")
        return f"{base_url}/experiences/{urllib.parse.quote(slug)}/"
    elif path_parts.startswith("books/"):
        slug = custom_slug or path_parts.replace("books/", "")
        return f"{base_url}/books/{urllib.parse.quote(slug)}/"
    elif path_parts.startswith("recipes/"):
        slug = custom_slug or path_parts.replace("recipes/", "")
        return f"{base_url}/recipes/{urllib.parse.quote(slug)}/"

    return ""

def format_sources_as_links(sources) -> str:
    """Convert source documents to formatted clickable links."""
    if not sources:
        return ""

    unique_sources = {}
    for doc in sources:
        source_path = doc.metadata.get("source", "")
        if source_path and source_path not in unique_sources:
            # Get custom slug from metadata if available
            custom_slug = doc.metadata.get("slug")
            url = convert_source_to_url(source_path, custom_slug)
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
                elif "genai" in filename.lower() or "image-pipeline" in filename.lower():
                    display_name = "Genai Image Pipeline"
                else:
                    # Default to title-case filename
                    display_name = filename.replace("-", " ").title()

                unique_sources[source_path] = f'• <a href="{url}" target="_blank">{display_name}</a>'

    if unique_sources:
        return "\n\n**Sources:**\n" + "\n".join(unique_sources.values())
    return ""