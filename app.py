import streamlit as st
import os
from dotenv import load_dotenv
import anthropic
import json
import time

# Load environment variables
load_dotenv()

# Initialize the Anthropic client
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
    
    # Construct the prompt for Claude
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
        # Send the request to Claude using the latest API
        message = client.beta.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": assessment_prompt}
            ]
        )
        
        # Parse the JSON response
        response_text = message.content[0].text
        assessment = json.loads(response_text)
        
        # Extract the results
        contains_violation = assessment.get('violation', False)
        violated_categories = assessment.get('categories', []) if contains_violation else []
        explanation = assessment.get('explanation') if contains_violation else None
        
        return contains_violation, violated_categories, explanation
        
    except Exception as e:
        st.error(f"Error processing message: {str(e)}")
        print(f"Detailed error: {str(e)}")  # Added for debugging
        return False, [], str(e)

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Content Moderation System",
        page_icon="🛡️",
        layout="wide"
    )
    
    # Main title and description
    st.title("🛡️ Content Moderation System")
    st.markdown("""
    This system analyzes text content for potential violations across various safety categories.
    Enter your text below to check if it contains any concerning content.
    """)
    
    # Create two columns for the layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Text input area
        user_input = st.text_area(
            "Enter text to analyze:",
            height=150,
            placeholder="Type or paste content here..."
        )
        
        # Analysis button
        if st.button("Analyze Content", type="primary"):
            if not user_input:
                st.warning("Please enter some text to analyze.")
            else:
                # Show spinner while processing
                with st.spinner("Analyzing content..."):
                    violation, categories, explanation = moderate_message_with_definitions(
                        user_input, unsafe_category_definitions
                    )
                
                # Display results in an expander
                with st.expander("Analysis Results", expanded=True):
                    if violation:
                        st.error("⚠️ Content Violation Detected")
                        st.write("**Violated Categories:**")
                        for category in categories:
                            st.markdown(f"- {category}")
                        if explanation:
                            st.write("**Explanation:**")
                            st.info(explanation)
                    else:
                        st.success("✅ No content violations detected")
    
    with col2:
        # Show category definitions in an expander
        with st.expander("Content Safety Categories"):
            for category, definition in unsafe_category_definitions.items():
                st.markdown(f"**{category}**")
                st.write(definition)
                st.divider()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Content Moderation System powered by Claude AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()