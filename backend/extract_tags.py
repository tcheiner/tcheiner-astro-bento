#!/usr/bin/env python3
"""
Extract tags from all MDX files and update scoring_keywords.json
This script should be run after content changes to keep technical_skills current
"""

import os
import json
import re
from pathlib import Path

def extract_tags_from_mdx_files():
    """Extract all tags from MDX files in posts and experiences"""
    tags = set()
    
    # Define paths to search
    content_dirs = [
        "../src/content/posts",
        "../src/content/experiences", 
        "../src/content/projects"
    ]
    
    for content_dir in content_dirs:
        if not os.path.exists(content_dir):
            print(f"Warning: Directory {content_dir} not found, skipping")
            continue
            
        # Find all .mdx files
        for mdx_file in Path(content_dir).glob("*.mdx"):
            try:
                with open(mdx_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract tags using regex (handles both array and single line formats)
                # Match: tags: ["tag1", "tag2"] or tags: ["tag1",\n  "tag2"]
                tag_patterns = [
                    r'tags:\s*\[(.*?)\]',  # Single line: tags: ["a", "b"]
                    r'tags:\s*\[\s*(.*?)\s*\]',  # Multi-line: tags: [\n  "a",\n  "b"\n]
                ]
                
                for pattern in tag_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        # Extract individual tags from the match
                        tag_items = re.findall(r'"([^"]+)"', match)
                        for tag in tag_items:
                            # Clean and normalize tag
                            clean_tag = tag.strip().lower()
                            if clean_tag and len(clean_tag) > 1:  # Skip empty or single char
                                tags.add(clean_tag)
                                
            except Exception as e:
                print(f"Error processing {mdx_file}: {e}")
    
    return sorted(list(tags))

def update_scoring_keywords(new_technical_skills):
    """Update the scoring_keywords.json file with new technical skills"""
    keywords_file = "scoring_keywords.json"
    
    try:
        # Load existing keywords
        with open(keywords_file, 'r') as f:
            keywords = json.load(f)
        
        # Update technical_skills section
        keywords['technical_skills'] = new_technical_skills
        
        # Write back to file with nice formatting
        with open(keywords_file, 'w') as f:
            json.dump(keywords, f, indent=2, sort_keys=False)
        
        print(f"✅ Updated technical_skills in {keywords_file}")
        print(f"   Found {len(new_technical_skills)} unique tags")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: {keywords_file} not found")
        return False
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {keywords_file}")
        return False
    except Exception as e:
        print(f"❌ Error updating keywords: {e}")
        return False

def main():
    print("🔍 Extracting tags from MDX files...")
    
    # Extract all tags
    technical_skills = extract_tags_from_mdx_files()
    
    if not technical_skills:
        print("⚠️  No tags found in MDX files")
        return
    
    print(f"📝 Found tags: {', '.join(technical_skills[:10])}{'...' if len(technical_skills) > 10 else ''}")
    
    # Update keywords file
    if update_scoring_keywords(technical_skills):
        print("🎉 Successfully updated scoring keywords!")
        
        # Show some stats
        print(f"\n📊 Tag Statistics:")
        print(f"   Total unique tags: {len(technical_skills)}")
        
        # Show sample of tags by category
        ai_tags = [t for t in technical_skills if any(x in t for x in ['ai', 'ml', 'llm', 'nlp', 'gpt'])]
        cloud_tags = [t for t in technical_skills if any(x in t for x in ['aws', 'cloud', 'lambda', 'docker'])]
        web_tags = [t for t in technical_skills if any(x in t for x in ['react', 'javascript', 'css', 'html', 'web'])]
        
        if ai_tags:
            print(f"   AI/ML tags: {', '.join(ai_tags)}")
        if cloud_tags:
            print(f"   Cloud tags: {', '.join(cloud_tags)}")  
        if web_tags:
            print(f"   Web tags: {', '.join(web_tags[:5])}")
            
    else:
        print("❌ Failed to update scoring keywords")

if __name__ == "__main__":
    main()