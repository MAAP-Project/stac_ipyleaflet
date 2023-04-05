#!git clone git@github.com:maap-project/biomass-dashboard-datasets
import csv
import json
import os

def write_biomass_layers():
    data_dir = 'biomass-dashboard-datasets/datasets/'
    files = os.listdir(data_dir)

    with open('biomass-layers.csv', 'w', newline='') as csv_file:
        fieldnames = ['Layer Name', 'Tiles URL']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for filename in files:
            with open(f"{data_dir}{filename}", 'r') as file_obj:
                data = json.loads(file_obj.read())
                if data['source'].get('tiles'):
                    tile_url = data['source']['tiles'][0]
                    tile_url = tile_url.replace('&color_formula=gamma r {gamma}', '')
                    tile_url = tile_url.replace('{titiler_server_url}', 'https://titiler.maap-project.org')
                file_obj.close()
            writer.writerow({
                fieldnames[0]: data['id'].capitalize().replace('_', ' '), 
                fieldnames[1]: tile_url})
        csv_file.close()

if __name__ == '__main__':
    write_biomass_layers()

