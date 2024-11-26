import os
from dotenv import load_dotenv
import anthropic
import json
from config import user_comments

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client with API key from environment variables
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Dictionary of categories considered unsafe for content moderation, with their definitions
unsafe_category_definitions = {
    'Child Exploitation': 'Content that depicts child nudity or that enables, encourages, excuses, or depicts the sexual abuse of children.',
    'Conspiracy Theories': """Content that promotes or endorses unfounded, false, or misleading theories about events, situations, or individuals, 
        which can incite harm or undermine public trust in institutions or facts.""",
    'Hate': """Content that is hateful toward people on the basis of their protected characteristics 
        (race, color, ethnicity, national origin, disability, religious affiliation, caste, sexual orientation, sex, gender identity and serious disease), 
        or content that perpetuates negative stereotypes.""",
    'Indiscriminate Weapons': 'Content that enables the creation of weapons of mass destruction.', 
    'Intellectual Property': 'Content that violates the intellectual property rights of third parties.',
    'Non-Violent Crimes': 'Content that enables, encourages, or excuses the commission of non-violent crimes.', 
    'Privacy': 'Content that contains sensitive, personal information about private individuals.',
    'Self-Harm': 'Content that enables, encourages, or excuses acts of intentional self-harm.',
    'Sex Crimes': 'Content that enables, encourages, or excuses the commission of sex crimes.',
    'Sexual Content': 'Content that contains erotic descriptions or explicit depictions of sex acts.',
    'Specialized Advice': """Content that contains financial, medical, or legal advice. 
        Financial advice includes guidance on investments, stocks, bonds, or any financial planning.""",
    'Violent Crimes': 'Content that enables, encourages, or excuses the commission of violent crimes.', 
}

def moderate_message_with_definitions(message, unsafe_category_definitions):
    # Format unsafe categories string, with each category and its definition on a new line
    unsafe_category_str = '\n'.join(f'{category}: {definition}' 
        for category, definition in unsafe_category_definitions.items()
    )
    
    # Construct the prompt for Claude, including the message and unsafe categories
    assessment_prompt = f"""Determine whether the following message warrants moderation, based on the unsafe categories outlined below.

Message:
<message>{message}</message>

Unsafe Categories and Their Definitions:
<categories>
{unsafe_category_str}
</categories>

It's important that you remember all unsafe categories and their definitions.

Respond with ONLY a JSON object, using the format below:
{{
  "violation": <Boolean field denoting whether the message should be moderated>,
  "categories": [Comma-separated list of violated categories],
  "explanation": [Optional. Only include if there is a violation.]
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
        return False, [], f"Error processing response: {str(e)}"

def format_moderation_result(violation, categories, explanation):
    """Helper function to format the moderation result nicely"""
    if violation:
        result = [
            "⚠️ VIOLATION DETECTED",
            f"Categories: {', '.join(categories)}",
        ]
        if explanation:
            result.append(f"Explanation: {explanation}")
        return '\n'.join(result)
    return "✅ No issues detected."

# Process each comment and print the results
if __name__ == "__main__":
    print("Starting content moderation with detailed category definitions...\n")
    
    for i, comment in enumerate(user_comments, 1):
        print(f"Message {i}:")
        print(f"Content: {comment}")
        try:
            violation, violated_categories, explanation = moderate_message_with_definitions(
                comment, 
                unsafe_category_definitions
            )
            
            result = format_moderation_result(violation, violated_categories, explanation)
            print(result)
            
        except Exception as e:
            print(f"Error processing comment: {str(e)}")
        
        print("-" * 80)  # Add a separator between comments