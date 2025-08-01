from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
import json
from tqdm import tqdm


def extract_definitions_by_color_and_size(pdf_path, target_color, min_font_size):
    total_pages = 711  # Adjust to match your PDF
    entries = []  # Store entries matching the criteria
    last_color = [0, 0, 0]
    current_entry = None  # Track the current word and its definition

    for i in tqdm(range(total_pages)):
        # Extract words from a single page
        for page_layout in extract_pages(pdf_path, page_numbers=[i]):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        for char in text_line:
                            if isinstance(char, LTChar):
                                color = char.graphicstate.ncolor  # Extract color
                                font_size = char.size  # Extract font size
                                text = char.get_text()

                                # Check if the character matches both color and size criteria
                                if color == target_color:
                                    if font_size >= min_font_size:
                                        # If there's a current entry, finalize it and store it
                                        if current_entry and last_color != target_color:
                                            # print(f"New entry: {text}, Color: {color}, Size: {font_size}")
                                            current_entry["definition"] = current_entry[
                                                "definition"
                                            ].strip()
                                            current_entry["word"] = current_entry[
                                                "word"
                                            ].strip()
                                            entries.append(current_entry)
                                            current_entry = None

                                        # If continuing the same entry, append the text
                                        if current_entry and last_color == target_color:
                                            current_entry["word"] += text
                                        else:
                                            # print(f"New entry: {text}, Color: {color}, Size: {font_size}")
                                            current_entry = {
                                                "word": text,
                                                "definition": "",
                                            }
                                        last_color = color
                                    # else:
                                else:
                                    # If an entry is active, add to its definition
                                    if current_entry:
                                        current_entry["definition"] += text
                                    last_color = color

                                # Update last seen color and font size
                # Save all entries to a JSON file
            with open(
                "docs/extracted_entries_nheengatu.json", "w", encoding="utf-8"
            ) as f:
                json.dump(entries, f, ensure_ascii=False, indent=4)

        # Print progress
        # print(f"Processed page {i + 1}/{total_pages}")

    # Add the last entry if it exists
    if current_entry:
        entries.append(current_entry)

    # Save all entries to a JSON file
    with open("docs/extracted_entries_nheengatu.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)

    print(f"Extraction complete! Found {len(entries)} entries.")


# Set the target color and minimum font size to avoid superscripts
target_color = [0.502, 0, 0]
min_font_size = 9.8  # Adjust based on your PDF's typical font sizes

# Update the path to your PDF file
pdf_path = "docs/primary_sources/2021_MarcelTwardowskyAvila_VCorr_dic.pdf"
extract_definitions_by_color_and_size(pdf_path, target_color, min_font_size)
