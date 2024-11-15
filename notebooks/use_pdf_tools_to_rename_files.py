"""
A notebook for experimenting with different
packages to extract metadata from PDFs and
use this to rename or organize PDF files.
"""

# %% LIBRARY IMPORTS

import glob
import os
import re

import fitz

# %% PATH TO TEST PDF FILES

path_to_pdfs = "../../../Reading/PAPERS/Cretaceous/NJLC-Unsorted/"

# %% CODE TO RENAME PDFS


def extract_metadata(
    pdf_path: str,
) -> tuple[str, str, str]:
    """
    Extract metadata (title, author,
    publication year) from a PDF.
    """
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        title = metadata.get("title", "")
        author = metadata.get("author", "")
        year = metadata.get("year", "")
        return title, author, year
    except Exception as e:
        print(
            f"Error extracting metadata from {pdf_path}: {e}"
        )
        return "", "", ""


def create_abbreviation(title: str) -> str:
    """
    Create an abbreviation from the title.
    punctuation is removed before
    abbreviation.
    """
    # remove punctuation and split title into words
    title_clean = re.sub(
        r"[^\w\s]", "", title
    )  # removes punctuation
    words = title_clean.split()
    abbreviation = "".join(
        [word[0].upper() for word in words]
    )
    return abbreviation


def rename_pdf(
    pdf_path: str,
    title: str,
    author: str,
    year: str,
):
    """Rename the PDF based on the extracted metadata."""
    if not title or not author or not year:
        print(
            f"Missing necessary metadata for {pdf_path}, skipping renaming."
        )
        return
    try:
        # process the title into abbreviation
        abbreviation = create_abbreviation(title)
        # format new name: YYYY-Abbreviation-LastNameFirstAuthor
        author_last_name, author_first_name = (
            author.split(",")[0].strip(),
            (
                author.split(",")[1].strip()
                if "," in author
                else author.strip()
            ),
        )
        formatted_name = f"{year}-{abbreviation}-{author_last_name}{author_first_name[0].upper()}"
        # generate new file path
        new_pdf_path = os.path.join(
            os.path.dirname(pdf_path),
            formatted_name + ".pdf",
        )
        # rename the file
        os.rename(pdf_path, new_pdf_path)
        print(
            f"Renamed: {pdf_path} -> {new_pdf_path}"
        )
    except Exception as e:
        print(f"Error renaming {pdf_path}: {e}")


def process_pdfs(pdf_folder: str):
    """process all PDFs in a folder and its subfolders."""
    # use glob to recursively find all PDF files in the folder and its subfolders
    pdf_files = glob.glob(
        os.path.join(pdf_folder, "**", "*.pdf"),
        recursive=True,
    )
    for pdf_path in pdf_files:
        title, author, year = extract_metadata(
            pdf_path
        )
        if title and author and year:
            rename_pdf(
                pdf_path, title, author, year
            )
        else:
            print(
                f"Missing metadata for {pdf_path}"
            )


# %% PROCESS PDFS

# rename all pdfs
process_pdfs(path_to_pdfs)

# %%
