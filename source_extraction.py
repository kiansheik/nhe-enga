# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility
import re
import gzip
import json
from tqdm import tqdm
from collections import Counter
from pdf2image import convert_from_path
import os

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

print("Saving VLB citations")
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

output_dir = 'docs/primary_sources/'
# open PDF "docs/primary_sources/vlb_drummond_1952.pdf" and save each page in "docs/primary_sources/vlb/{page_number_in_pdf}.png"
# reader = PdfReader('docs/primary_sources/vlb_drummond_1952.pdf')
# Path to your PDF file

pdf_path = 'docs/primary_sources/vlb_drummond_1952.pdf'
vlb_output_dir = f'{output_dir}vlb/'
# Check if the output directory is empty
if len(os.listdir(vlb_output_dir)) == 0:
    # Use pdf2image to convert each page of the PDF to an image
    images = convert_from_path(pdf_path)
    # Save each page as an image
    for i, image in tqdm(enumerate(images)):
        image_path = os.path.join(vlb_output_dir, f"{i+1}.png")
        image.save(image_path, 'PNG')
else:
    print("Output directory is not empty. Skipping conversion.")

print("Saving Anch. Arte citations")
citations = Counter()
malformed = Counter()
# Process VLB
for citation, count in entry_map['anch.'].most_common():
    instances = [x.strip() for x in citation.split(';') if 'anch., arte' in x.lower()]
    for instance in instances:
        is_malformed = False
        try:
            elements = [x.strip() for x in instance.split(',')]
            if elements[0] not in ('anch', 'anch.'):
                # print("no vlb", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            if elements[1] not in ('arte', 'arte.'):
                # print("no i", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            # if elements[2] is not a number, it's malformed
            page = int(elements[2].strip('v'))
        except Exception as e:
            # print("oops", elements)
            malformed.update([citation])
            is_malformed = True
            continue
        if not is_malformed:
            citations.update([(*elements[:3], elements[2].replace('v', 'a'))])

def generate_ancharte_page(n):
    if n == 0:
        return ["1"]
    if n == 58:
        return ["58a"]
    m = n + 1
    if n < 10:
        n = f"0{n}"
    if m < 10:
        m = f"0{m}"
    return [f"{n}a", f"{m}"]

pages = [generate_ancharte_page(i) for i in range(59)]

pdf_path = 'docs/primary_sources/anchieta_arte_1595.pdf'
ancharte_output_dir = f'{output_dir}ancharte/'
# Check if the output directory is empty
if len(os.listdir(ancharte_output_dir)) == 0:
    # Use pdf2image to convert each page of the PDF to an image
    images = convert_from_path(pdf_path)
    # Save each page as an image
    for i, image in tqdm(enumerate(images)):
        image_path = os.path.join(ancharte_output_dir, f"{i}.png")
        image.save(image_path, 'PNG')
else:
    print("Output directory is not empty. Skipping conversion.")


print("Saving Ar., Cat., 1618 citations")
citations = Counter()
malformed = Counter()
# Process VLB
for citation, count in entry_map['ar.'].most_common():
    instances = [x.strip() for x in citation.split(';') if 'ar., cat' in x.lower() and "1686" not in x]
    for instance in instances:
        is_malformed = False
        try:
            elements = [x.strip() for x in instance.split(',')]
            if elements[0] not in ('ar', 'ar.'):
                # print("no vlb", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            if elements[1] not in ('cat', 'cat.'):
                # print("no i", elements)
                malformed.update([citation])
                is_malformed = True
                continue
            # if elements[2] is not a number, it's malformed
            page = int(elements[2].strip('v'))
        except Exception as e:
            # print("oops", elements)
            malformed.update([citation])
            is_malformed = True
            continue
        if not is_malformed:
            citations.update([(*elements[:3], elements[2])])

def generate_arcat1618_page(n):
    page = int(n.strip('v'))*2 + 34
    if len(n) != len(n.strip('v')):
        page += 1
    return page

pages = [generate_arcat1618_page(i) for i in range(59)]

pdf_path = 'docs/primary_sources/ar.Cat.1618.pdf'
arcat1618_output_dir = f'{output_dir}arcat1618/'
# Maximum file size in bytes (e.g., 500KB)
max_file_size = 700 * 1024  # 500KB
# Minimum acceptable quality (to prevent infinite loop)
min_quality = 10

if len(os.listdir(arcat1618_output_dir)) == 0:
    images = convert_from_path(pdf_path)
    quality = 95
    for i, image in enumerate(tqdm(images)):
        image_path = os.path.join(arcat1618_output_dir, f"{i}.png")
        # Start with high quality
        image.save(image_path, 'PNG')
else:
    print("Output directory is not empty. Skipping conversion.")