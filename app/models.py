from datetime import UTC, datetime
from typing import List, Optional

from app.db import Base
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    storage_quota_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1073741824
    )
    used_storage_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )

    folders: Mapped[List["Folder"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    files: Mapped[List["File"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (
        Index(
            "uq_active_folder_name_per_location",
            "owner_id",
            text("COALESCE(parent_folder_id, -1)"),
            "name",
            unique=True,
            postgresql_where=text("is_deleted = FALSE"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_folder_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )

    owner: Mapped["User"] = relationship(back_populates="folders")

    parent_folder: Mapped[Optional["Folder"]] = relationship(
        "Folder", remote_side=[id], back_populates="child_folders"
    )

    child_folders: Mapped[List["Folder"]] = relationship(
        "Folder", back_populates="parent_folder", cascade="all, delete-orphan"
    )

    files: Mapped[List["File"]] = relationship(back_populates="folder")

    def __repr__(self) -> str:
        return f"Folder(id={self.id}, name='{self.name}', owner_id={self.owner_id})"


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        Index(
            "uq_active_file_name_per_location",
            "owner_id",
            text("COALESCE(folder_id, -1)"),
            "original_name",
            unique=True,
            postgresql_where=text("is_deleted = FALSE"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    folder_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=utcnow
    )

    owner: Mapped["User"] = relationship(back_populates="files")
    folder: Mapped[Optional["Folder"]] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"File(id={self.id}, original_name='{self.original_name}', owner_id={self.owner_id})"
