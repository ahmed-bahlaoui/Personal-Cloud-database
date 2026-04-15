# Cloud Database Documentation

## Overview

This project exposes a small FastAPI API for a cloud storage system backed by PostgreSQL and SQLAlchemy.

The application currently supports:

- listing a user's active files
- listing a user's active folders
- creating folders
- renaming files
- soft-deleting files

## Project Structure

- `app/main.py`: FastAPI routes and HTTP-level validation
- `app/models.py`: SQLAlchemy ORM models
- `app/queries.py`: reusable read queries
- `app/schemas.py`: Pydantic request and response schemas
- `app/db.py`: database engine, base class, and session factory
- `db/schema.sql`: SQL schema
- `db/queries.sql`: SQL query examples or reference queries

## Schema Layer

Pydantic schemas now define all request and response payloads used by the API.

Request schemas:

- `FolderCreate`
- `FileRename`

Response schemas:

- `MessageResponse`
- `FolderRead`
- `FileRead`

`FolderRead` and `FileRead` use `from_attributes=True`, which allows FastAPI to serialize SQLAlchemy ORM objects directly into API responses.

## API Endpoints

### `GET /`

Health-style root endpoint.

Response:

```json
{
  "message": "Cloud Storage API is running"
}
```

### `GET /files?user_id=<id>`

Returns all non-deleted files for an existing user.

Validation:

- returns `404` if the user does not exist

Response model:

- `list[FileRead]`

### `GET /folders?user_id=<id>`

Returns all non-deleted folders for an existing user.

Validation:

- returns `404` if the user does not exist

Response model:

- `list[FolderRead]`

### `POST /folders`

Creates a new folder.

Request body:

```json
{
  "name": "Documents",
  "parent_folder_id": null,
  "owner_id": 1
}
```

Validation:

- returns `400` if the folder name is empty after trimming
- returns `404` if the owner does not exist
- returns `404` if `parent_folder_id` is provided but does not exist
- returns `400` if the parent folder belongs to a different owner
- returns `409` if a non-deleted folder with the same name already exists in the same location
- returns `409` if the database rejects the insert

Response model:

- `FolderRead`

Status code:

- `201 Created`

### `PATCH /files/{file_id}`

Renames an existing file.

Request body:

```json
{
  "new_name": "report.pdf"
}
```

Validation:

- returns `404` if the file does not exist
- returns `400` if the file is already deleted
- returns `400` if the new name is empty after trimming
- returns `409` if a non-deleted file with the same name already exists in the same location
- returns `409` if the database rejects the update

Response model:

- `FileRead`

### `DELETE /files/{file_id}`

Soft-deletes a file by setting `is_deleted = true` and populating `deleted_at`.

Validation:

- returns `404` if the file does not exist
- returns `400` if the file is already deleted
- returns `409` if the database rejects the update

Response:

```json
{
  "message": "File deleted"
}
```

Response model:

- `MessageResponse`

## Notes On Current Behavior

- Folder creation prevents duplicate active folder names in the same parent folder for the same owner.
- File rename prevents duplicate active file names in the same folder for the same owner.
- File deletion is soft delete only; rows remain in the database.
- Read queries in `app/queries.py` currently focus on reusable fetch logic for files and folders.

## Known Next Improvements

- move more business logic from `app/main.py` into a service layer
- add response schemas for users if user endpoints are introduced
- enforce duplicate-name rules with database constraints or indexes in addition to application checks
- add automated tests for validation and conflict cases
- standardize error payloads across all endpoints
