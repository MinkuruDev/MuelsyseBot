import requests
from typing import Any, Dict, Optional

class MakiClient:
    """
    Main client for interacting with the Maki API.
    
    Args:
        base_url (str): The base URL for the Maki API (e.g. "https://api.maki.gg").
        api_key (Optional[str]): Your API key. It will be included in the Authorization header.
            For guild-specific tokens, use the format: "Guild YOUR_GUILD_API_TOKEN"
            For user tokens (OAuth2-based), use: "Bearer YOUR_USER_API_KEY"
    """
    def __init__(self, base_url: str = "https://api.maki.gg", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        if api_key:
            self.session.headers.update({"Authorization": api_key})

        # Initialize sub-clients
        self.health = HealthClient(self)
        self.auth = AuthClient(self)
        self.guilds = GuildsClient(self)
        self.users = UsersClient(self)
        self.commands = CommandsClient(self)
        self.tutorials = TutorialsClient(self)

    def request(self, method: str, path: str, **kwargs) -> Any:
        """Helper method for sending HTTP requests to the API."""
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, **kwargs)
        result = response.json()
        result["_status_code"] = response.status_code
        return result


# Health endpoints
class HealthClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def ping(self) -> Dict[str, Any]:
        """Check if the API is up and running."""
        return self.client.request("GET", "/health/")

    def get_stats(self) -> Dict[str, Any]:
        """Get application-wide stats."""
        return self.client.request("GET", "/health/stats")

    def get_clusters(self) -> Any:
        """Fetch all cluster health statuses."""
        return self.client.request("GET", "/health/clusters")

    def get_guild_status(self, guild_id: int) -> Dict[str, Any]:
        """Get the status information for a specific guild."""
        path = f"/health/guilds/{guild_id}"
        return self.client.request("GET", path)


