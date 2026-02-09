CREATE TABLE teacher (
    tid TEXT NOT NULL PRIMARY KEY,
    tname TEXT NOT NULL,
    designation TEXT,
    did INTEGER(9) NOT NULL,
    dname TEXT,
    exp INTEGER,
    propic BLOB,
    idcard BLOB,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);
