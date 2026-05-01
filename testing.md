# Testing the API with Insomnia

Insomnia is a good fit for this backend because it supports JSON requests, bearer tokens, form data, and multipart file uploads.

## 1. Start the backend

Run the API locally:

```powershell
uvicorn app.main:app --reload
```

The default local base URL is:

```text
http://127.0.0.1:8000
```

## 2. Create an environment

In Insomnia, create variables like:

```json
{
  "base_url": "http://127.0.0.1:8000",
  "token": ""
}
```

## 3. Test authentication

### Register

`POST {{ base_url }}/auth/register`

Body type: JSON

```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "strongpass123"
}
```

### Login

`POST {{ base_url }}/auth/login`

Body type: `Form URL Encoded`

- `username`
- `password`

Save the returned `access_token` into the `token` variable.

### Verify current user

`GET {{ base_url }}/auth/me`

Header:

```text
Authorization: Bearer {{ token }}
```

## 4. Test folders

### List folders

`GET {{ base_url }}/folders`

### Create folder

`POST {{ base_url }}/folders`

Body type: JSON

```json
{
  "name": "Documents",
  "parent_folder_id": null
}
```

### Rename folder

`PATCH {{ base_url }}/folders/{folder_id}`

Body type: JSON

```json
{
  "new_name": "Docs"
}
```

### Move folder

`PATCH {{ base_url }}/folders/{folder_id}/move`

Body type: JSON

```json
{
  "parent_folder_id": null
}
```

### View folder contents

`GET {{ base_url }}/folders/{folder_id}/contents`

## 5. Test files

### List files

`GET {{ base_url }}/files`

### Upload file

`POST {{ base_url }}/files`

Body type: `Multipart Form`

- `file` as type `File`
- optional `folder_id` as text

Example with a folder:

- `file`: `sample.txt`
- `folder_id`: `18`

### Rename file

`PATCH {{ base_url }}/files/{file_id}`

Body type: JSON

```json
{
  "new_name": "report-final.txt"
}
```

### Move file

`PATCH {{ base_url }}/files/{file_id}/move`

Body type: JSON

```json
{
  "folder_id": 18
}
```

### Download file

`GET {{ base_url }}/files/{file_id}/download`

You should get:
- `200 OK`
- file content in the response body
- a `Content-Disposition` header with the original filename

### Delete file

`DELETE {{ base_url }}/files/{file_id}`

### Restore file

`POST {{ base_url }}/files/{file_id}/restore`

Body type: JSON

```json
{
  "folder_id": null
}
```

## 6. Test trash

### Deleted files

`GET {{ base_url }}/trash/files`

### Deleted folders

`GET {{ base_url }}/trash/folders`

## 7. Expected auth behavior

Protected routes should return `401` without a bearer token.

Useful header:

```text
Authorization: Bearer {{ token }}
```

## 8. What to verify

When a request succeeds, check:

- the HTTP status code
- the returned JSON
- the response headers for downloads
- that uploaded files exist in storage
- that folder/file lists update after move, delete, or restore operations

## 9. Recommended manual test order

1. Register a new user.
2. Log in and save the token.
3. Call `/auth/me`.
4. Create a folder.
5. Upload a file to root.
6. Upload a file to the folder.
7. View folder contents.
8. Rename and move file/folder.
9. Download the file.
10. Delete and restore the file.
11. Delete the folder and confirm trash entries.