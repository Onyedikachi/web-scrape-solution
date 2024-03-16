from flask import Flask, request, jsonify
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse


import asyncio
import requests
import json
import re
import nltk
import ssl
import spacy

import requests
import shutil
import tracemalloc

tracemalloc.start()


app = Flask(__name__)
port = 3157
 
apiKey = "AIzaSyBogmROW5Z82EwUwL_SU7Etw6HMWjHCZvo"
searchId = "7256c75410b14434d"
bioSearchId = "918efd87408454290"

nlp = spacy.load("en_core_web_sm")
 
excluded_sites = ["twitter.com", "instagram.com", "facebook.com", "linkedin.com"]

# Specify the SSL certificate directory using the certifi package
nltk.data.path.append('/Users/mac/Desktop/IDDPYTHON/.venv/lib/python3.12/site-packages/certifi/cacert.pem')
# Download the punkt tokenizer models
nltk.download('punkt')

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

 
extracted_info = []
excluded_sites = ["twitter.com", "instagram.com", "facebook.com", "linkedin.com"]
 
async def scrape_site(url, file_url):
    try:
        page = requests.get(url)

        # Use asyncio.sleep to introduce a delay
        await asyncio.sleep(5)

        # Parse the HTML content using BeautifulSoup)
        soup = BeautifulSoup(page.content, "html.parser")
        extracted_text = soup.get_text()

        # Save extracted text to a text file
        text_file_path = file_url / f"{get_domain_from_url(url)}"

        with open(text_file_path, "w", encoding="utf-8") as file:
            file.write(extracted_text)

    except Exception as error:
        print("Error fetching website:", error)
def get_domain_from_url(url):

    hostname = urlparse(url).hostname

    return f"{hostname.replace('.', '_')}.txt"
async def main(searchItem):
    try:
        folder_path = Path(__file__).parent / "screenshots" / searchItem
        if folder_path.is_dir():

                files = [f for f in folder_path.iterdir() if f.is_file()]

                for file in files:
                    file_path = folder_path / file
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = file.read()

                    result_array = extract_biodata_information(data)
                    new_file_path = folder_path / "extracted.json"

                    extracted_info.append(result_array)

                    with open(new_file_path, "w", encoding="utf-8") as file:

                        json.dump(extracted_info, file, indent=2)
 
    except Exception as error:
        print("An error occurred:", error)
 
def extract_biodata_information(text):
    doc = nlp(text)
    dob_match = [ent for ent in doc.ents if ent.label_ == "DATE"]
    dob = dob_match[0].text if dob_match else None

    places = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    country = places[0] if places else None

    state = places[1] if len(places) > 1 else None
 
    # We need to implement extraction logic for gender and marital status based on requirements

    gender = None

    marital_status = None
 
    result = {
        "dob": dob,
        "country": country,
        "state": state,
        "gender": gender,
        "maritalStatus": marital_status,
    }
 
    return result
def process_profile(profile):
    """Process the profile data to extract and structure necessary information."""

    return {
        "fullNames": extract_name(profile.get("title", "")),
        "sourceLink": profile.get("link"),
        "pictures": extract_pictures(profile),
        "searchItemType": profile.get("kind")
    }
 
def extract_name(title):
    """Assuming a function to extract name from the title."""
    # Implement name extraction logic
    return title
 
def extract_pictures(profile):
    """Extract picture URLs from the profile."""

    pictures = []
    if "pagemap" in profile:
        if "cse_thumbnail" in profile["pagemap"]:
            pictures.extend([data["src"] for data in profile["pagemap"]["cse_thumbnail"]])

        if "metatags" in profile.get("pagemap", {}):
            pictures.extend([data["og:image"] for data in profile["pagemap"]["metatags"] if "og:image" in data])
        
        if "cse_image" in profile["pagemap"]:
            pictures.extend([data["src"] for data in profile["pagemap"]["cse_image"]])

    return pictures

def are_names_same(search_name, candidate_name):
    # Normalize both names by stripping leading/trailing spaces and converting to lowercase
    search_name_normalized = ' '.join(search_name.lower().split())
    candidate_name_normalized = ' '.join(candidate_name.lower().split())
    # Check if the candidate name matches the search name exactly
    return search_name_normalized == candidate_name_normalized

def are_names_similar(name1, name2):
    # Tokenize names into words
    tokens1 = set(word_tokenize(name1.lower()))
    tokens2 = set(word_tokenize(name2.lower()))

    # Calculate Jaccard similarity
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    jaccard_similarity = len(intersection) / len(union)

    # You can adjust the similarity threshold based on your requirements
    similarity_threshold = 0.1

    return jaccard_similarity >= similarity_threshold

async def remove_duplicates(input_array):
    unique_names_set = set()
    unique_names_array = []

    async def process_item(item):
        nonlocal unique_names_set, unique_names_array
        full_name = item['fullNames']

        if full_name not in unique_names_set:
            unique_names_set.add(full_name)
            unique_names_array.append(item)

    await asyncio.gather(*(process_item(item) for item in input_array))

    return unique_names_array

