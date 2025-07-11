import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import csv
import math
import itertools

MMFL_OUTPUT = '../mm_fixtures/commune_table.mmfl'
PIXEL_ROW_MARGIN = 0
PIXEL_COLUMN_MARGIN = 0

def read_csv_to_dict(filename):
    data_dict = {}

    def coerce_to_number(value):
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value if value else None
    
    with open(filename, mode='r') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            line_number = row["Line Number"]
            # Remove the "Line Number" key and convert empty strings to None
            row_data = {key: coerce_to_number(value) for key, value in row.items() if key != "Line Number"}
            data_dict[int(line_number)] = row_data
    
    return data_dict

def export_to_csv(data, filename="output.csv"):
    """
    Exports a list of lists of numbers to a CSV file with numbered headers.
    
    Parameters:
        data (list of lists): A list containing sublists of numbers.
        filename (str): The name of the CSV file to be created.
    """
    if not data:
        print("The data list is empty. No file will be created.")
        return
    
    # Determine the maximum row length for header numbering
    max_columns = max(len(row) for row in data)

    # Create the headers: First column is "Line#", followed by numbered headers
    headers = ["Line#"] + [str(i) for i in range(1, max_columns + 1)]
    
    # Prepare data with line numbers
    formatted_data = [[index + 1] + row for index, row in enumerate(data)]
    
    # Write to CSV file
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        
        # Write the headers
        writer.writerow(headers)
        
        # Write the data
        writer.writerows(formatted_data)

    print(f"CSV file '{filename}' has been successfully created.")

def generate_mapping_section(height, width, pixel_width, config_order, left_right_state):
    mapping = [[-1 for _o in range(0, width)] for _ in range(0, height)]
    for i, (linenum, line_config) in enumerate(config_order):
        mapping_row = mapping[len(mapping)-((linenum-1)*(PIXEL_COLUMN_MARGIN+1))-1]

        if line_config['Section'] in ('top', 'bottom'):
            current_channel = line_config['ChannelLStart']
            if left_right_state != "left":
                current_channel = line_config['ChannelRStart'] or line_config['ChannelLStart']
            coffset = line_config['CenterOffset']
            loffset = math.floor((pixel_width-line_config["PixelsL"])/2) + coffset

            start = loffset
            end = loffset+line_config["PixelsL"]
            step = 1
            if line_config["PixelsLStart"] == "R":
                start = end-1
                end = loffset-1
                step *= -1
            
            print(i, linenum, loffset, line_config["PixelsL"], pixel_width-loffset-line_config["PixelsL"], loffset+line_config["PixelsL"]+(pixel_width-loffset-line_config["PixelsL"]))
            print('\t', start, end)
            for i in range(start, end, step):
                mapping_row[i*(PIXEL_ROW_MARGIN+1)] = str(current_channel)
                current_channel += 3
        else:
            current_l_channel = line_config['ChannelLStart']
            current_r_channel = line_config['ChannelRStart']

            pixelsL = line_config["PixelsL"]
            pixelsR = line_config["PixelsR"]
            start = 0
            end = pixel_width
            step = 1
            if (left_right_state == "left" and line_config["PixelsLStart"] == "R") \
                or (left_right_state != "left" and line_config["PixelsRStart"] == "R"):
                start = end-1
                end = -1
                step *= -1

            print(i, linenum, left_right_state, pixelsL, pixelsR)
            print('\t', start, end)
            
            for i in range(start, end, step):
                if left_right_state == "left" and i < pixelsL:
                    mapping_row[i*(PIXEL_ROW_MARGIN+1)] = str(current_l_channel)
                    current_l_channel += 3
                elif left_right_state != "left" and i > pixel_width-pixelsR-1:
                    mapping_row[i*(PIXEL_ROW_MARGIN+1)] = str(current_r_channel)
                    current_r_channel += 3
    return mapping

def generate_mapping(height, width, line_configs):
    mapping = [[-1 for _o in range(0, width)] for _ in range(0, height)]

    pixel_height = len(line_configs)
    pixel_width = max([config["PixelsL"]+config["PixelsR"] for row, config in line_configs.items()])

    items = list(line_configs.items())
    #config_order = [*items[:50], *reversed(items[50:]), *reversed(items[50:])]
    #left_right_state = "left"

    mappingL = generate_mapping_section(height, width, pixel_width, items[:50], "left")
    mappingR = generate_mapping_section(height, width, pixel_width, items[-50:], "right") 

    
    
    export_to_csv(mappingL, "mappingL.csv")
    export_to_csv(mappingR, "mappingR.csv")

    return (mappingL, mappingR)

    


def create_custom_model():
    line_configs = read_csv_to_dict('../line_config.csv')
    height = len(line_configs)*(PIXEL_COLUMN_MARGIN+1)
    width = max([config["PixelsL"]+config["PixelsR"] for row, config in line_configs.items()])*(PIXEL_ROW_MARGIN+1)

    lfl = ET.Element('LEDFixtureLibrary')
    
    mappingL, mappingR = generate_mapping(height, width, line_configs)

    def map_lam(mapping):
        for m in mapping:
            yield m
            #yield "\n"

    lfb = ET.SubElement(lfl, "LEDFixture", {
        "product":"CommuneTableBottom",
        "group":"ElectricGerbil",
        "favorite":"0"
    })

    pmL = ET.SubElement(lfb, "PixelMapping", {
        "width": str(width),
        "type": "RGB",
        "height": str(height),
        "avoidCrossUniversePixels": "0"
    })
    pmL.text = " ".join((str(x) for x in itertools.chain(*map_lam(mappingL))))

    lft = ET.SubElement(lfl, "LEDFixture", {
        "product":"CommuneTableTop",
        "group":"ElectricGerbil",
        "favorite":"0"
    })

    pmR = ET.SubElement(lft, "PixelMapping", {
        "width": str(width),
        "type": "RGB",
        "height": str(height),
        "avoidCrossUniversePixels": "0"
    })
    pmR.text = " ".join((str(x) for x in itertools.chain(*map_lam(mappingR))))
    
    # Convert the ElementTree to a string
    xml_str = ET.tostring(lfl, encoding="unicode")
    
    # Add the XML declaration at the top
    # xml_declaration = '<?xml version="1.0"?>\n'
    xml_output = xml_str
    
    # Parse the rough string with minidom for pretty printing
    reparsed = minidom.parseString(xml_output)
    pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

    return pretty_xml_as_string


# Generate the XML
# xml_snippet = create_xml()
xml_snippet = create_custom_model()
print(xml_snippet)
with open(MMFL_OUTPUT, 'w') as f:
    f.write(xml_snippet)


