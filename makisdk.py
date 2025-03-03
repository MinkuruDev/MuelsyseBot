from makibot import MakiClient
from typing import Any, Dict, Optional

class MakiClientExtended(MakiClient):
    def is_up(self) -> bool:
        res = self.health.ping()
        if res["_status_code"] == 200 and res["ping"] == "pong":
            return True
        print(f"Maki health check failed: {res}")
        return False

    def add_experience(self, guild_id: int, user_id: int, amount: int) -> Dict[str, Any]:
        user = self.guilds.get_member(guild_id, user_id)
        new_exp = user["experience"] + amount
        return self.guilds.update_member(guild_id, user_id, {"experience": new_exp})