def extract_name(input_string):
    # Remove any content in parentheses or after a dash which often includes social media handles or additional info
    cleaned_input = re.sub(r'\(.*?\)|-\s.*$', '', input_string).strip()

    # Attempt to remove any trailing details after common descriptors like "•", " - ", "/", etc.
    cleaned_input = re.sub(r'•.*$|\/.*$', '', cleaned_input).strip()

    # Final cleanup to remove any residual artifacts like " -", ",", or "•" at the end of the name
    cleaned_input = re.sub(r'[\s\-•,]+$', '', cleaned_input).strip()

    # Extract the most likely name part before any remaining delimiters like " - " or " • "
    name_parts = re.split(r'[\s\-•,]+', cleaned_input)
    if len(name_parts) > 1:
        # Assuming the first two parts constitute the name in most cases
        return ' '.join(name_parts[:2])

    return cleaned_input

def isValidName(sentence):
    # Checks if the name contains only letters (and possibly spaces)
    # Adjust the regex as needed to fit your definition of a valid name
    return re.match(r'^[A-Za-z\s]+$', sentence) is not None

import asyncio
@app.route("/")
def home():
    return "Hello, Flask!"
@app.route("/api/v1/biodata", methods=["GET"])
async def biodata():
    search_item = request.args.get('searchItem')

    if not search_item:
        return jsonify(error="Missing required parameter: searchItem"), 400
 
    output_folder = Path(__file__).parent / "screenshots" / search_item

    if output_folder.exists() and output_folder.is_dir():

        shutil.rmtree(output_folder)

    output_folder.mkdir(parents=True, exist_ok=True)
 
    # Construct the query URL

    encoded_search_term = requests.utils.quote(search_item)
    encoded_query = requests.utils.quote("BioData")

    url = f"https://www.googleapis.com/customsearch/v1?key={apiKey}&cx={bioSearchId}&q={encoded_search_term}%20{encoded_query}"

    try:
        api_response = requests.get(url)
        api_response.raise_for_status()

        responseData = api_response.json()
        search_results = [process_profile(profile) for profile in responseData.get("items", []) if profile is not None]
                        
        # Iterate over each object in the 'data' array and print the 'sourceLink'
        for entry in search_results:
            source_link = entry.get("sourceLink")
            if source_link:
                await scrape_site(source_link, output_folder)
 
        # Return the search results
        await main(searchItem=search_item)
        return jsonify(status=200, message="Success", data=search_results), 200
 
    except requests.RequestException as e:

        print(f"Error making API request: {e}")

        return jsonify(error="Internal Server Error"), 500
 
 
@app.route("/api/v1/light-search")
def get_query_param():
    try:
        # Get the 'name' query parameter from the request
        name = request.args.get('name')

        # Check if 'name' is present
        if name is None:
            # Return an error message if 'name' is not present
            error_message = {'error': 'The query parameter "name" is missing.'}
            return jsonify(error_message), 400

        search_url = f"https://www.googleapis.com/customsearch/v1?key={apiKey}&cx={searchId}&q={name}"

        headers = {'Content-Type': 'application/json'}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            json_data = response.json()
            blogs = json_data.get("items", [])
            
            filtered_blogs = [
                {
                    'fullNames': blog['title'],
                    'sourceLink': blog['link'],
                    'searchItemType': None,
                    'pictures': [
                                data['src'] 
                    for data in blog['pagemap'].get('cse_thumbnail', []) 
                    if data.get('src')
                ] + [
                data['og:image'] 
            for data in blog['pagemap'].get('metatags', []) 
            if 'og:image' in data and data['og:image']
            ] + [
            data['src'] 
            for data in blog['pagemap'].get('cse_image', []) 
            if data.get('src')
           ],
            }
            for blog in blogs
            ]
            

            # Apply additional processing based on the JavaScript code
            search_results = []
            names_set = set()  # To track unique names
            for profile in filtered_blogs:
                    extracted_name = extract_name(profile['fullNames']).strip()  # Ensure to strip whitespace for a clean name
                    if are_names_similar(name, extracted_name) and isValidName(extracted_name) and extracted_name not in names_set:

                    # if isValidName(extract_name(profile['fullNames'])):
                        search_results.append({
                            'fullNames': extracted_name,
                            'sourceLink': profile['sourceLink'],
                            'pictures': profile['pictures'],
                            'searchItemType': profile['searchItemType'],
                        })
            
            names_set.add(extracted_name)  # Mark this name as added

            # Remove duplicates from search_results
            search_results = asyncio.run(remove_duplicates(search_results))
            return jsonify(search_results)

        print(f"Error: {response.status_code}")
        print(response.text)
        return jsonify({'error': 'Internal server error.'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error.'}), 500


if __name__ == "__main__":

   app.run(debug=True, port=port)