"""
Image fetching module for news articles.

Integrates with Unsplash API to fetch fallback images for news articles
that don't have their own images, following Unsplash API Guidelines:
https://help.unsplash.com/en/articles/2511245-unsplash-api-guidelines
"""

import logging
import requests
from typing import Optional, Dict
from .config import config

logger = logging.getLogger(__name__)


class ImageFetcher:
    """
    Fetches fallback images from Unsplash API for news articles.

    Complies with Unsplash API Guidelines:
    1. Hotlinks photos to original Unsplash URLs
    2. Triggers download events when photos are used
    3. Provides photographer attribution data
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ImageFetcher.

        Args:
            api_key: Unsplash Access Key. If None, uses config value.
        """
        self.api_key = api_key or config.UNSPLASH_ACCESS_KEY
        self.endpoint = config.UNSPLASH_API_ENDPOINT
        self.timeout = config.API_TIMEOUT

    def get_fallback_image(self, company_name: str) -> Optional[Dict[str, str]]:
        """
        Get a random fallback image from Unsplash related to the company.

        This method:
        1. Searches Unsplash for photos related to the company name
        2. Returns a random photo from results
        3. Includes photographer attribution data (required by Unsplash)

        Args:
            company_name: Name of the company to search for

        Returns:
            Dictionary with image data:
            {
                'image_url': str,           # Direct hotlink to Unsplash image (regular size)
                'photographer_name': str,   # Photographer's name
                'photographer_username': str, # Photographer's Unsplash username
                'photographer_url': str,    # Link to photographer's Unsplash profile
                'download_location': str    # Endpoint to trigger download event
            }
            Returns None if no image found or API error.
        """
        if not self.api_key:
            logger.warning("Unsplash API key not configured, skipping image fetch")
            return None

        logger.debug(f"Fetching fallback image for {company_name}")

        # Search for photos related to company
        # Use query="{company_name} finance stock business" for better results
        search_params = {
            "query": f"{company_name} finance business",
            "per_page": 1,
            "orientation": "landscape",
            "content_filter": "high"  # Family-friendly content only
        }

        headers = {
            "Authorization": f"Client-ID {self.api_key}",
            "Accept-Version": "v1"
        }

        try:
            # Search for photos
            search_url = f"{self.endpoint}/search/photos"
            response = requests.get(
                search_url,
                params=search_params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            search_data = response.json()

            # Check if we got results
            results = search_data.get("results", [])
            if not results:
                logger.warning(f"No Unsplash images found for {company_name}")
                return None

            # Get first photo
            photo = results[0]

            # Extract required attribution data
            image_data = {
                # Hotlink to original Unsplash image (regular size ~1080px)
                "image_url": photo["urls"]["regular"],

                # Photographer attribution (required by Unsplash)
                "photographer_name": photo["user"]["name"],
                "photographer_username": photo["user"]["username"],
                "photographer_url": photo["user"]["links"]["html"],

                # Download endpoint (to trigger download event)
                "download_location": photo["links"]["download_location"]
            }

            logger.info(
                f"Found Unsplash image for {company_name} by "
                f"{image_data['photographer_name']}"
            )

            return image_data

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching Unsplash image for {company_name}: {str(e)}",
                exc_info=True
            )
            return None
        except (KeyError, IndexError) as e:
            logger.error(
                f"Error parsing Unsplash response for {company_name}: {str(e)}",
                exc_info=True
            )
            return None

    def trigger_download(self, download_location: str) -> bool:
        """
        Trigger Unsplash download event.

        Required by Unsplash API Guidelines:
        "When a user in your application uses a photo, it triggers an event
        to the download endpoint."

        This must be called when:
        - A photo is displayed to users
        - A photo is saved/used in the application

        Args:
            download_location: The download_location URL from get_fallback_image()

        Returns:
            True if download event was triggered successfully, False otherwise.
        """
        if not self.api_key or not download_location:
            return False

        headers = {
            "Authorization": f"Client-ID {self.api_key}",
            "Accept-Version": "v1"
        }

        try:
            response = requests.get(
                download_location,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.debug(f"Triggered Unsplash download event")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error triggering Unsplash download event: {str(e)}",
                exc_info=True
            )
            return False
