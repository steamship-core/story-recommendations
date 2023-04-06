WORKSPACE_HANDLE = "wa-storyrec-6"
INSTANCE_HANDLE = "wa-storyrec-6"
VERSION_HANDLE = "1.0.5"
STORY_DATA = "./scripts/wa.csv"

import csv
from steamship import Steamship
import re
from tqdm import tqdm

def chunker(seq, size):
  return (seq[pos:pos + size] for pos in range(0, len(seq), size))


if __name__ == "__main__":
  pkg = Steamship.use(
    package_handle="story-recommendations",
    instance_handle=INSTANCE_HANDLE,
    workspace_handle=WORKSPACE_HANDLE,
    version=VERSION_HANDLE,
    profile="wa",
  )

  # Author—Story Title,Short Story Title,Author,Genre,Original or Main Publication,"Anthology/Collection, Main Original Editors",Word Count,Logline (Short Summary),Logline_Situation,Logline_Who,Logline_Action,Logline_Goal,Logline_Consequence,Summary,Tags Manual,Read if You Like,Adaptation Notes (Movie and Audio),Reader Notes,Learn More URL,Author Literary Agency,Wikipedia URL,Curation Source,Tags Linked,Publication Year (Estimate),Short Commercial Description,Alternative and Old Loglines,Honor Level and Year (Formula),Notes for Cover Image,Cover Images,General Notes,Honor Level and Year (Aggregated),Recommender Notes,Publication Date,Setting,Characters

  with open(STORY_DATA, 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    tags = []

    for row in csv_reader:
      title = row.get("Short Story Title", None)
      logline = row.get("Logline (Short Summary)", None)
      author = row.get("Author", None)
      slug_au = author.lower().replace(" ", "-")
      slug_au = re.sub(r'[^a-zA-Z0-9]', '-', slug_au)
      slug_ti = title.lower().replace(" ", "-")
      slug_ti = re.sub(r'[^a-zA-Z0-9]', '-', slug_ti)
      slug = f"{slug_au}--{slug_ti}"

      if title and logline:
        tag = {
          "text": logline,
          "value": {
            "author": author,
            "title": title,
            "slug": slug          
          }
        }
        tags.append(tag)

    for items in tqdm(chunker(tags, 10)):
      pkg.invoke("insert", items=items)

