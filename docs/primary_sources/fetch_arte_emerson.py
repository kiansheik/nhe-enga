import requests
from bs4 import BeautifulSoup
import re

# List of page identifiers
page_map = [['01'], ['01a', '02'], ['02a', '03'], ['03a', '04'], ['04a', '05'], ['05a', '06'], ['06a', '07'], ['07a', '08'], ['08a', '09'], ['09a', '10'], ['10a', '11'], ['11a', '12'], ['12a', '13'], ['13a', '14'], ['14a', '15'], ['15a', '16'], ['16a', '17'], ['17a', '18'], ['18a', '19'], ['19a', '20'], ['20a', '21'], ['21a', '22'], ['22a', '23'], ['23a', '24'], ['24a', '25'], ['25a', '26'], ['26a', '27'], ['27a', '28'], ['28a', '29'], ['29a', '30'], ['30a', '31'], ['31a', '32'], ['32a', '33'], ['33a', '34'], ['34a', '35'], ['35a', '36'], ['36a', '37'], ['37a', '38'], ['38a', '39'], ['39a', '40'], ['40a', '41'], ['41a', '42'], ['42a', '43'], ['43a', '44'], ['44a', '45'], ['45a', '46'], ['46a', '47'], ['47a', '48'], ['48a', '49'], ['49a', '50'], ['50a', '51'], ['51a', '52'], ['52a', '53'], ['53a', '54'], ['54a', '55'], ['55a', '56'], ['56a', '57'], ['57a', '58'], ['58a']]

# Flatten the page identifiers into a single list
pages = [item for sublist in page_map for item in sublist]

# Initialize a list to store the content
content_list = []

# Base URL
base_url = 'http://www.etnolinguistica.org/arte:{}'

# Headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

for page_id in pages:
    main_url = base_url.format(page_id)
    print(f'Fetching main page: {main_url}')
    main_response = requests.get(main_url, headers=headers)
    if main_response.status_code == 200:
        main_soup = BeautifulSoup(main_response.content, 'html.parser')
        
        # Find the iframe with src starting with '/arte:'
        iframe = main_soup.find('iframe', src=re.compile(r'^/arte:'))
        if iframe and iframe.has_attr('src'):
            iframe_src = iframe['src']
            # Construct the full URL
            iframe_url = 'http://www.etnolinguistica.org' + iframe_src
            print(f'Fetching iframe content: {iframe_url}')
            iframe_response = requests.get(iframe_url, headers=headers)
            if iframe_response.status_code == 200:
                iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')
                pre_content = iframe_soup.select_one('body > pre')
                if pre_content:
                    content_html = pre_content.decode_contents()
                    content_list.append(content_html)
                else:
                    print(f'No <pre> content found in iframe {iframe_url}')
            else:
                print(f'Failed to fetch iframe content from {iframe_url}')
        else:
            print(f'Iframe with src starting with /arte: not found on page {main_url}')
    else:
        print(f'Failed to fetch main page {main_url}')

# Combine the content with a separator
separator = '<hr style="page-break-after: always;">'
full_content = separator.join(content_list)

# Wrap in basic HTML structure
html_output = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Combined Content</title>
</head>
<body>
{full_content}
</body>
</html>'''

# Save to an HTML file
with open('combined_content.html', 'w', encoding='utf-8') as f:
    f.write(html_output)

print('Combined HTML content has been saved to combined_content.html')
