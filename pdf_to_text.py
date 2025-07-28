import fitz
import re
import sys

def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_ref(text, num):
  lines = text.splitlines()
  i = 0
  ref_block = ""
  while i < len(lines):
    if not lines[i].startswith(f"[{num}]"):
      i += 1
      continue
    print(lines[i])
    ref_block += re.sub(r"([.,])$", r"\1 ", lines[i].rstrip("-"))
    i += 1
    while i < len(lines) and not re.match(r"^\[\d+\]", lines[i]):
        ref_block += re.sub(r"([.,])$", r"\1 ", lines[i].rstrip("-"))
        i += 1

  return ref_block

if __name__ == "__main__":
    text = pdf_to_text("sample.pdf")
    ref = find_ref(text, int(sys.argv[1]))
    print(ref)
