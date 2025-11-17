# Project Title

## Overview

This FastAPI project provides a simple tree data structure API to manage hierarchical data. You can create, read, update, and delete tree items with nested relationships. The backend leverages a database to store tree nodes and supports both SQLite and PostgreSQL.

## Features

- **Tree Structure**: Supports nested tree items with flexible relationships.
- **CRUD Operations**: Allows for creating, reading, updating, and deleting tree items.
- **CORS**: Configured for cross-origin resource sharing.
- **Environment Configuration**: Uses environment variables for database connection details.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables:

   ```bash
   export DATABASE_URL="your_database_url"
   export ENVIRONMENT="development"  # or "production"
   export ALLOWED_ORIGINS="*"
   ```

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Get the Tree

- **Endpoint**: `GET /api/tree`
- **Description**: Retrieves only root nodes and their nested children.

### Get All Items

- **Endpoint**: `GET /api/tree/all`
- **Description**: Retrieves all tree items as a flat list.

### Create a Tree Item

- **Endpoint**: `POST /api/tree`
- **Description**: Replaces the entire tree with new data.

### Update Tree Item Data

- **Endpoint**: `PUT /api/tree/{item_id}/data`
- **Description**: Updates the data field of a specific tree item.

### Delete a Tree Item

- **Endpoint**: `DELETE /api/tree/{item_id}`
- **Description**: Deletes a tree item and all its children.

## Example Data

You can use the following JSON example to create a tree structure:

```json
[
  {
    "name": "root",
    "children": [
      {
        "name": "child1",
        "children": [
          {
            "name": "child1-child1",
            "data": "c1-c1 Hello"
          },
          {
            "name": "child1-child2",
            "data": "c1-c2 JS"
          }
        ]
      },
      {
        "name": "child2",
        "data": "c2 World"
      }
    ]
  }
]
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
