# PictoPy Documentation

This directory contains the documentation for PictoPy, built using MkDocs with the Material theme.

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Install documentation dependencies:**
   ```bash
   pip install -r docs/requirements.txt
   ```

2. **Build the documentation:**
   ```bash
   mkdocs build
   ```

3. **Serve the documentation locally:**
   ```bash
   mkdocs serve
   ```

4. **Access the documentation:**
   Open your browser and go to `http://127.0.0.1:8000/`

## Using Setup Scripts

### Windows (PowerShell)
```powershell
.\scripts\setup-docs.ps1
```

### Linux/macOS (Bash)
```bash
./scripts/setup-docs.sh
```

## Documentation Structure

- **API Overview**: High-level introduction to the PictoPy API
- **API Documentation**: Comprehensive endpoint documentation
- **API Quick Reference**: Fast lookup table for all endpoints
- **Interactive Swagger UI**: Guide to using the interactive documentation
- **Swagger Setup Guide**: Complete setup and usage instructions

## Configuration

The documentation is configured using `mkdocs.yml` in the root directory. Key features:

- **Material Theme**: Modern, responsive design
- **Search**: Full-text search functionality
- **Navigation**: Organized navigation structure
- **Code Highlighting**: Syntax highlighting for code blocks
- **Dark/Light Mode**: Toggle between themes

## Development

### Adding New Pages

1. Create a new Markdown file in the appropriate directory
2. Add the page to the navigation in `mkdocs.yml`
3. Build and test the documentation

### Styling

Custom CSS can be added in:
- `docs/stylesheets/extra.css`
- `docs/stylesheets/output.css`

### Building for Production

```bash
mkdocs build
```

The built documentation will be in the `site/` directory.

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port with `mkdocs serve -a localhost:8001`
2. **Missing dependencies**: Run `pip install -r docs/requirements.txt`
3. **Build errors**: Check the console output for specific error messages

### Getting Help

- Check the [MkDocs documentation](https://www.mkdocs.org/)
- Review the [Material theme documentation](https://squidfunk.github.io/mkdocs-material/)
- Open an issue in the project repository

## Contributing

When contributing to the documentation:

1. Follow the existing style and structure
2. Test your changes locally before submitting
3. Ensure all links work correctly
4. Update the navigation if adding new pages
5. Use clear, concise language

---

For more information about PictoPy, visit the [main project repository](https://github.com/AOSSIE-Org/PictoPy). 