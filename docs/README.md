# ORXL Documentation Site

This directory contains the GitHub Pages documentation site for ORXL.

## Structure

```
docs/
├── _site/              # GitHub Pages site (deployed)
│   ├── index.html      # Landing page
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript
│   ├── guides/         # Documentation guides
│   └── api/            # API reference
├── _config.yml         # Jekyll configuration
├── *.md                # Markdown documentation files
└── README.md           # This file
```

## Local Development

### View the Site Locally

1. Install dependencies:
```bash
pip install markdown
```

2. For GitHub Pages preview:
```bash
# Install Jekyll (if not installed)
gem install bundler jekyll

# Serve locally
cd docs
jekyll serve
```

3. Open `http://localhost:4000/orxl/` in your browser

### Direct HTML Preview

You can also open `docs/_site/index.html` directly in your browser to preview the static HTML.

## Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the main branch.

URL: `https://amuzetnoM.github.io/orxl/`

## Features

### 🎨 Design
- Dark theme with orange accents matching the web UI
- Fully responsive design
- Smooth animations and transitions
- Beautiful code syntax highlighting

### 📚 Content
- **Landing Page**: Hero section with argmax equation, features, and domains
- **Universal Data Guide**: Complete guide for predicting anything
- **Data Input Handbook**: Comprehensive data format reference
- **Quick Start**: 60-second setup guide
- **API Reference**: Full API documentation

### 🔗 Navigation
- Sticky navigation bar
- Cross-linked documentation
- GitHub buttons on every page
- Search functionality (coming soon)

### ⚡ Performance
- Optimized assets
- Minimal dependencies
- Fast load times
- Accessible

## Contributing

To add new documentation:

1. Create markdown file in `docs/`
2. Add to navigation in `_site/index.html`
3. Convert to HTML or let Jekyll handle it
4. Link from relevant pages

## Theme Colors

```css
--accent-color: #ff6b35;      /* Orange accent */
--bg-primary: #0a0a0a;        /* Dark background */
--bg-secondary: #121212;       /* Secondary dark */
--text-primary: #e8e8e8;      /* Primary text */
```

## Testing

Run tests to ensure all links work:

```bash
# Test file provider (backend)
cd ..
python -m pytest tests/unit/test_file_provider.py -v

# Check documentation links
# (Add link checker script here)
```

## Maintenance

- Update version numbers in landing page
- Keep test statistics current  
- Add new prediction domains as implemented
- Update API reference when methods change

## License

MIT License - Same as ORXL project
