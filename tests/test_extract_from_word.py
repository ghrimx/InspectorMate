import mammoth

def extract_hash_lines(docx_path):
    """
    Extract all lines starting with '#' from a Word (.docx) document using mammoth.
    """
    with open(docx_path, "rb") as docx_file:
        result = mammoth.extract_raw_text(docx_file)
        text = result.value  # The raw text extracted

    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("#")]
    return lines


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract lines starting with '#' from a Word document using mammoth.")
    parser.add_argument("docx_path", help="Path to the .docx file")
    parser.add_argument("-o", "--output", help="Optional output text file")

    args = parser.parse_args()

    lines = extract_hash_lines(args.docx_path)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        print(f"Extracted {len(lines)} lines to {args.output}")
    else:
        print("\n".join(lines))
