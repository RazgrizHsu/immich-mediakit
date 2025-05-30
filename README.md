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


## preivew

<p align="center">
<img src="docs/intro.jpg" alt="preview" />
</p>

<p align="center">
<img src="docs/intro-view.jpg" alt="preview" />
</p>

## Implementation Status

- [x] Fetch Immich assets
- [x] Generate vectors
- [x] Store vectors for comparison
- [x] Display library with filtering
- [x] Find similar
  - [x] Threshold settings
  - [x] Single-Group duplicate comparison similar
  - [x] Provide Deletion
- [ ] Batch processing

## How It Works

1. Fetches Users & Assets data from the Immich PostgreSQL database
2. Processes images through ResNet152 to extract feature vectors
3. Stores vectors in the Qdrant vector database
4. Uses vector similarity to identify similar/duplicate photos
5. Displays similar photo groups based on the configured threshold
6. Manages asset deletion by updating Immich database directly:
   - Follows Immich's deletion logic for compatibility
   - **Important**: Enable trash feature in Immich settings first
   - Deleted assets appear in Immich's trash where you can permanently delete or restore them


## Installation & Setup

### Prerequisites

- Access to an Immich installation with trash feature enabled
- A configured `.env` file (see above)
-


### Connecting to Immich Database

If your Immich is running with Docker Compose, you need to expose the PostgreSQL port. Add the following port mapping to your Immich's docker-compose.yml:

```yaml
services:
  database:
    container_name: immich_postgres
    image: ghcr.io/immich-app/postgres:14-vectorchord0.3.0-pgvectors0.2.0
    ports:
      - "5432:5432"  # Add this line to expose PostgreSQL
```

After updating, restart Immich to apply the changes. The exposed port (5432) should match the `PSQL_PORT` setting in your MediaKit `.env` file.


### Environment Variables

Create a `.env` file with the following variables:

```
# PostgreSQL connection to Immich
PSQL_HOST=localhost
PSQL_PORT=5432
PSQL_DB=immich
PSQL_USER=postgres
PSQL_PASS=postgres

# Immich connection
IMMICH_PATH=/path/to/immich/library

# Qdrant connection (not needed for Docker Compose)
QDRANT_URL=http://localhost:6333
QDRANT_PORT=6333

# MediaKit settings
MKIT_PORT=8086
MIKT_PORTWS=8087       # for background tasks (optional, default: 8087)
MKIT_WS_HOST=localhost  # for non-Docker setups (optional)
MKIT_DATA=/path/to/data/dir
```



### Option 1: Docker Compose (Recommended)

The easiest way to run Immich-MediaKit is with Docker Compose, which automatically includes the Qdrant vector database:

1. Ensure you have created the `.env` file
2. Run:

```bash
# Build and start containers
docker-compose up -d --build
```

### Option 2: Direct Installation

If you prefer to run without Docker:

1. Install Qdrant server separately
2. Ensure you have created the `.env` file
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python src/app.py
   ```


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

Happy organizing! We hope this tool enhances your Immich experience by helping you maintain a clean, duplicate-free library.
