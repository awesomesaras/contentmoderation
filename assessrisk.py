import os
from dotenv import load_dotenv
import anthropic
import json
from config import user_comments, unsafe_categories

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client with API key from environment variables
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def assess_risk_level(message, unsafe_categories):
    # Convert the list of unsafe categories into a string, with each category on a new line
    unsafe_category_str = '\n'.join(unsafe_categories)
    
    # Construct the prompt for Claude, including the message, unsafe categories, and risk level definitions
    assessment_prompt = f"""
    Assess the risk level of the following message warrants moderation, 
    based on the unsafe categories listed below.
    
Message:
<message>{message}</message>

Unsafe Categories:
<categories>
{unsafe_category_str}
</categories>

Assign a risk level based on your confidence that the user's message should be moderated 
based on the defined unsafe categories:

0 - No risk
1 - Low risk
2 - Medium risk
3 - High risk

Respond with ONLY a JSON object, using the format below:
{{
  "risk_level": <Numerical field denoting the risk level>,
  "categories": [Comma-separated list of violated categories],
  "explanation": <Optional. Only include if risk level is greater than 0>
}}"""

    try:
        # Send the request to Claude using the latest API syntax with all required parameters
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": assessment_prompt}
            ]
        )
        
        # Get the response text and parse it as JSON
        response_text = response.content[0].text
        assessment = json.loads(response_text)
        
        # Extract the risk level, violated categories, and explanation from the assessment
        risk_level = assessment.get("risk_level", 0)
        violated_categories = assessment.get("categories", [])
        explanation = assessment.get("explanation")
        
        return risk_level, violated_categories, explanation
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Claude's response: {e}")
        print(f"Raw response: {response_text}")
        return 0, [], "Error processing response"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 0, [], f"Error processing response: {str(e)}"

def get_risk_level_text(risk_level):
    risk_levels = {
        0: "No risk",
        1: "Low risk",
        2: "Medium risk",
        3: "High risk"
    }
    return risk_levels.get(risk_level, "Unknown risk level")

# Process each comment and print the results
if __name__ == "__main__":
    print("Starting risk assessment...\n")
    for comment in user_comments:
        print(f"Comment: {comment}")
        try:
            risk_level, violated_categories, explanation = assess_risk_level(comment, unsafe_categories)
            
            print(f"Risk Level: {risk_level} - {get_risk_level_text(risk_level)}")
            if violated_categories:
                print(f"Violated Categories: {', '.join(violated_categories)}")
            if explanation:
                print(f"Explanation: {explanation}")
            
        except Exception as e:
            print(f"Error processing comment: {str(e)}")
        
        print("-" * 80)  # Add a separator between comments