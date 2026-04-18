import datetime
from pathlib import Path

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import SessionLocal
from app.models import File, Folder, User
from app.queries import get_user_files_by_id, get_user_folders_by_id
from app.schemas import (
    FileRead,
    FileRename,
    FileRestore,
    FolderCreate,
    FolderRead,
    FolderRename,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.settings import ALLOWED_ORIGINS, STORAGE_ROOT
from app.storage import save_uploaded_file
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ROOT


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def recalculate_used_storage(session, user_id: int) -> None:
    total_storage = session.execute(
        select(func.coalesce(func.sum(File.size_bytes), 0)).where(
            File.owner_id == user_id,
            ~File.is_deleted,
        )
    ).scalar_one()
    user = session.get(User, user_id)
    if user:
        user.used_storage_bytes = int(total_storage)
        user.updated_at = utcnow()


def get_accessible_active_folder(session, folder_id: int, user_id: int) -> Folder:
    folder = session.get(Folder, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this folder")
    if folder.is_deleted:
        raise HTTPException(status_code=400, detail="Folder is deleted")
    return folder


def has_active_folder_name_conflict(
    session, user_id: int, parent_folder_id: int | None, name: str, exclude_folder_id: int | None = None
) -> bool:
    query = select(Folder).where(
        Folder.owner_id == user_id,
        Folder.name == name,
        ~Folder.is_deleted,
    )
    if exclude_folder_id is not None:
        query = query.where(Folder.id != exclude_folder_id)
    if parent_folder_id is None:
        query = query.where(Folder.parent_folder_id.is_(None))
    else:
        query = query.where(Folder.parent_folder_id == parent_folder_id)
    return session.execute(query).scalar_one_or_none() is not None


def has_active_file_name_conflict(
    session, user_id: int, folder_id: int | None, name: str, exclude_file_id: int | None = None
) -> bool:
    query = select(File).where(
        File.owner_id == user_id,
        File.original_name == name,
        ~File.is_deleted,
    )
    if exclude_file_id is not None:
        query = query.where(File.id != exclude_file_id)
    if folder_id is None:
        query = query.where(File.folder_id.is_(None))
    else:
        query = query.where(File.folder_id == folder_id)
    return session.execute(query).scalar_one_or_none() is not None


def soft_delete_folder_tree(session, root_folder: Folder) -> None:
    deleted_at = utcnow()
    folder_ids: list[int] = []
    stack = [root_folder]

    while stack:
        current_folder = stack.pop()
        folder_ids.append(current_folder.id)
        child_folders = session.execute(
            select(Folder).where(Folder.parent_folder_id == current_folder.id)
        ).scalars().all()
        stack.extend(child_folders)

    active_folders = session.execute(
        select(Folder).where(Folder.id.in_(folder_ids), ~Folder.is_deleted)
    ).scalars().all()
    for folder in active_folders:
        folder.is_deleted = True
        folder.deleted_at = deleted_at
        folder.updated_at = deleted_at

    active_files = session.execute(
        select(File).where(File.folder_id.in_(folder_ids), ~File.is_deleted)
    ).scalars().all()
    for file in active_files:
        file.is_deleted = True
        file.deleted_at = deleted_at
        file.updated_at = deleted_at


@app.get("/", response_model=MessageResponse)
def root():
    return {"message": "Cloud Storage API is running"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register_user(data: UserCreate):
    with SessionLocal() as session:
        username = data.username.strip()
        email = data.email.strip().lower()

        if not username:
            raise HTTPException(
                status_code=400, detail="Username cannot be empty")
        if not email:
            raise HTTPException(
                status_code=400, detail="Email cannot be empty")
        if len(data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long",
            )

        existing_user = session.execute(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        ).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="A user with this username or email already exists",
            )

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(data.password),
        )

        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="User could not be created because the database rejected the insert",
            )

        return user


@app.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.username == form_data.username)
        ).scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@app.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# GET /files


@app.get("/files", response_model=list[FileRead])
def get_files(current_user: User = Depends(get_current_user)):
    return get_user_files_by_id(current_user.id)

# GET folders


@app.get("/folders", response_model=list[FolderRead])
def get_folders(current_user: User = Depends(get_current_user)):
    return get_user_folders_by_id(current_user.id)


