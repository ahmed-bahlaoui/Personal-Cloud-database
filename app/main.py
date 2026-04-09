from typing import Sequence

from db import SessionLocal
from models import File, Folder, User
from sqlalchemy import select


def print_users(users: Sequence[User]) -> None:
    print("Users:")
    for user in users:
        print(user)


def print_user_files(id: int, files: Sequence[File]) -> None:
    print(f"\nFiles of user {id}:")
    for file in files:
        print(file)


def print_user_folders(id: int, folders: Sequence[Folder]) -> None:
    print(f"\nFolders of user {id}:")
    for folder in folders:
        print(folder)


def get_user_files_by_id(id: int = 1) -> None:
    with SessionLocal() as session:
        files = session.execute(
            select(File).where(File.owner_id == id, ~File.is_deleted)
        ).scalars().all()
        print_user_files(id, files)


def get_user_folders_by_id(id: int = 1) -> None:
    with SessionLocal() as session:
        folders = session.execute(
            select(Folder).where(Folder.owner_id ==
                                 id, ~Folder.is_deleted)
        ).scalars().all()
        print_user_folders(id, folders)


def get_all_users() -> None:
    with SessionLocal() as session:
        users = session.execute(select(User)).scalars().all()
        print_users(users)


def main() -> None:
    get_all_users()
    get_user_files_by_id(1)
    get_user_folders_by_id(1)


if __name__ == "__main__":
    main()
