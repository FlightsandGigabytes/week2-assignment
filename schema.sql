-- ============================================================
-- library.db — schema for a small library
-- MSAI-5523, Module 2
--
-- Design summary:
--   * A "book" is a TITLE (the work), separate from the physical
--     COPIES of it on the shelf.
--   * Authors are first-class: a book can have many authors and an
--     author can write many books (many-to-many via book_authors).
--   * Members are cardholders; we verify a government ID at signup
--     but never store the raw ID number (only a verification flag
--     and the id type). The library card number is the member key.
--   * Loan state (checked out / overdue) is DERIVED from borrowings,
--     not stored. A copy's physical condition IS stored on the copy.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------- books: a title / work ----------
CREATE TABLE books (
    book_id           INTEGER PRIMARY KEY,
    title             TEXT    NOT NULL,
    isbn              TEXT,                      -- stored as text (preserves leading zeros)
    publication_year  INTEGER,
    genre             TEXT                       -- not in source data; assigned by the library
);

-- ---------- authors: one row per author ----------
CREATE TABLE authors (
    author_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE             -- same author is stored once, linked to many books
);

-- ---------- book_authors: many-to-many link ----------
CREATE TABLE book_authors (
    book_id    INTEGER NOT NULL,
    author_id  INTEGER NOT NULL,
    PRIMARY KEY (book_id, author_id),           -- a book-author pairing is unique
    FOREIGN KEY (book_id)   REFERENCES books(book_id),
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

-- ---------- copies: a physical copy on the shelf ----------
CREATE TABLE copies (
    copy_id   INTEGER PRIMARY KEY,
    book_id   INTEGER NOT NULL,
    status    TEXT NOT NULL DEFAULT 'available'
                 CHECK (status IN ('available', 'lost', 'damaged', 'withdrawn')),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

-- ---------- members: a cardholder ----------
CREATE TABLE members (
    member_id          INTEGER PRIMARY KEY,     -- the library card number
    full_name          TEXT NOT NULL,
    member_type        TEXT NOT NULL DEFAULT 'adult'
                          CHECK (member_type IN ('adult', 'minor')),
    join_date          TEXT NOT NULL,           -- ISO date 'YYYY-MM-DD'
    id_verified        INTEGER NOT NULL DEFAULT 0 CHECK (id_verified IN (0, 1)),
    id_type            TEXT,                     -- e.g. 'drivers_license'; raw ID number NOT stored
    guardian_name      TEXT,                     -- for minors; null for adults
    guardian_member_id INTEGER,                  -- optional: guardian who is also a cardholder
    FOREIGN KEY (guardian_member_id) REFERENCES members(member_id)
);

-- ---------- borrowings: a checkout event ----------
CREATE TABLE borrowings (
    borrowing_id   INTEGER PRIMARY KEY,
    member_id      INTEGER NOT NULL,
    copy_id        INTEGER NOT NULL,
    checkout_date  TEXT NOT NULL,                -- ISO date 'YYYY-MM-DD'
    due_date       TEXT NOT NULL,                -- 2-week default; can be extended (renewals)
    return_date    TEXT,                         -- NULL means still out
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (copy_id)   REFERENCES copies(copy_id)
);

-- ---------- indexes to support lookups ----------
CREATE INDEX idx_copies_book        ON copies(book_id);
CREATE INDEX idx_book_authors_author ON book_authors(author_id);
CREATE INDEX idx_borrowings_member  ON borrowings(member_id);
CREATE INDEX idx_borrowings_copy    ON borrowings(copy_id);
CREATE INDEX idx_borrowings_open    ON borrowings(return_date);
