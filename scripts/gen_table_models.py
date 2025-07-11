import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import csv
import math

# line_ranges ={
#     **{i:('commune_table1', 'bottom', 1) for i in range(1,10)}, #bottom1 9 lines
#     **{i:('commune_table1', 'bottom', 2) for i in range(10,17)}, #bottom2 7 lines
#     **{i:('commune_table1', 'bottom', 3) for i in range(17,22)}, #bottom3 6 lines
#     **{i:('commune_table1', 'bottom', 4) for i in range(22,27)}, #bottom4 4 lines

#     **{i:('commune_table1', 'quad', 5) for i in range(27,42)}, #quad 15 lines
#     **{i:('commune_table1', 'quad', 6) for i in range(42,46)}, #quad 4 lines
#     **{i:('commune_table1', 'quad', 7) for i in range(46,61)}, #quad 15 lines
#     **{i:('commune_table1', 'quad', 8) for i in range(61, 65)}, #quad 4 lines

#     **{i:('commune_table2','top', 4) for i in range(65, 69)}, #top 4 lines
#     **{i:('commune_table2','top', 3) for i in range(69, 74)}, #top 6 lines
#     **{i:('commune_table2','top', 2) for i in range(74, 82)}, #top 7 lines
#     **{i:('commune_table2','top', 1) for i in range(82, 91)}, #top 9 lines
# }
# pixel_counts = {0:   0, 
#                 1:  41, 2:  44, 3:  46, 4:  48, 5:  50, 6:  54, 7:  56, 8:  60, 9:  62, 
#                 10: 64, 11: 65, 12: 67, 13: 71, 14: 73, 15: 75, 16: 79, 
#                 17: 81, 18: 83, 19: 88, 20: 90, 21: 92,  
#                 22: 96, 23: 98, 24: 100, 25: 100, 26: 100, 

#                 #24
#                 27: 41, 28: 40, 29: 38, 30: 38, 31: 36, 32: 36, 33: 33, 34: 32, 35: 32, 36: 30, 37: 30, 38: 29, 39: 29, 40: 29, 41: 29, 
#                 42: 29, 43: 29, 44: 29, 45: 29, 
#                 46: 29, 47: 29, 48: 29, 49: 29, 50: 29, 51: 29, 52: 29, 53: 29, 54: 30, 55: 30, 56: 32, 57: 32, 58: 33, 59: 36, 60: 36, 
#                 61: 38, 62: 38, 63: 40, 64: 41, 

#                 65:100, 66:100, 67:100, 68: 98, 69: 96,
#                 70: 92, 71: 90, 72: 88, 73: 83, 
#                 74: 81, 75: 79, 76: 75, 77: 73, 78: 71, 79: 67, 80: 65, 81: 64, 
#                 82: 62, 83: 60, 84: 56, 85: 54, 86: 50, 87: 48, 88: 46, 89: 44, 90: 41}

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

line_configs = read_csv_to_dict('../line_config.csv')

start_world_x = 48.9468

distance_between_lines_x = 1.175

pixel_width = (-1*(-30.85-6.73))/41.0

string_start_bottom_z_left = 7.1426
string_start_bottom_z_right = -32.29

string_start_quad_z_left = 32.7131
string_start_quad_z_right = -56.17

string_start_pixel_count = line_configs[1]['PixelsL']

table_world_pos_y = 43.0
table_y2_pos = -0.044338

common_attributes = {
                "DisplayAs": "Single Line",
                "StringType": "RGB Nodes",
                "StartSide": "B",
                "Dir": "L",
                "Antialias": "1",
                "PixelSize": "2",
                "Transparency": "0",
                "LayoutGroup": "Default",
                "parm1": "1",
                "parm3": "1",
                "versionNumber": "7",
        }

