-- Active: 1775685284534@@127.0.0.1@5432@cloud_storage
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, 
    storage_quota_bytes BIGINT NOT NULL DEFAULT 1073741824,
    used_storage_bytes BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE folders (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    parent_folder_id BIGINT NULL,
    name VARCHAR(255) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_folders_owner
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,

    CONSTRAINT fk_folders_parent
        FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    folder_id BIGINT NULL,
    original_name VARCHAR(255) NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    mime_type VARCHAR(100),
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    checksum CHAR(64),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_files_owner
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,

    CONSTRAINT fk_files_folder
        FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
);

CREATE INDEX idx_folders_owner_parent
ON folders(owner_id, parent_folder_id);

CREATE INDEX idx_files_owner_folder
ON files(owner_id, folder_id);

CREATE INDEX idx_files_owner_created_at
ON files(owner_id, created_at DESC);

CREATE UNIQUE INDEX uq_active_folder_name_per_location
ON folders(owner_id, COALESCE(parent_folder_id, -1), name)
WHERE is_deleted = FALSE;

CREATE UNIQUE INDEX uq_active_file_name_per_location
ON files(owner_id, COALESCE(folder_id, -1), original_name)
WHERE is_deleted = FALSE;






