# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility
import re
import gzip
import json
from tqdm import tqdm
from collections import Counter
from pdf2image import convert_from_path

regex = r'\(.*?\)'

with open('docs/primary_sources/DTAbib.txt', 'r') as file:
    text = file.read()
    trusted_authors = set([x.lower()[1:-1] for x in re.findall(regex, text)])
    trusted_authors = sorted(trusted_authors)
    print(trusted_authors)

with gzip.open('docs/dict-conjugated.json.gz', 'rt') as file:
    text = file.read()
    data = json.loads(text)
    # make a set of each string matching r"\((.*?)\)" in each raw_definition in the list

raw_sources = list()
for word in tqdm(data):
    matches = set([x.lower()[1:-1] for x in re.findall(regex, word['d'])])
    for match in matches:
        for key in trusted_authors:
            if key in match:
                raw_sources.append(match)

entry_map = {x:Counter() for x in trusted_authors}
for line in raw_sources:
    members = [x.strip() for x in line.split(';')]
    for member in members:
        for author in trusted_authors:
            if author in member:
                entry_map[author].update([line])

counts = []
for entry in entry_map:
    coll = entry_map[entry]
    # get the total number entered into coll
    total = sum(coll.values())
    counts.append((total, entry))

sorted_counts = sorted(counts, key=lambda x: x[0], reverse=True)
for count in sorted_counts:
    print(count)

citations = Counter()
malformed = Counter()
# Process VLB
for citation, count in entry_map['vlb'].most_common():
    instances = [x.strip() for x in citation.split(';') if 'vlb' in x.lower()]
    for instance in instances:
        is_malformed = False
        try:
            elements = [x.strip() for x in instance.split(',')]
            if elements[0] not in ('vlb', 'vlb.'):
                # print("no vlb", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            if elements[1] not in ('i', 'ii'):
                # print("no i", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            # if elements[2] is not a number, it's malformed
            page = int(elements[2])
        except Exception as e:
            # print("oops", elements)
            malformed.update([citation])
            is_malformed = True
            continue
        if not is_malformed:
            citations.update([(*elements[:3], page if elements[1] == 'i' else page + 154)])


print("Saving VLB citations")
# open PDF "docs/primary_sources/vlb_drummond_1952.pdf" and save each page in "docs/primary_sources/vlb/{page_number_in_pdf}.png"
# reader = PdfReader('docs/primary_sources/vlb_drummond_1952.pdf')
# Path to your PDF file
pdf_path = 'docs/primary_sources/vlb_drummond_1952.pdf'
# Use pdf2image to convert each page of the PDF to an image
images = convert_from_path(pdf_path)

# Save each page as an image
for i, image in tqdm(enumerate(images)):
    image_path = f"docs/primary_sources/vlb/{i+1}.png"
    image.save(image_path, 'PNG')