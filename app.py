from flask import Flask, request, jsonify
from pathlib import Path
from utils import scrape_helper, neo4j_query_helper

import asyncio
import requests
import nltk
import ssl

import shutil
import tracemalloc

tracemalloc.start()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import endpoints


# app = Flask(__name__)
app = FastAPI()
# app.include_router(endpoints.read_router)
#cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
port = 3157
 
apiKey = "AIzaSyBogmROW5Z82EwUwL_SU7Etw6HMWjHCZvo"
searchId = "7256c75410b14434d"
bioSearchId = "918efd87408454290"
 
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

import asyncio
@app.get("/")
def home():
    return "Hello, Flask!"
@app.get("/api/v1/biodata")
async def biodata(request: Request):
    search_item = request.query_params.get('searchItem')

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
        search_results = [scrape_helper.process_profile(profile) for profile in responseData.get("items", []) if profile is not None]
                        
        # Iterate over each object in the 'data' array and print the 'sourceLink'
        for entry in search_results:
            source_link = entry.get("sourceLink")
            if source_link:
                await scrape_helper.scrape_site(source_link, output_folder)
 
        # Return the search results
        await scrape_helper.main(searchItem=search_item)
        return JSONResponse(status_code=200, content=search_results)

    except requests.RequestException as e:

        print(f"Error making API request: {e}")
        return JSONResponse(status_code=500, content="Internal Server Error")
 
@app.get("/api/v1/light-search")
def get_query_param(request: Request):
    try:
        # Get the 'name' query parameter from the request
        name = request.query_params.get('name')
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
                    extracted_name = scrape_helper.extract_name(profile['fullNames']).strip()  # Ensure to strip whitespace for a clean name
                    if scrape_helper.are_names_similar(name, extracted_name) and scrape_helper.isValidName(extracted_name) and extracted_name not in names_set:

                    # if isValidName(extract_name(profile['fullNames'])):
                        search_results.append({
                            'fullNames': extracted_name,
                            'sourceLink': profile['sourceLink'],
                            'pictures': profile['pictures'],
                            'searchItemType': profile['searchItemType'],
                        })
            
            names_set.add(extracted_name)  # Mark this name as added

            # Remove duplicates from search_results
            search_results = asyncio.run(scrape_helper.remove_duplicates(search_results))
            return JSONResponse(status_code=200, content=search_results)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content="Internal Server Error")



@app.get("/api/v1/search-results")
def search_results(request: Request):
        name = request.query_params.get('name')
        try:
            data = neo4j_query_helper.find(name)
            return JSONResponse(status_code=200, content=data)
        
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            return JSONResponse(status_code=200, content=search_results)

        
if __name__ == "__main__":
#    app.run(debug=True, port=port)
    uvicorn.run('app:app', host="localhost", port=port, reload=True)