# Authentication endpoints
class AuthClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def login(self) -> Dict[str, Any]:
        """Get the Discord OAuth login URL."""
        return self.client.request("GET", "/oauth/login")

    def callback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the Discord OAuth callback.
        
        Args:
            params (dict): Query parameters from the callback (e.g. code, state).
        """
        return self.client.request("GET", "/oauth/callback", params=params)

    def logout(self) -> Dict[str, Any]:
        """Log out the user and remove their session token."""
        return self.client.request("GET", "/oauth/logout")


# Guilds endpoints
class GuildsClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def get_featured(self, amount: int = 20) -> Any:
        """Get a list of featured guilds."""
        params = {"amount": amount}
        return self.client.request("GET", "/guilds/featured", params=params)

    def get_guild(self, guild_id: int) -> Dict[str, Any]:
        """Get a guild and its relevant data."""
        path = f"/guilds/{guild_id}"
        return self.client.request("GET", path)

    def get_modules(self, guild_id: int) -> Dict[str, Any]:
        """Get the modules of a guild."""
        path = f"/guilds/{guild_id}/modules"
        return self.client.request("GET", path)

    def update_modules(self, guild_id: int, modules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the modules of a guild.
        
        Args:
            guild_id (int): The guild ID.
            modules (dict): A dictionary following the PatchGuildsModules schema.
        """
        path = f"/guilds/{guild_id}/modules"
        return self.client.request("PATCH", path, json=modules)

    def generate_guild_token(self, guild_id: int) -> Dict[str, Any]:
        """
        Generate a new API token for a guild.
        The generated token is sensitive – keep it secure!
        """
        path = f"/guilds/{guild_id}/token"
        return self.client.request("POST", path)

    def get_member(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Get a guild member's profile information."""
        path = f"/guilds/{guild_id}/members/{user_id}"
        return self.client.request("GET", path)

    def update_member(self, guild_id: int, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a guild member's data.
        
        Args:
            guild_id (int): The guild ID.
            user_id (int): The member's user ID.
            data (dict): The data to update (e.g., level, experience).
        """
        path = f"/guilds/{guild_id}/members/{user_id}"
        return self.client.request("PATCH", path, json=data)

    def get_member_moderations(self, guild_id: int, user_id: int) -> Any:
        """Get the last 50 moderation actions taken on a guild member."""
        path = f"/guilds/{guild_id}/members/{user_id}/moderations"
        return self.client.request("GET", path)

    def get_leaderboards(self, guild_id: int, lb_type: str, page: int = 1) -> Any:
        """
        Get the leaderboard for a specific guild.
        
        Args:
            guild_id (int): The guild ID.
            lb_type (str): The leaderboard type, one of ["level", "balance", "streak", "reputation", "time"].
            page (int): The page number.
        """
        path = f"/guilds/{guild_id}/leaderboards"
        params = {"type": lb_type, "page": page}
        return self.client.request("GET", path, params=params)

    # Additional methods for other guild modules (birthdays, economy, levels, music, roleplay,
    # starboard, suggestions, temporary_channels, vanity, welcome) can be implemented similarly.
    def get_birthdays(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/birthdays"
        return self.client.request("GET", path)

    def update_birthdays(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/birthdays"
        return self.client.request("PATCH", path, json=data)

    def get_economy(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/economy"
        return self.client.request("GET", path)

    def update_economy(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/economy"
        return self.client.request("PATCH", path, json=data)

    def get_levels(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/levels"
        return self.client.request("GET", path)

    def update_levels(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/levels"
        return self.client.request("PATCH", path, json=data)

    def get_music(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/music"
        return self.client.request("GET", path)

    def update_music(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/music"
        return self.client.request("PATCH", path, json=data)

    def get_roleplay(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/roleplay"
        return self.client.request("GET", path)

    def update_roleplay(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/roleplay"
        return self.client.request("PATCH", path, json=data)

    def get_starboard(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/starboard"
        return self.client.request("GET", path)

    def update_starboard(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/starboard"
        return self.client.request("PATCH", path, json=data)

    def get_suggestions(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/suggestions"
        return self.client.request("GET", path)

    def update_suggestions(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/suggestions"
        return self.client.request("PATCH", path, json=data)

    def get_temporary_channels(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/temporary_channels"
        return self.client.request("GET", path)

    def update_temporary_channels(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/temporary_channels"
        return self.client.request("PATCH", path, json=data)

    def get_vanity(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/vanity"
        return self.client.request("GET", path)

    def update_vanity(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/vanity"
        return self.client.request("PATCH", path, json=data)

    def get_welcome(self, guild_id: int) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/welcome"
        return self.client.request("GET", path)

    def update_welcome(self, guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/guilds/{guild_id}/welcome"
        return self.client.request("PATCH", path, json=data)


# Users endpoints
class UsersClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get a user by ID."""
        path = f"/users/{user_id}"
        return self.client.request("GET", path)

    def get_my_guilds(self) -> Any:
        """Get the guilds for the current user."""
        return self.client.request("GET", "/users/@me/guilds")


# Commands endpoints
class CommandsClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def get_commands(self) -> Any:
        """Get the list of global application commands."""
        return self.client.request("GET", "/commands")


# Tutorials endpoints
class TutorialsClient:
    def __init__(self, client: MakiClient):
        self.client = client

    def get_tutorials_list(self) -> Any:
        """Get the list of tutorials."""
        return self.client.request("GET", "/tutorials")

    def create_tutorial(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tutorial.
        
        Args:
            data (dict): Tutorial data following the PostTutorial schema.
        """
        return self.client.request("POST", "/tutorials", json=data)

    def get_tutorial(self, slug: str) -> Dict[str, Any]:
        """Get a specific tutorial by its slug."""
        path = f"/tutorials/{slug}"
        return self.client.request("GET", path)

    def update_tutorial(self, slug: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing tutorial.
        
        Args:
            slug (str): The tutorial slug.
            data (dict): The fields to update.
        """
        path = f"/tutorials/{slug}"
        return self.client.request("PATCH", path, json=data)

    def delete_tutorial(self, slug: str) -> Dict[str, Any]:
        """Delete an existing tutorial."""
        path = f"/tutorials/{slug}"
        return self.client.request("DELETE", path)


# Example usage:
if __name__ == "__main__":
    # Replace with your actual API base URL and API key
    BASE_URL = "https://api.maki.gg"
    API_KEY = "Bearer YOUR_USER_API_KEY"

    client = MakiClient(base_url=BASE_URL, api_key=API_KEY)
    
    try:
        # Check API health
        ping_response = client.health.ping()
        print("Ping:", ping_response)
        
        # Get application stats
        stats = client.health.get_stats()
        print("Stats:", stats)
        
        # Fetch featured guilds
        featured_guilds = client.guilds.get_featured()
        print("Featured Guilds:", featured_guilds)
        
        # Fetch tutorials list
        tutorials = client.tutorials.get_tutorials_list()
        print("Tutorials:", tutorials)
    except requests.HTTPError as e:
        print("An error occurred:", e)
