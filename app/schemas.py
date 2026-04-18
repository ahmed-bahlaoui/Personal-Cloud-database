from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: int | None = None


class FolderRename(BaseModel):
    new_name: str


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    parent_folder_id: int | None
    name: str
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FileRename(BaseModel):
    new_name: str


class FileRestore(BaseModel):
    folder_id: int | None = None


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    folder_id: int | None
    original_name: str
    storage_key: str
    mime_type: str | None
    size_bytes: int
    checksum: str | None
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    storage_quota_bytes: int
    used_storage_bytes: int
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