def get_top_bottom_attributes(linenum, line_config, world_pos_x):
    pixel_count = line_config['PixelsL']
    start_pixel = 1 + sum([cfg['PixelsL'] for i, cfg in line_configs.items() if i < linenum])
    pixel_start_offset = pixel_count - string_start_pixel_count
    
    world_pos_z = string_start_bottom_z_left + ((pixel_start_offset * pixel_width)/2)

    x2 = -0.480370
    z2 = -1*(pixel_width*pixel_count) #this is length
    
    if linenum % 2 ==0: #reverse the lines
        world_pos_z = string_start_bottom_z_right - (((pixel_start_offset-1) * pixel_width)/2)
        world_pos_x -= distance_between_lines_x/2
        z2 *= -1
        x2 *= -1

    model_attributes = {
        **common_attributes,
        "Controller": line_config['LController'],
        "StartChannel": f"!{line_config['LController']}:{1 + (3 * start_pixel)}",
        "name": f"table_{line_config['Section']}_{linenum}",
        "parm2": str(pixel_count), # pixels in string

        "WorldPosX": str(world_pos_x),
        "WorldPosY": str(table_world_pos_y), #verticle position, stays the same
        "WorldPosZ": str(world_pos_z), 
        "X2": str(x2),
        "Y2": str(table_y2_pos),
        "Z2": str(z2)
    }

    if linenum != 1:
        model_attributes["ModelChain"] =  f">table_{line_config['Section']}_{linenum-1}"

    controller_attrs = {
        "Port": str(line_config['LPin']),
        "Protocol": "ws2811"
    }

    return model_attributes, controller_attrs

def get_quad_left_attributes(linenum, line_config, world_pos_x):
    l_pixel_count = line_config['PixelsL']
    l_start_pixel = 1 + sum([cfg['PixelsL'] for i, cfg in line_configs.items() if i < linenum])

    l_string_length = pixel_width*l_pixel_count
    l_world_pos_z = string_start_quad_z_left
    l_world_pos_x = world_pos_x
    x2 = -0.480370
    z2 = -1*l_string_length
    
    if linenum % 2 ==0: #reverse the lines
        #l_world_pos_z = -2.43+(pixel_width*(line_configs[27]["PixelsL"]-l_pixel_count))
        l_world_pos_z = string_start_quad_z_left - (l_pixel_count * pixel_width)
        l_world_pos_x -= distance_between_lines_x/2
        x2 *= -1
        z2 = l_string_length
    
    model_attributes = {
        **common_attributes,
        "Controller": line_config['LController'],
        "StartChannel": f"!{line_config['LController']}:{1 + (3 * l_start_pixel)}",
        "name": f"table_{line_config['Section']}_{linenum}L",
        "parm2": str(l_pixel_count), # pixels in string

        "WorldPosX": str(l_world_pos_x),
        "WorldPosY": str(table_world_pos_y), #verticle position, stays the same
        "WorldPosZ": str(l_world_pos_z), 
        "X2": str(x2),
        "Y2": str(table_y2_pos),
        "Z2": str(z2)
    }

    if linenum != 1:
        model_attributes["ModelChain"] =  f">table_{line_config['Section']}_{linenum-1}L"

    controller_attrs = {
        "Port": str(line_config['LPin']),
        "Protocol": "ws2811"
    }

    return model_attributes, controller_attrs

def get_quad_right_attributes(linenum, line_config, world_pos_x):
    r_start_pixel = 1 + sum([cfg['PixelsR'] for i, cfg in line_configs.items() if i < linenum])
    r_pixel_count = line_config['PixelsR']
    r_string_length = pixel_width*r_pixel_count
    r_world_pos_z = string_start_quad_z_right
    r_world_pos_x = world_pos_x - distance_between_lines_x/2
    x2 = 0.315968
    z2 = r_string_length
    if linenum % 2 ==0: #reverse the lines
        r_world_pos_z = -18.4420 - (pixel_width*(line_configs[27]["PixelsR"]-r_pixel_count))
        r_world_pos_x = world_pos_x 
        x2 *= -1
        z2 = -1 * r_string_length


    model_attributes = {
        **common_attributes,
        "Controller": "commune_table2", #ugly, but R is always on other controller
        "StartChannel": f"!commune_table2:{1 + (3 * r_start_pixel)}",
        "name": f"table_{line_config['Section']}_{linenum}R",
        "parm2": str(r_pixel_count), # pixels in string

        "WorldPosX": str(r_world_pos_x),
        "WorldPosY": str(table_world_pos_y), #verticle position, stays the same
        "WorldPosZ": str(r_world_pos_z), 
        "X2": str(x2),
        "Y2": str(table_y2_pos),
        "Z2": str(z2)
    }

    if linenum != 1:
        model_attributes["ModelChain"] =  f">table_{line_config['Section']}_{linenum-1}R"

    controller_attrs = {
        "Port": str(line_config['RPin']),
        "Protocol": "ws2811"
    }

    return model_attributes, controller_attrs


