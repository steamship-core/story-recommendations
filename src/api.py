import inspect
from termcolor import colored
from typing import Union, List
from steamship import check_environment, RuntimeEnvironments, Steamship, Tag
from steamship.invocable import post, PackageService

PROMPT_LOCATION = """
Your goal is to extract information from the user's input that matches the form described below. Extract an Output with <location> for each Input.
  
<location>: Generate the location in the world of the following input. Only repond with the city and country.

Input:
Ruriko visits robot versions of her former bandmates, who are kept in a sex hotel. Through talking with them, she revisits the day all of them died, leaving her the sole survivor. 
Output:
Tokyo, Japan

Input:
After a disaster wipes out most of the food supply, a young woman struggles to find hope and love in her new basecamp.
Output:
Kraków, Poland

Input:
A TV critic begins to have trouble telling the difference between her own, real life, and the lives of the characters on television.
Output:
London, United Kingdom

Input:
{story}
Output:
"""

PROMPT_AUDIENCE = """
Your goal is to extract information from the user's input that matches the form described below. Extract an Output with <audience> for each Input.
  
<audience>: Extract the target audience of the following input. Only repond with the group of people that could be interested in this input

Input:
Ruriko visits robot versions of her former bandmates, who are kept in a sex hotel. Through talking with them, she revisits the day all of them died, leaving her the sole survivor. 
Output:
Fans of science fiction

Input:
After a disaster wipes out most of the food supply, a young woman struggles to find hope and love in her new basecamp.
Output:
Young adults, people interested in stories of resilience and hope

Input:
A TV critic begins to have trouble telling the difference between her own, real life, and the lives of the characters on television.
Output:
TV viewers, people interested in media and pop culture

Input:
{story}
Output:
"""

PROMPT_TOPIC = """
Your goal is to extract information from the user's input that matches the form described below. Extract an Output with <topic> for each Input.
  
<topic>: Generate the the main topics of the following input. Only repond with two

Input:
Ruriko visits robot versions of her former bandmates, who are kept in a sex hotel. Through talking with them, she revisits the day all of them died, leaving her the sole survivor. 
Output:
Death and Technology

Input:
After a disaster wipes out most of the food supply, a young woman struggles to find hope and love in her new basecamp.
Output:
Survival and Romance

Input:
A TV critic begins to have trouble telling the difference between her own, real life, and the lives of the characters on television.
Output:
Television and Reality

Input:
{story}
Output:
"""

PROMPT_EXPLANATION = """
You are writing a one-sentence recommendation for why a reader might like a story. Be consice and don't repeat terms.

Input:
- The story takes place in New York City, USA.
- The audience for the story is fans of crime and suspense
- The story is about love and nature

Output:
This thrilling story about love and nature set in the heart of New York City will appeal to fans of crime and suspense.

Input:
- The story takes place in Tokyo, Japan
- The audience for the story is people interested in stories about science-fiction
- The story is about robots and death

Output: 
This thrilling tale about robots and death set in the bustling city of Tokyo will appeal to readers interested in science-fiction.

Input:
- The story takes place in Westport, Ireland.
- The audience for the story is children, people interested in magical realism
- The story is about mystery and wonder.

Why might the reader like this book?

Output:
This enchanting story of mystery and wonder in Westport, Ireland will appeal to children and those interested in magical realism.

Input:
- The story takes place in {location}
- The audience for the story is {audience}
- The story is about {topic}

Output:
"""


