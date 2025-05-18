<p align="center"></p>

<p align="center"><img src="src/assets/logo.png" width="256" height="256" alt="logo" /></p>
<p align="center">
<small> 
An extension toolkit for <a href="https://github.com/immich-app/immich">Immich</a>
enabling advanced management capabilities through AI-powered similarity detection
</small>
</p>
<p align="center">
<a href="https://buymeacoffee.com/razgrizhsu" target="_blank"><img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow.svg?style=flat-square&logo=buy-me-a-coffee" alt="Buy Me A Coffee"/></a>
</p>

## Key Features

- **Asset Management**: Import and manage photo assets from Immich
- **AI-Powered Vector**: Convert photos to feature vectors using ResNet152 for advanced similarity detection
- **Duplicate Detection**: Find and manage duplicate photos based on visual similarity
- **Filtering and Batch**: Browse photo library with filtering options and perform batch operations
- **Web-Based UI**: User-friendly dashboard for all operations

## Implementation Status

- [x] Fetch Immich assets
- [x] Process photos to generate feature vectors using ResNet152
- [x] Store vectors in Qdrant for similarity comparison
- [ ] Display photo library with filtering and deletion features
- [ ] Find duplicate/similar photos with adjustable threshold
    - [ ] Provide configurable threshold settings for similarity search
    - [ ] Implement single-group duplicate comparison similar to Immich
- [ ] Set up batch processing rules for duplicate management
    - [ ] Backup about-to-be-deleted images
    - [ ] Organize backups by groups in local folders

## How It Works

1. Fetches Users & Assets data from the Immich PostgreSQL database
2. Processes images through ResNet152 to extract feature vectors
3. Stores vectors in the Qdrant vector database
4. Uses vector similarity to identify similar/duplicate photos
5. Displays similar photo groups based on the configured threshold

## Installation & Setup

### Prerequisites

- Access to an Immich installation
- API keys for Immich users whose assets you want to manage

### Option 1: Docker Compose (Recommended)

The easiest way to run Immich-MediaKit is with Docker Compose, which automatically includes the Qdrant vector database:

1. Create a `.env` file (see Environment Variables section below)
2. Run:

```bash
# Build and start containers
docker-compose up -d --build
```

### Option 2: Direct Installation

If you prefer to run without Docker:

1. Install Qdrant server separately
2. Create a `.env` file
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python src/app.py
   ```

## Environment Variables

Create a `.env` file with the following variables:

```
# Qdrant connection (not needed for Docker Compose)
QDRANT_URL=http://localhost:6333

# PostgreSQL connection to Immich
PSQL_HOST=localhost
PSQL_PORT=5432
PSQL_DB=immich
PSQL_USER=postgres
PSQL_PASS=postgres

# Immich connection
IMMICH_URL=http://localhost:2283
IMMICH_PATH=/path/to/immich/library  # Optional, for faster local access

# MediaKit settings
MKIT_PORT=8086
MKIT_DATA=/path/to/data/dir
```

## Performance Optimization

Setting the `IMMICH_PATH` environment variable to point to your Immich installation's physical path significantly improves performance. This allows Immich-MediaKit to access images directly from the filesystem rather than downloading them via HTTP API requests.

## Access Control

To manage user assets in Immich, you must create API keys for those users in the Immich system. Assets belonging to users without API keys cannot be accessed. Ensure the API keys have appropriate permissions (read or delete) based on the operations you want to perform.

## Vector Database: Qdrant vs FAISS

This project uses Qdrant as the vector database instead of FAISS due to:

- Better support for custom IDs with direct vector access
- More efficient memory usage (approximately 50% less memory for large collections)
- Native support for vector comparison operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

If you find this project helpful, consider buying me a coffee:

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/razgrizhsu)

## License

This project is licensed under the [GNU General Public License v3.0 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html).

Commercial use is permitted, but any derivative works must also be open-sourced under the same license. If you modify and distribute this software, you must make your source code publicly available.

## Disclaimer

This tool interacts with your Immich photo library and database.
While designed to be safe, it is still under active development and may contain unexpected behaviors.
Please consider the following:

- Always backup your Immich database before performing operations that modify data
- Use the similarity threshold carefully when identifying duplicates to avoid false positives
- The developers are not responsible for any data loss that may occur from using this tool
- Vector similarity is based on AI models and may not perfectly match human perception of similarity

Immich-MediaKit is provided "as is" without warranty of any kind. By using this software, you acknowledge the potential risks involved in managing and potentially modifying your photo collection.

Happy photo organizing! We hope this tool enhances your Immich experience by helping you maintain a clean, duplicate-free photo library.
