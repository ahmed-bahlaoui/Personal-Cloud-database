-- =========================================
-- SEED DATA FOR PERSONAL CLOUD STORAGE APP
-- =========================================

-- Optional cleanup if you want to reseed from scratch
-- DELETE FROM files;
-- DELETE FROM folders;
-- DELETE FROM users;

-- =========================================
-- USERS
-- =========================================
INSERT INTO
    users (
        id,
        email,
        username,
        password_hash,
        storage_quota_bytes,
        used_storage_bytes
    )
VALUES (
        1,
        'ahmed@example.com',
        'ahmed',
        'hashed_pw_1',
        1073741824,
        0
    ),
    (
        2,
        'wiam@example.com',
        'wiam',
        'hashed_pw_2',
        2147483648,
        0
    ),
    (
        3,
        'youssef@example.com',
        'youssef',
        'hashed_pw_3',
        1073741824,
        0
    );


-- =========================================
-- FOLDERS
-- =========================================
-- Ahmed's folders
INSERT INTO
    folders (
        id,
        owner_id,
        parent_folder_id,
        name,
        is_deleted,
        deleted_at
    )
VALUES (
        1,
        1,
        NULL,
        'Documents',
        FALSE,
        NULL
    ),
    (
        2,
        1,
        NULL,
        'Pictures',
        FALSE,
        NULL
    ),
    (
        3,
        1,
        1,
        'University',
        FALSE,
        NULL
    ),
    (
        4,
        1,
        1,
        'Administrative',
        FALSE,
        NULL
    ),
    (
        5,
        1,
        2,
        'Vacations',
        FALSE,
        NULL
    ),
    (
        6,
        1,
        2,
        'Screenshots',
        FALSE,
        NULL
    );

-- Wiam's folders
INSERT INTO
    folders (
        id,
        owner_id,
        parent_folder_id,
        name,
        is_deleted,
        deleted_at
    )
VALUES (
        7,
        2,
        NULL,
        'Work',
        FALSE,
        NULL
    ),
    (
        8,
        2,
        NULL,
        'Personal',
        FALSE,
        NULL
    ),
    (
        9,
        2,
        7,
        'Reports',
        FALSE,
        NULL
    );

-- Youssef's folders
INSERT INTO
    folders (
        id,
        owner_id,
        parent_folder_id,
        name,
        is_deleted,
        deleted_at
    )
VALUES (
        10,
        3,
        NULL,
        'Projects',
        FALSE,
        NULL
    ),
    (11, 3, 10, 'ML', FALSE, NULL);

-- =========================================
-- FILES
-- =========================================
INSERT INTO
    files (
        id,
        owner_id,
        folder_id,
        original_name,
        storage_key,
        mime_type,
        size_bytes,
        checksum,
        is_deleted,
        deleted_at
    )
VALUES
    -- Ahmed files
    (
        1,
        1,
        1,
        'cv.pdf',
        'user_1/docs/cv_001.pdf',
        'application/pdf',
        245760,
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        FALSE,
        NULL
    ),
    (
        2,
        1,
        3,
        'ml_notes.pdf',
        'user_1/docs/university/ml_notes_001.pdf',
        'application/pdf',
        512000,
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        FALSE,
        NULL
    ),
    (
        3,
        1,
        3,
        'database_course.docx',
        'user_1/docs/university/database_course_001.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        128000,
        'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
        FALSE,
        NULL
    ),
    (
        4,
        1,
        2,
        'beach.png',
        'user_1/pictures/beach_001.png',
        'image/png',
        1048576,
        'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
        FALSE,
        NULL
    ),
    (
        5,
        1,
        5,
        'marrakech.jpg',
        'user_1/pictures/vacations/marrakech_001.jpg',
        'image/jpeg',
        2097152,
        'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
        FALSE,
        NULL
    ),
    (
        6,
        1,
        6,
        'error_screenshot.png',
        'user_1/pictures/screenshots/error_001.png',
        'image/png',
        350000,
        'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
        FALSE,
        NULL
    ),
    (
        7,
        1,
        NULL,
        'todo.txt',
        'user_1/root/todo_001.txt',
        'text/plain',
        2048,
        '1111111111111111111111111111111111111111111111111111111111111111',
        FALSE,
        NULL
    ),
    (
        8,
        1,
        4,
        'cin_scan.pdf',
        'user_1/docs/admin/cin_scan_001.pdf',
        'application/pdf',
        700000,
        '2222222222222222222222222222222222222222222222222222222222222222',
        TRUE,
        CURRENT_TIMESTAMP
    ),
-- Sara files
(
    9,
    2,
    7,
    'meeting_notes.txt',
    'user_2/work/meeting_notes_001.txt',
    'text/plain',
    4096,
    '3333333333333333333333333333333333333333333333333333333333333333',
    FALSE,
    NULL
),
(
    10,
    2,
    9,
    'q1_report.xlsx',
    'user_2/work/reports/q1_report_001.xlsx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    860160,
    '4444444444444444444444444444444444444444444444444444444444444444',
    FALSE,
    NULL
),
(
    11,
    2,
    8,
    'passport_scan.pdf',
    'user_2/personal/passport_scan_001.pdf',
    'application/pdf',
    650000,
    '5555555555555555555555555555555555555555555555555555555555555555',
    FALSE,
    NULL
),
-- Youssef files
(
    12,
    3,
    10,
    'app_architecture.pdf',
    'user_3/projects/app_architecture_001.pdf',
    'application/pdf',
    900000,
    '6666666666666666666666666666666666666666666666666666666666666666',
    FALSE,
    NULL
),
(
    13,
    3,
    11,
    'model_results.csv',
    'user_3/projects/ml/model_results_001.csv',
    'text/csv',
    150000,
    '7777777777777777777777777777777777777777777777777777777777777777',
    FALSE,
    NULL
),
(
    14,
    3,
    NULL,
    'readme.md',
    'user_3/root/readme_001.md',
    'text/markdown',
    3000,
    '8888888888888888888888888888888888888888888888888888888888888888',
    FALSE,
    NULL
);

-- =========================================
-- UPDATE USED STORAGE
-- =========================================
UPDATE users u
SET
    used_storage_bytes = (
        SELECT COALESCE(SUM(f.size_bytes), 0)
        FROM files f
        WHERE
            f.owner_id = u.id
            AND f.is_deleted = FALSE
    );