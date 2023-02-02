import json
import os
import pandas as pd
from pystac_client import Client

out_dir = "catalogs"

url = "https://stac.maap-project.org/"

root = Client.open(url, headers=[])

collections = root.get_all_collections()

output_collections = []

for collection in collections:
    try:
        data = collection.to_dict()
        print(data["id"])
        collection_obj = {}
        output = out_dir + "/" + data["id"].replace("/", "_") + ".json"
        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        collection_obj["id"] = data["id"].strip()

        collection_obj["title"] = data["title"].strip()

        start_date = data["extent"]["temporal"]["interval"][0][0]
        end_date = data["extent"]["temporal"]["interval"][0][1]

        if start_date is not None:
            collection_obj["start_date"] = start_date.split("T")[0]
        else:
            collection_obj["start_date"] = ""

        if end_date is not None:
            collection_obj["end_date"] = end_date.split("T")[0]
        else:
            collection_obj["end_date"] = ""
        collection_obj["bbox"] = ", ".join(
            [str(coord) for coord in data["extent"]["spatial"]["bbox"][0]]
        )

        # url = ""
        metadata = ""
        href = ""

        for l in data["links"]:
            if l["rel"] == "about":
                metadata = l["href"]
            if l["rel"] == "self":
                href = l["href"]
            # if l["rel"] == "via":
            #     url = l["href"]

        # collection_obj["url"] = url
        collection_obj["metadata"] = metadata
        collection_obj["href"] = href

        collection_obj["description"] = (
            data["description"]
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\\u", " ")
            .replace("                 ", " ")
        )

        collection_obj["license"] = data["license"]

        output_collections.append(collection_obj)
    except Exception as e:
        print("Error: ", collection)
        print(e)

print("Total collections: ", len(output_collections))

print()
df = pd.DataFrame(output_collections)
df.sort_values(by=["id"], inplace=True)
df.drop(columns=["metadata"]).to_csv(
    "nasa_maap_stac.tsv", index=False, sep="\t"
)

with open("nasa_maap_stac.json", "w") as f:
    json.dump(df.to_dict("records"), f, indent=4)
