#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Common MDX syntax issues that cause build failures
const mdxValidations = [
  {
    name: 'Numbered lists in MDX',
    pattern: /^\d+\\\.\s/gm,
    description: 'Escaped numbered lists (8\\.) should be unescaped (8.)',
    fix: (content) => content.replace(/(\d+)\\\./g, '$1.')
  },
  {
    name: 'Numbered lists causing parser errors',
    pattern: /^\d+\.\s/gm,
    description: 'Numbered lists at start of line might need escaping or formatting',
    fix: (content) => {
      // Check if the numbered list is causing issues by looking for problematic patterns
      const lines = content.split('\n');
      let fixed = false;
      const newLines = lines.map(line => {
        // If it's a numbered list at the start of a line and not in a code block
        if (/^\d+\.\s/.test(line)) {
          // Check if it's problematic by seeing if it's followed by content that might confuse parser
          const nextChar = line.charAt(line.indexOf('.') + 2);
          if (nextChar && /[A-Z]/.test(nextChar)) {
            fixed = true;
            return line.replace(/^(\d+)\./g, '$1\\.');
          }
        }
        return line;
      });
      return fixed ? newLines.join('\n') : content;
    }
  },
  {
    name: 'Unescaped HTML-like characters',
    pattern: /<(?!\/?\w+[^>]*>)/g,
    description: 'Unescaped < characters that might be confused for HTML tags',
    fix: (content) => content.replace(/<(?!\/?\w+[^>]*>)/g, '&lt;')
  },
  {
    name: 'JSX-like syntax errors',
    pattern: /<(\w+)[^>]*,/g,
    description: 'Commas in JSX-like tags can cause parser errors',
    fix: null // Manual fix needed
  },
  {
    name: 'Unbalanced backticks in code blocks',
    pattern: /```[^`]*$/gm,
    description: 'Code blocks that are not properly closed',
    fix: null // Manual fix needed
  },
  {
    name: 'Em dashes in content',
    pattern: /—/g,
    description: 'Em dashes might cause encoding issues',
    fix: (content) => content.replace(/—/g, '-')
  },
  {
    name: 'Temperature symbols',
    pattern: /°F|°C/g,
    description: 'Temperature symbols found - ensure they render correctly',
    fix: null // Just a warning, no fix needed
  },
  {
    name: 'Fraction symbols',
    pattern: /½|¼|¾|⅓|⅔|⅛|⅜|⅝|⅞/g,
    description: 'Unicode fraction symbols found - might need HTML entity conversion',
    fix: (content) => content
      .replace(/½/g, '1/2')
      .replace(/¼/g, '1/4') 
      .replace(/¾/g, '3/4')
      .replace(/⅓/g, '1/3')
      .replace(/⅔/g, '2/3')
      .replace(/⅛/g, '1/8')
      .replace(/⅜/g, '3/8')
      .replace(/⅝/g, '5/8')
      .replace(/⅞/g, '7/8')
  }
];

function validateMdxFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const issues = [];
    let fixedContent = content;
    let hasAutoFixes = false;

    mdxValidations.forEach(validation => {
      const matches = content.match(validation.pattern);
      if (matches) {
        const issue = {
          validation: validation.name,
          description: validation.description,
          matches: matches.length,
          canAutoFix: validation.fix !== null
        };
        
        if (validation.fix) {
          fixedContent = validation.fix(fixedContent);
          hasAutoFixes = true;
        }
        
        issues.push(issue);
      }
    });

    return {
      filePath,
      issues,
      fixedContent: hasAutoFixes ? fixedContent : null,
      hasIssues: issues.length > 0
    };
  } catch (error) {
    return {
      filePath,
      error: error.message,
      hasIssues: true
    };
  }
}

function validateAllMdxFiles(pattern = './src/content/**/*.mdx') {
  const files = glob.sync(pattern);
  const results = [];
  
  console.log(`🔍 Validating ${files.length} MDX files matching pattern: ${pattern}\n`);
  
  files.forEach(file => {
    const result = validateMdxFile(file);
    results.push(result);
    
    if (result.error) {
      console.log(`❌ ${file}: ERROR - ${result.error}`);
    } else if (result.hasIssues) {
      console.log(`⚠️  ${file}:`);
      result.issues.forEach(issue => {
        console.log(`   - ${issue.validation}: ${issue.matches} occurrence(s)`);
        console.log(`     ${issue.description}`);
        if (issue.canAutoFix) {
          console.log(`     ✅ Can auto-fix`);
        } else {
          console.log(`     🔧 Manual fix required`);
        }
      });
      console.log();
    } else {
      console.log(`✅ ${file}: No issues found`);
    }
  });
  
  // Summary
  const filesWithIssues = results.filter(r => r.hasIssues);
  const filesWithAutoFixes = results.filter(r => r.fixedContent);
  
  console.log(`\n📊 Summary:`);
  console.log(`- Total files: ${results.length}`);
  console.log(`- Files with issues: ${filesWithIssues.length}`);
  console.log(`- Files with auto-fixable issues: ${filesWithAutoFixes.length}`);
  
  return { results, filesWithAutoFixes };
}

function applyAutoFixes(results) {
  console.log(`\n🔧 Applying auto-fixes to ${results.length} files...\n`);
  
  results.forEach(result => {
    if (result.fixedContent) {
      try {
        fs.writeFileSync(result.filePath, result.fixedContent);
        console.log(`✅ Fixed: ${result.filePath}`);
      } catch (error) {
        console.log(`❌ Failed to fix ${result.filePath}: ${error.message}`);
      }
    }
  });
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const shouldFix = args.includes('--fix');
  
  // Get pattern, excluding flags
  let pattern = args.find(arg => !arg.startsWith('--')) || './src/content/**/*.mdx';
  
  const { results, filesWithAutoFixes } = validateAllMdxFiles(pattern);
  
  if (shouldFix && filesWithAutoFixes.length > 0) {
    applyAutoFixes(filesWithAutoFixes);
  } else if (filesWithAutoFixes.length > 0) {
    console.log(`\n💡 Run with --fix to automatically apply fixes to ${filesWithAutoFixes.length} files`);
  }
  
  process.exit(results.some(r => r.hasIssues) ? 1 : 0);
}

module.exports = { validateMdxFile, validateAllMdxFiles };