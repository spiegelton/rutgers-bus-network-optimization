import os
import json

input_dir = 'route_geojson'
output_dir = 'route_raw_polylines'

os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if not filename.endswith('.geojson'):
        continue

    route_name = filename.replace('.geojson', '')
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, f'{route_name}.json')

    with open(input_path, 'r') as f:
        geojson_data = json.load(f)

    try:
        coordinates = geojson_data['features'][0]['geometry']['coordinates']
    except (IndexError, KeyError):
        print(f"Could not read coordinates for {filename}")
        continue

    # Write as plain list of [lat, lon] pairs (reversed from [lon, lat])
    latlon_coords = [[lat, lon] for lon, lat in coordinates]

    with open(output_path, 'w') as f_out:
        json.dump(latlon_coords, f_out)

    print(f"Saved {route_name} to {output_path}")