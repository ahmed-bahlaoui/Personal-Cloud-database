-- Active: 1775685284534@@127.0.0.1@5432@cloud_storage
-- =========================================
-- queries.sql
-- Personal Cloud Storage - Common Operations
-- =========================================

-- =========================================================
-- 1. FILES - FINDING / LISTING
-- =========================================================

-- Find all active files of a user

SELECT * FROM files
WHERE owner_id = 2
AND is_deleted = FALSE
LIMIT 5;


-- Find all active files of a user (clean display)
SELECT
    id,
    original_name,
    mime_type,
    size_bytes,
    created_at
FROM files
WHERE
    owner_id = 1
    AND is_deleted = FALSE
ORDER BY created_at DESC;

-- Find all files in a specific folder
SELECT *
FROM files
WHERE
    owner_id = 1
    AND folder_id = 3
    AND is_deleted = FALSE;

-- Find all root-level files of a user
SELECT *
FROM files
WHERE
    owner_id = 1
    AND folder_id IS NULL
    AND is_deleted = FALSE;

-- Find deleted files (trash) of a user
SELECT *
FROM files
WHERE
    owner_id = 1
    AND is_deleted = TRUE
ORDER BY deleted_at DESC;

-- Find files sorted by newest first
SELECT id, original_name, created_at
FROM files
WHERE
    owner_id = 1
    AND is_deleted = FALSE
ORDER BY created_at DESC;

-- Find largest files of a user
SELECT original_name, size_bytes
FROM files
WHERE
    owner_id = 1
    AND is_deleted = FALSE
ORDER BY size_bytes DESC
LIMIT 5;

-- =========================================================
-- 2. STORAGE / AGGREGATIONS
-- =========================================================

-- Calculate total active storage used by a user
SELECT COALESCE(SUM(size_bytes), 0) AS total_storage
FROM files
WHERE
    owner_id = 1
    AND is_deleted = FALSE;

-- Show storage quota and used storage for one user
SELECT u.username, u.storage_quota_bytes, COALESCE(SUM(f.size_bytes), 0) AS used_storage
FROM users u
    LEFT JOIN files f ON u.id = f.owner_id
    AND f.is_deleted = FALSE
WHERE
    u.id = 1
GROUP BY
    u.id,
    u.username,
    u.storage_quota_bytes;

-- Recalculate storage used for one user
UPDATE users u
SET
    used_storage_bytes = (
        SELECT COALESCE(SUM(size_bytes), 0)
        FROM files f
        WHERE
            f.owner_id = u.id
            AND f.is_deleted = FALSE
    )
WHERE
    u.id = 1;

-- Recalculate storage used for all users
UPDATE users u
SET
    used_storage_bytes = (
        SELECT COALESCE(SUM(f.size_bytes), 0)
        FROM files f
        WHERE
            f.owner_id = u.id
            AND f.is_deleted = FALSE
    );

-- =========================================================
-- 3. FOLDERS - FINDING / LISTING
-- =========================================================

-- Find all active folders of a user
SELECT * FROM folders WHERE owner_id = 1 AND is_deleted = FALSE;

-- Find all root folders of a user
SELECT *
FROM folders
WHERE
    owner_id = 1
    AND parent_folder_id IS NULL
    AND is_deleted = FALSE;

-- Find all subfolders of a folder
SELECT *
FROM folders
WHERE
    parent_folder_id = 1
    AND is_deleted = FALSE;

-- Show folder names with parent folder names
SELECT child.id, child.name, parent.name AS parent_name, child.owner_id
FROM folders child
    LEFT JOIN folders parent ON child.parent_folder_id = parent.id
WHERE
    child.owner_id = 1
    AND child.is_deleted = FALSE
ORDER BY child.id;

-- =========================================================
-- 4. COUNTS / STATS
-- =========================================================

-- Count active files owned by a user
SELECT COUNT(*) AS file_count
FROM files
WHERE
    owner_id = 1
    AND is_deleted = FALSE;

-- Count active folders owned by a user
SELECT COUNT(*) AS folder_count
FROM folders
WHERE
    owner_id = 1
    AND is_deleted = FALSE;

-- Count active files per user
SELECT u.username, COUNT(f.id) AS file_count
FROM users u
    LEFT JOIN files f ON u.id = f.owner_id
    AND f.is_deleted = FALSE
GROUP BY
    u.id,
    u.username
ORDER BY file_count DESC;

-- Calculate total storage used by each user
SELECT u.username, COALESCE(SUM(f.size_bytes), 0) AS total_used_bytes
FROM users u
    LEFT JOIN files f ON u.id = f.owner_id
    AND f.is_deleted = FALSE
