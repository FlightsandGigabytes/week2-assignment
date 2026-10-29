"""Load the first N books from books.csv into library.db.

Splits the comma-separated `authors` field into individual authors,
stores each author once, and links books <-> authors via book_authors.
Run with: python3 -I load_books.py
"""
import csv
import sqlite3

N_BOOKS = 25
CSV_PATH = "books.csv"
DB_PATH = "library.db"


def to_int(value):
    """goodbooks stores year as a float string like '2008.0'."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # per-connection; must enable each time
    cur = conn.cursor()

    author_ids = {}  # name -> author_id, so each author is inserted only once

    def get_author_id(name):
        if name in author_ids:
            return author_ids[name]
        cur.execute("INSERT INTO authors (name) VALUES (?)", (name,))
        author_ids[name] = cur.lastrowid
        return author_ids[name]

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = 0
        for row in reader:
            if loaded >= N_BOOKS:
                break
            book_id = int(row["book_id"])
            cur.execute(
                "INSERT INTO books (book_id, title, isbn, publication_year, genre) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    book_id,
                    row["title"],
                    row["isbn"] or None,
                    to_int(row["original_publication_year"]),
                    None,  # genre not in source data; left null for now
                ),
            )
            # split "J.K. Rowling, Mary GrandPré" -> ["J.K. Rowling", "Mary GrandPré"]
            for raw in row["authors"].split(","):
                name = raw.strip()
                if not name:
                    continue
                aid = get_author_id(name)
                cur.execute(
                    "INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES (?, ?)",
                    (book_id, aid),
                )
            loaded += 1

    conn.commit()

    # report
    books = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    authors = cur.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
    links = cur.execute("SELECT COUNT(*) FROM book_authors").fetchone()[0]
    print(f"Loaded: {books} books, {authors} distinct authors, {links} book-author links")
    conn.close()


if __name__ == "__main__":
    main()
