from pathlib import Path

import app.main


def upload_sample_file(
    client,
    headers,
    filename: str = "report.txt",
    content: bytes = b"hello upload",
    folder_id: int | None = None,
):
    request_kwargs = {
        "headers": headers,
        "files": {"file": (filename, content, "text/plain")},
    }
    if folder_id is not None:
        request_kwargs["data"] = {"folder_id": str(folder_id)}
    return client.post("/files", **request_kwargs)


def test_upload_file_succeeds_in_root(client, register_and_login):
    headers = register_and_login()

    response = upload_sample_file(client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["original_name"] == "report.txt"
    assert body["folder_id"] is None
    assert body["size_bytes"] == len(b"hello upload")

    storage_path = app.main.STORAGE_ROOT / body["storage_key"]
    assert storage_path.exists()
    assert storage_path.read_bytes() == b"hello upload"


def test_upload_file_requires_authentication(client):
    response = upload_sample_file(client, headers={})

    assert response.status_code == 401


def test_upload_file_rejects_other_users_folder(client, register_and_login):
    owner_headers = register_and_login(
        username="owner1",
        email="owner1@example.com",
    )
    other_headers = register_and_login(
        username="other1",
        email="other1@example.com",
    )

    folder_response = client.post(
        "/folders",
        headers=owner_headers,
        json={"name": "private-folder", "parent_folder_id": None},
    )
    folder_id = folder_response.json()["id"]

    response = client.post(
        "/files",
        headers=other_headers,
        data={"folder_id": str(folder_id)},
        files={"file": ("report.txt", b"hello upload", "text/plain")},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this folder"


def test_upload_file_rejects_duplicate_name_in_same_folder(client, register_and_login):
    headers = register_and_login()

    first_response = upload_sample_file(client, headers, content=b"first file")
    second_response = upload_sample_file(client, headers, content=b"second file")

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A file with the same name already exists in this location"
    )


def test_upload_file_rejects_when_quota_is_exceeded(
    client,
    register_and_login,
):
    headers = register_and_login()

    me_response = client.get("/auth/me", headers=headers)
    user_id = me_response.json()["id"]

    with app.main.SessionLocal() as session:
        user = session.get(app.main.User, user_id)
        user.storage_quota_bytes = 5
        user.used_storage_bytes = 0
        session.commit()

    response = client.post(
        "/files",
        headers=headers,
        files={"file": ("large.txt", b"0123456789", "text/plain")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File upload exceeds the user's storage quota"


def test_delete_file_soft_deletes_and_recalculates_storage(client, register_and_login):
    headers = register_and_login()

    upload_response = upload_sample_file(client, headers, content=b"0123456789")
    assert upload_response.status_code == 201
    uploaded_file = upload_response.json()

    me_before_delete = client.get("/auth/me", headers=headers)
    assert me_before_delete.status_code == 200
    assert me_before_delete.json()["used_storage_bytes"] == 10

    delete_response = client.delete(f"/files/{uploaded_file['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "File deleted"

    trash_response = client.get("/trash/files", headers=headers)
    assert trash_response.status_code == 200
    trash_files = trash_response.json()
    assert len(trash_files) == 1
    assert trash_files[0]["id"] == uploaded_file["id"]
    assert trash_files[0]["is_deleted"] is True

    me_after_delete = client.get("/auth/me", headers=headers)
    assert me_after_delete.status_code == 200
    assert me_after_delete.json()["used_storage_bytes"] == 0


def test_restore_file_reactivates_file_and_recalculates_storage(client, register_and_login):
    headers = register_and_login()

    upload_response = upload_sample_file(client, headers, content=b"restore me")
    file_id = upload_response.json()["id"]

    delete_response = client.delete(f"/files/{file_id}", headers=headers)
    assert delete_response.status_code == 200

    restore_response = client.post(
        f"/files/{file_id}/restore",
        headers=headers,
        json={"folder_id": None},
    )

    assert restore_response.status_code == 200
    restored_file = restore_response.json()
    assert restored_file["id"] == file_id
    assert restored_file["is_deleted"] is False
    assert restored_file["deleted_at"] is None

    files_response = client.get("/files", headers=headers)
    assert files_response.status_code == 200
    active_files = files_response.json()
    assert len(active_files) == 1
    assert active_files[0]["id"] == file_id

    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["used_storage_bytes"] == len(b"restore me")


def test_restore_file_rejects_when_quota_is_exceeded(client, register_and_login):
    headers = register_and_login()

    upload_response = upload_sample_file(client, headers, filename="quota.txt", content=b"0123456789")
    file_id = upload_response.json()["id"]
    delete_response = client.delete(f"/files/{file_id}", headers=headers)
    assert delete_response.status_code == 200

    me_response = client.get("/auth/me", headers=headers)
    user_id = me_response.json()["id"]

    with app.main.SessionLocal() as session:
        user = session.get(app.main.User, user_id)
        user.storage_quota_bytes = 5
        user.used_storage_bytes = 0
        session.commit()

    restore_response = client.post(
        f"/files/{file_id}/restore",
        headers=headers,
        json={"folder_id": None},
    )

    assert restore_response.status_code == 413
    assert restore_response.json()["detail"] == (
        "Restoring this file exceeds the user's storage quota"
    )


def test_delete_folder_soft_deletes_descendants_and_recalculates_storage(client, register_and_login):
    headers = register_and_login()

    parent_response = client.post(
        "/folders",
        headers=headers,
        json={"name": "projects", "parent_folder_id": None},
    )
    assert parent_response.status_code == 201
    parent_folder = parent_response.json()

    child_response = client.post(
        "/folders",
        headers=headers,
        json={"name": "archive", "parent_folder_id": parent_folder["id"]},
    )
    assert child_response.status_code == 201
    child_folder = child_response.json()

    parent_file_response = upload_sample_file(
        client,
        headers,
        filename="parent.txt",
        content=b"12345",
        folder_id=parent_folder["id"],
    )
    child_file_response = upload_sample_file(
        client,
        headers,
        filename="child.txt",
        content=b"67890",
        folder_id=child_folder["id"],
    )
    assert parent_file_response.status_code == 201
    assert child_file_response.status_code == 201

    me_before_delete = client.get("/auth/me", headers=headers)
    assert me_before_delete.status_code == 200
    assert me_before_delete.json()["used_storage_bytes"] == 10

    delete_response = client.delete(f"/folders/{parent_folder['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Folder deleted"

    folders_response = client.get("/folders", headers=headers)
    assert folders_response.status_code == 200
    assert folders_response.json() == []

    trashed_folders_response = client.get("/trash/folders", headers=headers)
    assert trashed_folders_response.status_code == 200
    trashed_folder_ids = {folder["id"] for folder in trashed_folders_response.json()}
    assert parent_folder["id"] in trashed_folder_ids
    assert child_folder["id"] in trashed_folder_ids

    trashed_files_response = client.get("/trash/files", headers=headers)
    assert trashed_files_response.status_code == 200
    trashed_files = trashed_files_response.json()
    assert len(trashed_files) == 2
    assert all(file["is_deleted"] is True for file in trashed_files)

    me_after_delete = client.get("/auth/me", headers=headers)
    assert me_after_delete.status_code == 200
    assert me_after_delete.json()["used_storage_bytes"] == 0
