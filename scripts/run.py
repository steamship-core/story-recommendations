WORKSPACE_HANDLE = "wa-storyrec-6"
INSTANCE_HANDLE = "wa-storyrec-6"
VERSION_HANDLE = "1.0.5"
STORY_DATA = "./scripts/wa.csv"

import csv
from steamship import Steamship
import re
from tqdm import tqdm

if __name__ == "__main__":
  pkg = Steamship.use(
    package_handle="story-recommendations",
    instance_handle=INSTANCE_HANDLE,
    workspace_handle=WORKSPACE_HANDLE,
    version=VERSION_HANDLE,
    profile="wa",
  )

  print("Ask")
  resp = pkg.invoke("suggest_story", query="A person travels Goa expecting the beach, but finds a war with Portugal")
  print(resp)
  