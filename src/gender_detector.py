"""Gender detection using LLM for person entity queries."""

import json
import requests
from typing import Optional, Literal
from src.config import Config


class GenderDetector:
    """Detects likely gender of person queries using LLM."""

    def __init__(self):
        """Initialize the gender detector."""
        self.api_key = Config.ZEUS_LLM_API_KEY
        self.endpoint = Config.ZEUS_LLM_ENDPOINT
        self.pipeline_id = Config.ZEUS_LLM_PIPELINE_ID
        self.temperature = Config.ZEUS_LLM_TEMPERATURE
        self.enabled = Config.ENABLE_GENDER_FILTERING and self.api_key is not None

    def detect_gender(self, query: str) -> Optional[Literal['male', 'female']]:
        """
        Detect the likely gender of a person from their name/query.

        Args:
            query: The person's name or query string

        Returns:
            'male', 'female', or None if detection is disabled or fails
        """
        if not self.enabled:
            print("[Gender Detection] Gender filtering is disabled or API key not configured")
            return None

        print(f"[Gender Detection] Detecting gender for query: '{query}'")

        try:
            # Prepare the LLM request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            prompt = (
                f"Is the person named '{query}' likely male or female? "
                f"Respond with ONLY one word: 'male' or 'female'. "
                f"If uncertain, make your best guess based on the name."
            )

            data = {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'pipeline_id': self.pipeline_id,
                'temperature': self.temperature
            }

            # Call the LLM API
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=data,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # Parse the response
            result = response.json()
            llm_response = result['choices'][0]['message']['content'].lower().strip()

            print(f"[Gender Detection] LLM response: '{llm_response}'")

            # Extract gender from response
            if 'male' in llm_response and 'female' not in llm_response:
                gender = 'male'
            elif 'female' in llm_response:
                gender = 'female'
            else:
                print(f"[Gender Detection] Could not determine gender from response: '{llm_response}'")
                return None

            print(f"[Gender Detection] Detected gender: {gender}")
            return gender

        except requests.exceptions.Timeout:
            print(f"[Gender Detection] ✗ LLM API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[Gender Detection] ✗ LLM API request failed: {e}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"[Gender Detection] ✗ Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            print(f"[Gender Detection] ✗ Unexpected error: {e}")
            return None
