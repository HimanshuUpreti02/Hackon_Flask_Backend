import json
import re
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to preprocess text
def preprocess_text(text):
    # Convert to lowercase, remove punctuation, and split into tokens
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    tokens = text.split()
    # Remove common stop words (you can add more to this list)
    stop_words = set(["the", "a", "an", "in", "on", "at", "for", "to", "and"])
    tokens = [token for token in tokens if token not in stop_words]
    return tokens


# Calculate the cosine similarity between two texts
def cosine_similarity(text1, text2):
    tokens1 = preprocess_text(text1)
    tokens2 = preprocess_text(text2)

    # Create a vocabulary from both texts
    vocab = set(tokens1 + tokens2)

    # Create one-hot encoded vectors for each text
    vector1 = [tokens1.count(word) for word in vocab]
    vector2 = [tokens2.count(word) for word in vocab]

    # Calculate the dot product of the vectors
    dot_product = sum(a * b for a, b in zip(vector1, vector2))

    # Calculate the norms of the vectors
    norm1 = sum(a**2 for a in vector1) ** 0.5
    norm2 = sum(b**2 for b in vector2) ** 0.5

    # Calculate the cosine similarity
    if norm1 * norm2 == 0:
        return 0.0  # Handle division by zero
    cosine_similarity = dot_product / (norm1 * norm2)

    return cosine_similarity


def relevancy_list_from_query(user_query):
    similarity_threshold = 3

    with open("phone_dataset.json", "r") as json_file:
        json_database = json.load(json_file)

    relevant_products = []
    for entry in json_database:
        product_title = entry["title"]
        product_brand = entry["brand"]
        product_description = entry["description"]
        product_price = str(entry["price"])
        product_rating = str(entry["rating"])

        weighted_similarity = 0.0
        weighted_similarity += cosine_similarity(user_query, product_title) * 8
        weighted_similarity += cosine_similarity(user_query, product_brand) * 10
        weighted_similarity += cosine_similarity(user_query, product_description) * 50
        weighted_similarity += cosine_similarity(user_query, product_price) * 15
        weighted_similarity += cosine_similarity(user_query, product_rating) * 20

        if weighted_similarity > similarity_threshold:
            # print(weighted_similarity)
            # print(entry)
            relevant_products.append((entry, weighted_similarity))

    sorted_results = sorted(relevant_products, key=lambda x: x[1], reverse=True)

    sorted_json_results = (
        [entry[0] for entry in sorted_results]
        if sorted_results
        else [entry[0] for entry in relevant_products]
    )[:10]

    return sorted_json_results



def main(query):
    response_template = f"""You are an e-commerce virtual agent chat bot.
    Your task is to make user shopping experience more interactive and better.
    You should strictly follow all the rules mentioned below:-
    - User will provide a query and would expect to get results/relevant products based on the query.
    - User should mention the following details in the query to get the best results.
        ## RULES
        - Brand of the product should be mentioned or at least the user mentions that any brand is acceptable in the query. (It is a required field)
        - Specifications of the product is mentioned in the query. Eg: 14MP camera, cotton clothes, or mentions details about the products or "any specifications". (It is a required field)
        - User should mention the price range of the product in the query. (It is a required field)
        - User can also mention the rating of the product required in the query. (It is a not a required field)
    
    - If you think the user's query does not follows the above mentioned rules. You need to follow the rules mentioned below.
        - If there are multiple rules that are not followed above. Ask the user to give a missing detail (Ensure that you ask the user to provide only a single missing details in the query). Eg:- If the user's query is missing [brand, price and specifications] you only need to ask the user to either provide a brand or price-range or specifications.
        - Eg if you think the brand, price, specifications is missing. Ask for only one detail at a time.
        - To answer this type of query return the result.

    - If you think the user's query follows the above mentioned rules. Generate a response follow the below mentioned rules.
        - Generate a simple response for the acknowledgement of the user's query.
        - Also generate a reduced query (only important keywords) which can be used by the system admins to do relevancy search for fetch products from knowledge database.
        - You are only required to respond with the acknowledgement of the query and not with the results based on the query.
        - Use this format to answer this type of query "[Acknowledgement] ||| [REDUCED QUERY]" Eg: "Awesome! here are the products based on the query ||| [Append the reduced query for relevancy search here] (This is very important rule to follow).
    Stricly adhere to the above guidlines and be professional"""
    # Load your API key from an environment variable or secret management service

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": response_template},
            {
                "role": "user",
                "content": "Give me products based on this query : "
                + query,
            },
        ],
    )
    content = response["choices"][0]["message"]["content"]

    if len(content.split("|||")) > 1:
        parts = content.split("|||")
        stripped_parts = [part.strip() for part in parts]
        content = stripped_parts[0]
        query = stripped_parts[1]
        sorted_json_results = relevancy_list_from_query(query)

        dict = {"content" : content,
            "result" : sorted_json_results}
        print(dict)
        print("idhar hu bhaiya abhi")
        return dict

    else :
        dict = {
            "content" : content,
            "result" : []
        }
        return dict