class EmbeddingSearchPackage(PackageService):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # This will create a persistent vector index named "my-embedding-index"
    # Using the "openai-embedder" plugin for embeddings.
    self.index = self.client.use_plugin(
      "embedding-index",
      "my-embedding-index",
      config={
        "embedder": {
          "plugin_handle": "openai-embedder",
          "fetch_if_exists": True,
          "config": {
            "model": "text-embedding-ada-002",
            "dimensionality": 1536,
          }
        }
      },
      fetch_if_exists=True,
    )
    llm_config = {
    # Controls randomness of output (range: 0.0-1.0).
      "temperature": 0.8,
    }

    self.llm = self.client.use_plugin("gpt-4", config=llm_config)
  
  # When you run `ship deploy`, this annotation tells Steamship
  # to create an API endpoint called `/insert` request path.
  # See README.md for more information about deployment.
  @post("insert")
  def insert(self, items: Union[Tag, List[Tag]]) -> bool:
    # The insert command can accept either a Tag or a list of Tags.
    # Passing in JSON or a dict over HTTP is fine since we'll parse it below.
    # Tag has shape {kind: str, name: str, text: str, value: dict}
    # The `text` of the tag is what will be embedded.
    if type(items) != list:
      items = [items]
    items = [Tag.parse_obj(item) for item in items]
    self.index.insert(items)
    return True

  # When you run `ship deploy`, this annotation tells Steamship
  # to create an API endpoint called `/query` request path.
  # See README.md for more information about deployment.
  @post("search")
  def search(self, query: str = "", k: int = 3) -> List[Tag]:
    """Return the `k` closest items in the embedding index."""
    search_results = self.index.search(query, k=k)
    search_results.wait()
    items = search_results.output.items
    return items
  
  @post("suggest_story")
  def suggest_story(self, query: str = "", k: int = 3) -> List[dict]:
    """Return the `k` closest items in the embedding index."""
    search_results = self.index.search(query, k=k)
    search_results.wait()
    items = search_results.output.items

    for item in items:
      location_promt = PROMPT_LOCATION.format(**{"story": item.tag.text})
      location = self.llm.generate(text=location_promt)

      audience_promt = PROMPT_AUDIENCE.format(**{"story": item.tag.text})
      audience = self.llm.generate(text=audience_promt)

      topic_promt = PROMPT_TOPIC.format(**{"story": item.tag.text})
      topic = self.llm.generate(text=topic_promt)

      location.wait()
      audience.wait()
      topic.wait()

      item.tag.value["topic"] = topic.output.blocks[0].text
      item.tag.value["audience"] = audience.output.blocks[0].text
      item.tag.value["location"] = location.output.blocks[0].text

      explanation_promt = PROMPT_EXPLANATION.format(**{"location": item.tag.text, "audience": item.tag.text, "topic": item.tag.text})
      explanation = self.llm.generate(text=explanation_promt)
      explanation.wait()
      item.tag.value["explanation"] = explanation.output.blocks[0].text
    return items


# Try it out locally by running this file!
if __name__ == "__main__":
  print(
    colored("Embedding Search API with OpenAI Embeddings\n", attrs=['bold']))

  # This helper provides runtime API key prompting, etc.
  check_environment(RuntimeEnvironments.REPLIT)

  # This `main` method will delete of its cloud data (including saved items) after completing.
  with Steamship.temporary_workspace() as client:
    api = EmbeddingSearchPackage(client)

    NZ = {
      "text":
      "New Zealand's South Island brims with majestic landscapes at every turn, from dramatic mountains to spectacular fjords. Here, you can admire the mountains of Fiordland National Park, a UNESCO World Heritage Site, from hiking trails or a boat on Milford Sound.",
      "value": {
        "place": "South Island, New Zealand"
      }
    }

    FR = {
      "text":
      "The magnetic City of Light draws visitors from around the globe who come to see iconic attractions like the Eiffel Tower, the Louvre and the Arc de Triomphe. But what travelers really fall in love with are the city's quaint cafes, vibrant markets, trendy shopping districts and unmistakable je ne sais quoi",
      "value": {
        "place": "Paris, France"
      }
    }

    ITEMS = [NZ, FR]

    print(colored("First, let's embed and index some items...", 'green'))
    for item in ITEMS:
      print(f"- {item['value']['place']}")
      api.insert(item)

    print(colored("Now, let's try searching it...", 'green'))

    try_again = True
    while try_again:
      kwargs = {"k": 1}
      kwargs["query"] = input(colored('QUERY: ', 'grey'))

      print(colored("Searching...", 'grey'))
      results = api.suggest_story(**kwargs)

      for result in results:
        # score = result.score
        # tag = result.tag
        # print(colored("Place:", 'grey'), f"{tag.value['place']} - {score}\n")
        print(result)
        try_again = input(colored("Search again (y/n)? ",
                                'green')).lower().strip() == 'y'
        print()