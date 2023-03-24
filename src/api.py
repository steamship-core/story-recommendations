"""Description of your app."""
from enum import Enum
from typing import Optional, List, Dict, Any
from steamship import Steamship
from steamship.invocable import post, PackageService, InvocationContext

from pydantic import BaseModel

class Style(str, Enum):
     painting = "painting"
     neon = "neon"
     magazine = "magazine"


class Output(BaseModel):
    image_urls: Optional[List[str]]
    text: Optional[str]


class SteamshipPackage(PackageService):
    def __init__(
        self,
        client: Steamship = None,
        config: Dict[str, Any] = None,
        context: InvocationContext = None,
    ):
        super().__init__(client, config, context)

    @post("generate")
    def generate(
        self,
        title: str = "A Story", 
        description: str = "Story Description",
        style: Style = Style.painting
    ) -> dict:

        # CODE THAT DOES THINGS HERE :)

        output = Output(
            text="This is text!",
            image_urls=[
                "https://media.istockphoto.com/id/1157515115/photo/cheeseburger-isolated-on-white.jpg?s=612x612&w=0&k=20&c=6f6jnWe3iGi2GinEvSJlDsqKbaYoRwj3vYChPCU96U4="
            ]   
        )

        return output
