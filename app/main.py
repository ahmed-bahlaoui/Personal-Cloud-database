import datetime

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
    FolderCreate,
    FolderRead,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.settings import ALLOWED_ORIGINS
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
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

        existing_folder_query = select(Folder).where(
            Folder.owner_id == current_user.id,
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

        existing_folder = session.execute(
            existing_folder_query).scalar_one_or_none()
        if existing_folder:
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

        duplicate_file_query = select(File).where(
            File.id != file_id,
            File.owner_id == file.owner_id,
            File.original_name == new_name,
            ~File.is_deleted,
        )

        if file.folder_id is None:
            duplicate_file_query = duplicate_file_query.where(
                File.folder_id.is_(None))
        else:
            duplicate_file_query = duplicate_file_query.where(
                File.folder_id == file.folder_id
            )

        duplicate_file = session.execute(
            duplicate_file_query).scalar_one_or_none()
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
