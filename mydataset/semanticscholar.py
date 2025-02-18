import os
import requests
import csv
import time

def search_semantic_scholar(query, max_papers=1000, batch_size=10):
    """
    Search the Semantic Scholar API for papers based on a query string.
    
    :param query: The search query string (e.g., keywords, author names, etc.).
    :param max_papers: Maximum number of papers to fetch.
    :param batch_size: Number of results to fetch in each request (maximum 100).
    :return: List of dictionaries containing metadata for each paper.
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    papers = []

    # Loop through batches of papers
    for offset in range(0, max_papers, batch_size):
        params = {
            "query": query,
            "offset": offset,
            "limit": min(batch_size, max_papers - len(papers)),  # Ensure not to exceed max_papers
            "fields": "title,authors,abstract,year,url,references"
        }

        print(f"\nQuerying Semantic Scholar with offset={offset} and limit={min(batch_size, max_papers - len(papers))}...")

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            print(f"Response status code: {response.status_code}")  # Log status code

            # Check if the response is JSON
            data = response.json()
            print("Successfully parsed JSON response.")  # Log successful JSON parsing

            if "data" in data and data["data"]:
                print(f"Found {len(data['data'])} papers in this batch.")  # Log number of papers found
                
                for entry in data["data"]:
                    title = entry.get("title", "No title")
                    authors = [author["name"] for author in entry.get("authors", [])]
                    abstract = entry.get("abstract", "No abstract available")
                    year = entry.get("year", "Unknown")
                    url = entry.get("url", "No URL available")
                    references = entry.get("references", [])
                    
                    reference_list = []
                    for idx, ref in enumerate(references, start=1):
                        ref_title = ref.get("title", "No title")
                        ref_authors = ", ".join(author["name"] for author in ref.get("authors", []))
                        ref_year = ref.get("year", "Unknown")
                        formatted_reference = f"[{idx}] {ref_authors}, \"{ref_title},\" {ref_year}."
                        reference_list.append(formatted_reference)

                    paper = {
                        "title": title,
                        "summary": abstract,
                        "authors": authors,
                        "published": year,
                        "pdf_url": url,
                        "references": " ".join(reference_list) if reference_list else "No references available"
                    }
                    papers.append(paper)

                    if len(papers) >= max_papers:
                        print(f"Reached the maximum of {max_papers} papers.")
                        break

            else:
                print("No papers found for the given query.")
                print("Full response:", data)  # Print full response for debugging
                break

            # If less papers than requested, we're done
            if len(data["data"]) < batch_size:
                print(f"Retrieved all available papers ({len(papers)} total).")
                break

            # Optional delay to avoid hitting rate limits
            time.sleep(2)

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Log HTTP errors
            print(f"Response content: {response.content}")  # Log the content of the response for more info
            break
        except requests.exceptions.RequestException as req_err:
            print(f"Request error: {req_err}")
            break
        except ValueError as json_err:
            print(f"JSON decode error: {json_err}")
            print(f"Response content: {response.content}")  # Log the response content
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    return papers

def save_papers_to_file(papers, folder_path, filename="semantic_scholar_papers.csv"):
    """
    Save the metadata of Semantic Scholar papers to a CSV file in a specified folder.
    
    :param papers: A list of dictionaries containing metadata for each paper.
    :param folder_path: The folder path where the CSV file will be saved.
    :param filename: The name of the output file.
    """
    
    # Ensure the folder exists
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)

    headers = ["Title", "Authors", "Published", "Summary", "PDF URL", "References"]

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for paper in papers:
                writer.writerow({
                    "Title": paper["title"],
                    "Authors": ", ".join(paper["authors"]),
                    "Published": paper["published"],
                    "Summary": paper["summary"],
                    "PDF URL": paper["pdf_url"],
                    "References": paper["references"]
                })

        print(f"Saved {len(papers)} papers to {file_path}")
    
    except Exception as e:
        print(f"Failed to save papers to file: {e}")

# Example usage
if __name__ == "__main__":
    query = "machine learning"  # Change this to your preferred query
    output_folder = "output_papers"  # Specify your desired output folder

    print("Starting paper retrieval...")

    # Fetch all papers for the query
    papers = search_semantic_scholar(query, max_papers=1000, batch_size=10)

    # Print out the results
    print(f"Total papers retrieved: {len(papers)}")
    if papers:
        for paper in papers:
            print(f"Title: {paper['title']}, Authors: {', '.join(paper['authors'])}, Published: {paper['published']}, PDF URL: {paper['pdf_url']}, References: {paper['references']}")
    else:
        print("No papers retrieved.")

    # Optionally save the results to a CSV file in the specified folder
    save_papers_to_file(papers, output_folder, "semantic_scholar_papers.csv")
import requests
import time
import csv
import os

def format_reference(ref):
    """Format the reference according to IEEE style."""
    ref_authors = ", ".join(author["name"] for author in ref.get("authors", []))
    ref_title = ref.get("title", "No title")
    ref_year = ref.get("year", "Unknown")
    
    return f"{ref_authors}, \"{ref_title},\" {ref_year}."

def search_semantic_scholar(query, max_papers=1000, batch_size=100, delay=3):
    """
    Search the Semantic Scholar API for papers based on a query string.
    
    :param query: The search query string (e.g., keywords, author names, etc.).
    :param max_papers: Maximum number of papers to fetch.
    :param batch_size: Number of results to fetch in each request (maximum 100).
    :param delay: Delay in seconds between requests to avoid overloading the API.
    :return: List of dictionaries containing metadata for each paper.
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    start_index = 0
    papers = []

    while len(papers) < max_papers:
        params = {
            "query": query,
            "offset": start_index,
            "limit": batch_size,
            "fields": "title,authors,abstract,year,url,references"  # Fields to retrieve
        }
        
        print(f"\nQuerying Semantic Scholar with offset={start_index} and limit={batch_size}...")
        response = requests.get(base_url, params=params)

        # Log the request URL
        print(f"Request URL: {response.url}")

        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error: Failed 