GROUP BY
    u.id,
    u.username
ORDER BY total_used_bytes DESC;

-- =========================================================
-- 5. SEARCH / FILTERING
-- =========================================================

-- Search files by name
SELECT *
FROM files
WHERE
    owner_id = 1
    AND original_name ILIKE '%report%'
    AND is_deleted = FALSE;

-- Filter files by exact MIME type
SELECT *
FROM files
WHERE
    owner_id = 1
    AND mime_type = 'application/pdf'
    AND is_deleted = FALSE;

-- Find all image files of a user
SELECT *
FROM files
WHERE
    owner_id = 1
    AND mime_type LIKE 'image/%'
    AND is_deleted = FALSE;

-- Find all PDF files in the whole system
SELECT
    id,
    owner_id,
    original_name,
    size_bytes
FROM files
WHERE
    mime_type = 'application/pdf'
    AND is_deleted = FALSE
ORDER BY size_bytes DESC;

-- =========================================================
-- 6. JOINS
-- =========================================================

-- Show files with their folder names
SELECT f.id, f.original_name, f.size_bytes, fo.name AS folder_name
FROM files f
    LEFT JOIN folders fo ON f.folder_id = fo.id
WHERE
    f.owner_id = 1
    AND f.is_deleted = FALSE;

-- Show files with user information
SELECT u.username, f.original_name, f.size_bytes
FROM files f
    JOIN users u ON f.owner_id = u.id
WHERE
    f.is_deleted = FALSE;

-- Show files and folders together for one folder view
SELECT id, name, 'folder' AS type, created_at
FROM folders
WHERE
    owner_id = 1
    AND parent_folder_id = 1
    AND is_deleted = FALSE
UNION ALL
SELECT
    id,
    original_name AS name,
    'file' AS type,
    created_at
FROM files
WHERE
    owner_id = 1
    AND folder_id = 1
    AND is_deleted = FALSE;

-- =========================================================
-- 7. UPDATE OPERATIONS
-- =========================================================

-- Rename a file
UPDATE files
SET
    original_name = 'new_name.pdf',
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = 3
    AND owner_id = 1;

-- Move a file to another folder
UPDATE files
SET
    folder_id = 4,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = 3
    AND owner_id = 1;

-- Move a file to root level
UPDATE files
SET
    folder_id = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = 3
    AND owner_id = 1;

-- =========================================================
-- 8. SOFT DELETE / RESTORE / DELETE
-- =========================================================

-- Soft delete a file (move to trash)
UPDATE files
SET
    is_deleted = TRUE,
    deleted_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = 3
    AND owner_id = 1;

-- Restore a file from trash
UPDATE files
SET
    is_deleted = FALSE,
    deleted_at = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = 3
    AND owner_id = 1;

-- Permanently delete a file
DELETE FROM files WHERE id = 3 AND owner_id = 1;

-- =========================================================
-- 9. VERIFICATION QUERIES
-- =========================================================

-- Verify one specific file
SELECT
    id,
    original_name,
    folder_id,
    is_deleted,
    deleted_at,
    updated_at
FROM files
WHERE
    id = 3;

-- Show all users
SELECT * FROM users;

-- Show all folders
SELECT * FROM folders;

-- Show all files
SELECT * FROM files;

-- =========================================================
-- 10. ADVANCED / EXTRA
-- =========================================================

-- Find duplicate files by checksum
SELECT checksum, COUNT(*) AS duplicate_count
FROM files
WHERE
    checksum IS NOT NULL
GROUP BY
    checksum
HAVING
    COUNT(*) > 1;

-- Show active files with folder names, newest first
SELECT f.id, f.original_name, f.mime_type, f.size_bytes, fo.name AS folder_name, f.created_at
FROM files f
    LEFT JOIN folders fo ON f.folder_id = fo.id
WHERE
    f.owner_id = 1
    AND f.is_deleted = FALSE
ORDER BY f.created_at DESC;

-- Show all files currently in trash
SELECT
    id,
    owner_id,
    original_name,
    deleted_at
FROM files
WHERE
    is_deleted = TRUE
ORDER BY deleted_at DESC;

-- Reset sequences after manual inserts in seed.sql
SELECT setval( 'users_id_seq', ( SELECT MAX(id) FROM users ) );

SELECT setval( 'folders_id_seq', ( SELECT MAX(id) FROM folders ) );

SELECT setval( 'files_id_seq', ( SELECT MAX(id) FROM files ) );