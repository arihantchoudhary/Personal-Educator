import os
from dotenv import load_dotenv
from openai import OpenAI
import base64
from pathlib import Path

# Load environment variables from the .env file
load_dotenv()

class GPT:
    def __init__(self, api_key=None, system_prompt=None, model="gpt-4", temperature=0.7, max_tokens=1000):
        """
        Initialize the GPT class with OpenAI client.

        Args:
            api_key (str): Your OpenAI API key
            system_prompt (str): The system prompt for context
            model (str): Model to use (default: gpt-4)
            temperature (float): Controls randomness (0.0-1.0)
            max_tokens (int): Maximum tokens to generate
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is not set in environment variables or provided as a parameter.")

        self.client = OpenAI(api_key=self.api_key)
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_response(self, user_prompt):
        """
        Generate a response using the OpenAI API.

        Args:
            user_prompt (str): The user's input prompt

        Returns:
            str: The generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Extract response text
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            print("Response:")
            print(response_text)
            print(f"Tokens used: {tokens_used}")

            return response_text

        except Exception as e:
            print(f"Error while calling API: {e}")
            return None

class Gemini:
    def __init__(self, api_key=None, site_url=None, site_name=None):
        """
        Initialize the Gemini class with OpenRouter client.

        Args:
            api_key (str): Your OpenRouter API key
            site_url (str): Your site URL for rankings on openrouter.ai
            site_name (str): Your site name for rankings on openrouter.ai
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is not set in environment variables or provided as a parameter.")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        self.site_url = site_url
        self.site_name = site_name

    def generate_response(self, text_prompt, image_url=None):
        """
        Generate a response using the Gemini model via OpenRouter API.

        Args:
            text_prompt (str): The text prompt to send
            image_url (str, optional): URL or local path of an image/PDF to analyze

        Returns:
            str: The generated response text
        """
        try:
            messages = [{
                "role": "user",
                "content": []
            }]

            # Add text content
            messages[0]["content"].append({
                "type": "text",
                "text": text_prompt
            })

            # Add image/PDF content if provided
            if image_url:
                # Handle local files
                if image_url.startswith('file://'):
                    file_path = image_url[7:]  # Remove 'file://' prefix
                    if not os.path.exists(file_path):
                        raise ValueError(f"File not found: {file_path}")
                    
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        
                        # Determine MIME type based on file extension
                        mime_type = 'application/pdf' if file_path.lower().endswith('.pdf') else 'image/jpeg'
                        data_url = f"data:{mime_type};base64,{base64_content}"
                        
                        messages[0]["content"].append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        })
                else:
                    # Handle web URLs
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    })

            # Prepare headers
            extra_headers = {}
            if self.site_url:
                extra_headers["HTTP-Referer"] = self.site_url
            if self.site_name:
                extra_headers["X-Title"] = self.site_name

            completion = self.client.chat.completions.create(
                extra_headers=extra_headers,
                extra_body={},
                model="google/gemini-2.0-flash-001",
                messages=messages
            )

            return completion.choices[0].message.content

        except Exception as e:
            print(f"Error while calling API: {e}")
            return None

if __name__ == "__main__":
    gem = Gemini()  # It will automatically use OPENROUTER_API_KEY from .env
    prompt = "Please analyze this PDF about LLM reasoning. What are the main points and key takeaways?"
    response = gem.generate_response(text_prompt=prompt, image_url="file:///Users/arihantchoudhary/GitHub/Personal-Educator/slides/llm-reasoning.pdf")
    print(response)
