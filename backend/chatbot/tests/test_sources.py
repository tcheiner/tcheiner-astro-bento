"""
Unit tests for source URL conversion and formatting

Tests convert_source_to_url and format_sources_as_links functions
"""

import pytest
from chatbot.sources import convert_source_to_url, format_sources_as_links
from langchain_core.documents import Document


class TestSourceConversion:
    """Test suite for source URL conversion"""

    # ========================================
    # convert_source_to_url Tests
    # ========================================

    def test_converts_post_path(self):
        """Should convert post path to URL"""
        path = "src/content/posts/post-2025-01-01.mdx"

        url = convert_source_to_url(path)

        assert "tcheiner.com/posts" in url
        assert "2025-01-01" in url

    def test_converts_project_path(self):
        """Should convert project path to URL"""
        path = "src/content/projects/ai-chatbot.mdx"

        url = convert_source_to_url(path)

        assert "tcheiner.com/projects" in url
        assert "ai-chatbot" in url

    def test_converts_experience_path(self):
        """Should convert experience path to URL"""
        path = "src/content/experiences/manaburn.mdx"

        url = convert_source_to_url(path)

        assert "tcheiner.com/experiences" in url
        assert "manaburn" in url

    def test_uses_custom_slug(self):
        """Should use custom slug if provided"""
        path = "src/content/projects/genAI-image-pipeline.mdx"
        custom_slug = "custom lora gen ai imagery"

        url = convert_source_to_url(path, custom_slug)

        assert "tcheiner.com/projects" in url
        assert "custom%20lora%20gen%20ai%20imagery" in url

    def test_url_encodes_slugs(self):
        """Should URL encode slugs with spaces"""
        path = "src/content/projects/test.mdx"
        slug = "my test project"

        url = convert_source_to_url(path, slug)

        assert "my%20test%20project" in url

    def test_removes_post_prefix(self):
        """Should remove 'post-' prefix from post slugs"""
        path = "src/content/posts/post-2025-01-01.mdx"

        url = convert_source_to_url(path)

        # Should have /posts/2025-01-01/, not /posts/post-2025-01-01/
        assert "/posts/2025-01-01/" in url
        assert "/posts/post-" not in url

    def test_preserves_custom_slug_post_prefix(self):
        """Should preserve custom slug even if it has 'post-' prefix"""
        path = "src/content/posts/post-2025-01-01.mdx"
        slug = "post-special-article"

        url = convert_source_to_url(path, slug)

        # Custom slug should be used as-is
        assert "post-special-article" in url

    def test_handles_invalid_path(self):
        """Should handle paths without src/content/"""
        path = "/invalid/path/file.mdx"

        url = convert_source_to_url(path)

        assert url == ""

    def test_handles_empty_path(self):
        """Should handle empty path"""
        url = convert_source_to_url("")

        assert url == ""

    def test_handles_none_path(self):
        """Should handle None path"""
        url = convert_source_to_url(None)

        assert url == ""

    def test_removes_mdx_extension(self):
        """Should remove .mdx extension"""
        path = "src/content/projects/test.mdx"

        url = convert_source_to_url(path)

        assert ".mdx" not in url

    def test_removes_md_extension(self):
        """Should remove .md extension"""
        path = "src/content/posts/test.md"

        url = convert_source_to_url(path)

        assert ".md" not in url

    def test_production_url_by_default(self):
        """Should use production URL by default"""
        path = "src/content/projects/test.mdx"

        url = convert_source_to_url(path)

        assert "https://tcheiner.com" in url
        assert "localhost" not in url

    def test_handles_books_path(self):
        """Should handle books content type"""
        path = "src/content/books/test-book.mdx"

        url = convert_source_to_url(path)

        assert "tcheiner.com/books" in url

    def test_handles_recipes_path(self):
        """Should handle recipes content type"""
        path = "src/content/recipes/test-recipe.mdx"

        url = convert_source_to_url(path)

        assert "tcheiner.com/recipes" in url

    def test_ends_with_slash(self):
        """URLs should end with trailing slash"""
        path = "src/content/projects/test.mdx"

        url = convert_source_to_url(path)

        assert url.endswith("/")

    # ========================================
    # format_sources_as_links Tests
    # ========================================

    @pytest.fixture
    def mock_documents(self):
        """Create mock document objects"""
        return [
            Document(
                page_content="Content 1",
                metadata={
                    "source": "src/content/projects/ai-chatbot.mdx",
                    "slug": "ai-chatbot"
                }
            ),
            Document(
                page_content="Content 2",
                metadata={
                    "source": "src/content/posts/post-2025-01-01.mdx",
                    "slug": None
                }
            ),
            Document(
                page_content="Content 3",
                metadata={
                    "source": "src/content/experiences/manaburn.mdx",
                    "slug": "manaburn"
                }
            )
        ]

    def test_formats_sources_as_links(self, mock_documents):
        """Should format sources as HTML links"""
        result = format_sources_as_links(mock_documents)

        assert "**Sources:**" in result
        assert '<a href=' in result
        assert 'target="_blank"' in result

    def test_includes_all_unique_sources(self, mock_documents):
        """Should include all unique sources"""
        result = format_sources_as_links(mock_documents)

        # Should have 3 links
        assert result.count('<a href=') == 3

    def test_deduplicates_sources(self):
        """Should remove duplicate sources"""
        docs = [
            Document(
                page_content="Content 1",
                metadata={"source": "src/content/projects/test.mdx"}
            ),
            Document(
                page_content="Content 2",
                metadata={"source": "src/content/projects/test.mdx"}  # Duplicate
            ),
        ]

        result = format_sources_as_links(docs)

        # Should only have 1 link
        assert result.count('<a href=') == 1

    def test_generates_display_names(self, mock_documents):
        """Should generate appropriate display names"""
        result = format_sources_as_links(mock_documents)

        # Should have display names (not just URLs)
        assert "AI Chatbot Project" in result or "Blog Post" in result

    def test_handles_empty_list(self):
        """Should handle empty document list"""
        result = format_sources_as_links([])

        assert result == ""

    def test_handles_none_input(self):
        """Should handle None input"""
        result = format_sources_as_links(None)

        assert result == ""

    def test_handles_missing_source_metadata(self):
        """Should handle documents without source metadata"""
        docs = [
            Document(
                page_content="Content",
                metadata={}  # No source
            )
        ]

        result = format_sources_as_links(docs)

        # Should not crash, may return empty or skip
        assert isinstance(result, str)

    def test_uses_custom_slugs(self):
        """Should use custom slugs from metadata"""
        docs = [
            Document(
                page_content="Content",
                metadata={
                    "source": "src/content/projects/genAI-image-pipeline.mdx",
                    "slug": "custom lora gen ai imagery"
                }
            )
        ]

        result = format_sources_as_links(docs)

        # URL should have encoded custom slug
        assert "custom%20lora%20gen%20ai%20imagery" in result

    def test_formats_with_bullet_points(self, mock_documents):
        """Should format with bullet points"""
        result = format_sources_as_links(mock_documents)

        # Should have bullet points (•)
        assert "•" in result

    def test_includes_newlines_between_sources(self, mock_documents):
        """Should separate sources with newlines"""
        result = format_sources_as_links(mock_documents)

        # Should have multiple lines
        assert result.count("\n") >= 3  # At least header + sources

    # ========================================
    # Edge Cases
    # ========================================

    def test_handles_very_long_path(self):
        """Should handle very long file paths"""
        long_path = "src/content/projects/" + "a" * 200 + ".mdx"

        url = convert_source_to_url(long_path)

        # Should still generate URL
        assert "tcheiner.com/projects" in url

    def test_handles_special_chars_in_filename(self):
        """Should handle special characters in filename"""
        path = "src/content/projects/test-project_2.0.mdx"

        url = convert_source_to_url(path)

        # Should URL encode special chars
        assert "tcheiner.com/projects" in url

    def test_handles_unicode_in_slug(self):
        """Should handle unicode characters in slug"""
        path = "src/content/projects/test.mdx"
        slug = "café-résumé"

        url = convert_source_to_url(path, slug)

        # Should URL encode unicode
        assert "tcheiner.com/projects" in url
        assert "caf" in url  # URL encoded

    def test_multiple_dots_in_filename(self):
        """Should handle multiple dots in filename"""
        path = "src/content/projects/test.project.v2.mdx"

        url = convert_source_to_url(path)

        # Should only remove final .mdx
        assert ".mdx" not in url
        assert "tcheiner.com/projects" in url
