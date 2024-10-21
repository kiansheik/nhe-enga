# read dictionary
import json
import pdfplumber

pdf_path = "docs/primary_sources/2021_MarcelTwardowskyAvila_VCorr_dic.pdf"

def extract_words_with_formatting(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"--- Page {page_num + 1} ---")
            
            words = []  # Collect words with their formatting
            current_word = ""
            current_font_size = None

            # Iterate over characters and group them into words
            for char in page.objects.get("char", []):
                char_text = char["text"]
                font_size = char["size"]

                if char_text.strip():  # If it's not whitespace, add it to the current word
                    if current_font_size is None:
                        current_font_size = font_size  # Set the font size for the first char
                    
                    # If font size changes, treat it as the end of a word
                    if font_size != current_font_size:
                        words.append({"word": current_word, "font_size": current_font_size})
                        current_word = char_text  # Start new word
                        current_font_size = font_size  # Update font size
                    else:
                        current_word += char_text  # Continue building the word
                else:
                    if current_word:  # If word is complete, add it
                        words.append({"word": current_word, "font_size": current_font_size})
                        current_word = ""  # Reset for next word
                        current_font_size = None

            # Add any remaining word after the loop
            if current_word:
                words.append({"word": current_word, "font_size": current_font_size})

            # Print the collected words
            for word in words:
                print(f"Word: '{word['word']}', Font Size: {word['font_size']}")


extract_words_with_formatting(pdf_path)