def create_xml():
    # Create the root element with attributes
    models = ET.Element('models')
    for linenum, line_config in line_configs.items():
        

        world_pos_x = start_world_x - (distance_between_lines_x * (linenum-1))  #change this to move up table 48.9697 is the 1st 41.1276 is the 9th
        
        if line_config['Section'] in ('top', 'bottom'):
            attrs, controller_attrs = get_top_bottom_attributes(linenum, line_config, world_pos_x)

            model = ET.SubElement(models, "model", attrs)
            ET.SubElement(model, "ControllerConnection", controller_attrs)

        else: #is quad
            l_attrs, l_controller_attrs = get_quad_left_attributes(linenum, line_config, world_pos_x)

            model = ET.SubElement(models, "model", l_attrs)
            ET.SubElement(model, "ControllerConnection", l_controller_attrs)

            r_attrs, r_controller_attrs = get_quad_right_attributes(linenum, line_config, world_pos_x)

            model = ET.SubElement(models, "model", r_attrs)
            ET.SubElement(model, "ControllerConnection", r_controller_attrs)

            
    
    # Convert the ElementTree to a string
    xml_str = ET.tostring(models, encoding="unicode")
    
    # Add the XML declaration at the top
    xml_declaration = '<?xml version="1.0"?>\n'
    xml_output = xml_declaration + xml_str
    
    # Parse the rough string with minidom for pretty printing
    reparsed = minidom.parseString(xml_output)
    pretty_xml_as_string = reparsed.toprettyxml(indent="  ")
    
    return pretty_xml_as_string


def create_custom_model():
    

    attrs = {
        "name": "table",
        "parm1": str(100), #matrix width
        "parm2": str(76), #lines
        "Depth": "1",
        "StringType": "RGB Nodes",
        "Transparency":"0",
        "PixelSize":"2",
        "ModelBrightness":"0",
        "Antialias":"1",
        "StrandNames":"",
        "NodeNames":"",
        "LayoutGroup":"Default",
        "CustomModelCompressed":"1,0,28;2,0,29;3,0,30;4,0,31;5,0,32;6,0,33;7,0,34;8,0,35;9,0,36;10,0,37;11,0,38;12,0,39;13,0,40;14,0,41;15,0,42;16,0,43;17,0,44;18,0,45;19,0,46;20,0,47;43,1,27;42,1,28;41,1,29;40,1,30;39,1,31;38,1,32;37,1,33;36,1,34;35,1,35;34,1,36;33,1,37;32,1,38;31,1,39;30,1,40;29,1,41;28,1,42;27,1,43;26,1,44;25,1,45;24,1,46;23,1,47;22,1,48;21,1,49",
        "Protocol": "ws2811",
        "SourceVersion":"2024.13"
    }

    model_placements = []
    current_pixel = 1
    for linenum, line_config in line_configs.items():
        line_placement = [""] * 100

        if line_config['Section'] in ('top', 'bottom'):
            loffset = math.floor((100-line_config["PixelsL"])/2)
            start = loffset
            end = loffset+line_config["PixelsL"]
            step = 1
            if linenum % 2 == 0:
                start = end-1
                end = loffset+1
                step = -1
            
            for i in range(start, end, step):
                line_placement[i] = str(current_pixel)
                current_pixel += 1
        
        model_placements.append(line_placement)

    attrs["CustomModel"] = ';'.join((','.join(lp) for lp in model_placements))
    
    model = ET.Element('custommodel', attrs)

     # Convert the ElementTree to a string
    xml_str = ET.tostring(model, encoding="unicode")
    
    # Add the XML declaration at the top
    xml_declaration = '<?xml version="1.0"?>\n'
    xml_output = xml_declaration + xml_str
    
    # Parse the rough string with minidom for pretty printing
    reparsed = minidom.parseString(xml_output)
    pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

    return pretty_xml_as_string


# Generate the XML
# xml_snippet = create_xml()
xml_snippet = create_custom_model()
print(xml_snippet)