@app.get("/trash/files", response_model=list[FileRead])
def get_deleted_files(current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        return session.execute(
            select(File).where(
                File.owner_id == current_user.id,
                File.is_deleted,
            ).order_by(File.deleted_at.desc())
        ).scalars().all()


@app.get("/trash/folders", response_model=list[FolderRead])
def get_deleted_folders(current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        return session.execute(
            select(Folder).where(
                Folder.owner_id == current_user.id,
                Folder.is_deleted,
            ).order_by(Folder.deleted_at.desc())
        ).scalars().all()


@app.post("/files", response_model=FileRead, status_code=201)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: int | None = Form(default=None),
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as session:
        user = session.get(User, current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        target_folder = None
        if folder_id is not None:
            target_folder = get_accessible_active_folder(session, folder_id, current_user.id)

        original_name = Path(file.filename or "").name.strip()
        if not original_name:
            raise HTTPException(status_code=400, detail="File name cannot be empty")

        if has_active_file_name_conflict(session, current_user.id, folder_id, original_name):
            raise HTTPException(
                status_code=409,
                detail="A file with the same name already exists in this location",
            )

        content = file.file.read()
        size_bytes = len(content)
        if user.used_storage_bytes + size_bytes > user.storage_quota_bytes:
            raise HTTPException(
                status_code=413,
                detail="File upload exceeds the user's storage quota",
            )

        storage_key, checksum = save_uploaded_file(original_name, content)
        file_record = File(
            owner_id=current_user.id,
            folder_id=target_folder.id if target_folder else None,
            original_name=original_name,
            storage_key=storage_key,
            mime_type=file.content_type,
            size_bytes=size_bytes,
            checksum=checksum,
        )

        try:
            session.add(file_record)
            recalculate_used_storage(session, current_user.id)
            session.commit()
            session.refresh(file_record)
        except IntegrityError:
            session.rollback()
            storage_path = STORAGE_ROOT / storage_key
            if storage_path.exists():
                storage_path.unlink()
            raise HTTPException(
                status_code=409,
                detail="File could not be uploaded because the database rejected the insert",
            )

        return file_record


# POST folders
@app.post("/folders", response_model=FolderRead, status_code=201)
def create_folder(data: FolderCreate, current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        folder_name = data.name.strip()
        if not folder_name:
            raise HTTPException(
                status_code=400, detail="Folder name cannot be empty")

        if data.parent_folder_id is not None:
            parent_folder = session.get(Folder, data.parent_folder_id)
            if not parent_folder:
                raise HTTPException(
                    status_code=404, detail="Parent folder not found")
            if parent_folder.owner_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this parent folder",
                )
            if parent_folder.is_deleted:
                raise HTTPException(status_code=400, detail="Parent folder is deleted")

        if has_active_folder_name_conflict(
            session, current_user.id, data.parent_folder_id, folder_name
        ):
            raise HTTPException(
                status_code=409,
                detail="A folder with the same name already exists in this location",
            )

        folder = Folder(
            name=folder_name,
            parent_folder_id=data.parent_folder_id,
            owner_id=current_user.id
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


@app.patch("/folders/{folder_id}", response_model=FolderRead)
def rename_folder(
    folder_id: int,
    data: FolderRename,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as session:
        folder = get_accessible_active_folder(session, folder_id, current_user.id)
        new_name = data.new_name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Folder name cannot be empty")

        if has_active_folder_name_conflict(
            session,
            current_user.id,
            folder.parent_folder_id,
            new_name,
            exclude_folder_id=folder.id,
        ):
            raise HTTPException(
                status_code=409,
                detail="A folder with the same name already exists in this location",
            )

        folder.name = new_name
        folder.updated_at = utcnow()

        try:
            session.commit()
            session.refresh(folder)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Folder could not be renamed because the database rejected the update",
            )

        return folder


@app.delete("/folders/{folder_id}", response_model=MessageResponse)
def delete_folder(folder_id: int, current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        folder = session.get(Folder, folder_id)

        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have access to this folder")
        if folder.is_deleted:
            raise HTTPException(status_code=400, detail="Folder is already deleted")

        soft_delete_folder_tree(session, folder)
        recalculate_used_storage(session, current_user.id)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Folder could not be deleted because the database rejected the update",
            )

        return {"message": "Folder deleted"}


@app.patch("/files/{file_id}", response_model=FileRead)
def rename_file(file_id: int, data: FileRename, current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        file = session.get(File, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You do not have access to this file")

        if file.is_deleted:
            raise HTTPException(
                status_code=400, detail="Cannot rename a deleted file")

        new_name = data.new_name.strip()
        if not new_name:
            raise HTTPException(
                status_code=400, detail="File name cannot be empty")

        if has_active_file_name_conflict(
            session,
            file.owner_id,
            file.folder_id,
            new_name,
            exclude_file_id=file_id,
        ):
            raise HTTPException(
                status_code=409,
                detail="A file with the same name already exists in this location",
            )

        file.original_name = new_name
        file.updated_at = utcnow()

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


@app.post("/files/{file_id}/restore", response_model=FileRead)
def restore_file(
    file_id: int,
    data: FileRestore,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as session:
        file = session.get(File, file_id)
        user = session.get(User, current_user.id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have access to this file")
        if not file.is_deleted:
            raise HTTPException(status_code=400, detail="File is not deleted")
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        target_folder_id = data.folder_id if data.folder_id is not None else file.folder_id
        if target_folder_id is not None:
            target_folder = get_accessible_active_folder(session, target_folder_id, current_user.id)
            target_folder_id = target_folder.id

        if has_active_file_name_conflict(
            session,
            current_user.id,
            target_folder_id,
            file.original_name,
            exclude_file_id=file.id,
        ):
            raise HTTPException(
                status_code=409,
                detail="A file with the same name already exists in this location",
            )

        if user.used_storage_bytes + file.size_bytes > user.storage_quota_bytes:
            raise HTTPException(
                status_code=413,
                detail="Restoring this file exceeds the user's storage quota",
            )

        file.folder_id = target_folder_id
        file.is_deleted = False
        file.deleted_at = None
        file.updated_at = utcnow()
        recalculate_used_storage(session, current_user.id)

        try:
            session.commit()
            session.refresh(file)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="File could not be restored because the database rejected the update",
            )

        return file


@app.delete("/files/{file_id}", response_model=MessageResponse)
def delete_file(file_id: int, current_user: User = Depends(get_current_user)):
    with SessionLocal() as session:
        file = session.get(File, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You do not have access to this file")

        if file.is_deleted:
            raise HTTPException(
                status_code=400, detail="File is already deleted")

        file.is_deleted = True
        file.deleted_at = utcnow()
        file.updated_at = utcnow()
        recalculate_used_storage(session, current_user.id)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="File could not be deleted because the database rejected the update",
            )

        return {"message": "File deleted"}
