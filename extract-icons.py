# open the page https://birdsoftheworld.org/bow/species and look for the icons

import os
import requests
import json

response = requests.get("https://birdsoftheworld.org/bow/api/v1/taxonomy?depth=20&categoriesForCounts=species&showIucnStatusCounts=false&locale=en")
data = response.json()

# traverse the object on subTaxa and for each element with a illusAssetId property create an entry with taxonCode and illusAssetId
icons = {}
def traverse(taxa):
    if "illusAssetId" in taxa:
        icons[taxa["taxonCode"]] = taxa["illusAssetId"]
    if "subTaxa" in taxa:
        for sub in taxa["subTaxa"]:
            traverse(sub)
            
traverse(data)
    
# save the icons to a json file
with open("icons.json", "w") as f:
    json.dump(icons, f, indent=4)