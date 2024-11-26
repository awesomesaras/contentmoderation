import os
from dotenv import load_dotenv
import anthropic
import json
from config import user_comments, unsafe_categories

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client with API key from environment variables
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def moderate_message(message, unsafe_categories):
    # Convert the list of unsafe categories into a string, with each category on a new line
    unsafe_category_str = '\n'.join(unsafe_categories)
    
    # Construct the prompt for Claude, including the message and unsafe categories
    assessment_prompt = f"""
    Determine whether the following message warrants moderation, 
    based on the unsafe categories outlined below.
    
    Message:
    <message>{message}</message>

    Unsafe Categories:
    <categories>
    {unsafe_category_str}
    </categories>

    Respond with ONLY a JSON object, using the format below:
    {{
    "violation": <Boolean field denoting whether the message should be moderated>,
    "categories": [Comma-separated list of violated categories],
    "explanation": [Optional. Only include if there is a violation.]
    }}"""

    # Send the request to Claude using the latest API syntax with all required parameters
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": assessment_prompt}
        ]
    )
    
    try:
        # Get the response text and parse it as JSON
        response_text = response.content[0].text
        assessment = json.loads(response_text)
        
        # Extract the violation status from the assessment
        contains_violation = assessment.get('violation', False)
        
        # If there's a violation, get the categories and explanation; otherwise, use empty defaults
        violated_categories = assessment.get('categories', []) if contains_violation else []
        explanation = assessment.get('explanation') if contains_violation else None
        
        return contains_violation, violated_categories, explanation
    except json.JSONDecodeError as e:
        print(f"Error parsing Claude's response: {e}")
        print(f"Raw response: {response_text}")
        return False, [], "Error processing response"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Raw response content: {response.content}")
        return False, [], "Error processing response"

# Process each comment and print the results
if __name__ == "__main__":
    print("Starting content moderation...\n")
    for comment in user_comments:
        print(f"Comment: {comment}")
        try:
            violation, violated_categories, explanation = moderate_message(comment, unsafe_categories)
            
            if violation:
                print(f"Violated Categories: {', '.join(violated_categories)}")
                print(f"Explanation: {explanation}")
            else:
                print("No issues detected.")
            print("-" * 80)  # Add a separator between comments
        except Exception as e:
            print(f"Error processing comment: {str(e)}")
            print("-" * 80)  # Add a separator between comments