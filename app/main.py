import datetime

from app.db import SessionLocal
from app.models import File, Folder, User
from app.queries import get_user_files_by_id, get_user_folders_by_id
from app.schemas import (
    FileRead,
    FileRename,
    FolderCreate,
    FolderRead,
    MessageResponse,
)
from fastapi import FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


app = FastAPI()


# ROOT
@app.get("/", response_model=MessageResponse)
def root():
    return {"message": "Cloud Storage API is running"}

# GET /files


@app.get("/files", response_model=list[FileRead])
def get_files(user_id: int = 1):
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return get_user_files_by_id(user_id)

# GET folders


@app.get("/folders", response_model=list[FolderRead])
def get_folders(user_id: int = 1):
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return get_user_folders_by_id(user_id)


# POST folders
@app.post("/folders", response_model=FolderRead, status_code=201)
def create_folder(data: FolderCreate):
    with SessionLocal() as session:
        folder_name = data.name.strip()
        if not folder_name:
            raise HTTPException(status_code=400, detail="Folder name cannot be empty")

        owner = session.get(User, data.owner_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        if data.parent_folder_id is not None:
            parent_folder = session.get(Folder, data.parent_folder_id)
            if not parent_folder:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            if parent_folder.owner_id != data.owner_id:
                raise HTTPException(
                    status_code=400,
                    detail="Parent folder does not belong to this owner",
                )

        existing_folder_query = select(Folder).where(
            Folder.owner_id == data.owner_id,
            Folder.name == folder_name,
            ~Folder.is_deleted,
        )

        if data.parent_folder_id is None:
            existing_folder_query = existing_folder_query.where(
                Folder.parent_folder_id.is_(None)
            )
        else:
            existing_folder_query = existing_folder_query.where(
                Folder.parent_folder_id == data.parent_folder_id
            )

        existing_folder = session.execute(existing_folder_query).scalar_one_or_none()
        if existing_folder:
            raise HTTPException(
                status_code=409,
                detail="A folder with the same name already exists in this location",
            )

        folder = Folder(
            name=folder_name,
            parent_folder_id=data.parent_folder_id,
            owner_id=data.owner_id
        )

        try:
            session.add(folder)
            session.commit()
            session.refresh(folder)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=(
                    "Folder could not be created because the database generated "
                    "a conflicting id or rejected the insert"
                ),
            )

        return folder


@app.patch("/files/{file_id}", response_model=FileRead)
def rename_file(file_id: int, data: FileRename):
    with SessionLocal() as session:
        file = session.get(File, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.is_deleted:
            raise HTTPException(status_code=400, detail="Cannot rename a deleted file")

        new_name = data.new_name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="File name cannot be empty")

        duplicate_file_query = select(File).where(
            File.id != file_id,
            File.owner_id == file.owner_id,
            File.original_name == new_name,
            ~File.is_deleted,
        )

        if file.folder_id is None:
            duplicate_file_query = duplicate_file_query.where(File.folder_id.is_(None))
        else:
            duplicate_file_query = duplicate_file_query.where(
                File.folder_id == file.folder_id
            )

        duplicate_file = session.execute(duplicate_file_query).scalar_one_or_none()
        if duplicate_file:
            raise HTTPException(
                status_code=409,
                detail="A file with the same name already exists in this location",
            )

        file.original_name = new_name

        try:
            session.commit()
            session.refresh(file)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="File could not be renamed because the database rejected the update",
            )

        return file


@app.delete("/files/{file_id}", response_model=MessageResponse)
def delete_file(file_id: int):
    with SessionLocal() as session:
        file = session.get(File, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.is_deleted:
            raise HTTPException(status_code=400, detail="File is already deleted")

        file.is_deleted = True
        file.deleted_at = datetime.datetime.now(datetime.timezone.utc)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="File could not be deleted because the database rejected the update",
            )

        return {"message": "File deleted"}
