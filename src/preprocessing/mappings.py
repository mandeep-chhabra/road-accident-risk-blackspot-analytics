"""
Official STATS19 UK Road Safety Variable Lookups and Encodings.
Derived from the UK Department for Transport (DfT) Open Data Standards.
"""

SEVERITY_MAP = {
    1: "Fatal",
    2: "Serious",
    3: "Slight",
}

SEVERITY_CODE_MAP = {
    "Fatal": 1,
    "Serious": 2,
    "Slight": 3,
}

DAY_OF_WEEK_MAP = {
    1: "Sunday",
    2: "Monday",
    3: "Tuesday",
    4: "Wednesday",
    5: "Thursday",
    6: "Friday",
    7: "Saturday",
}

LIGHT_CONDITIONS_MAP = {
    1: "Daylight",
    4: "Darkness - lights lit",
    5: "Darkness - lights unlit",
    6: "Darkness - no street lighting",
    7: "Darkness - lighting unknown",
    -1: "Missing / Unknown",
}

WEATHER_CONDITIONS_MAP = {
    1: "Fine no high winds",
    2: "Raining no high winds",
    3: "Snowing no high winds",
    4: "Fine + high winds",
    5: "Raining + high winds",
    6: "Snowing + high winds",
    7: "Fog or mist",
    8: "Other",
    9: "Unknown",
    -1: "Missing / Unknown",
}

ROAD_SURFACE_CONDITIONS_MAP = {
    1: "Dry",
    2: "Wet or damp",
    3: "Snow",
    4: "Frost or ice",
    5: "Flood over 3cm",
    6: "Oil or diesel",
    7: "Mud",
    9: "Unknown",
    -1: "Missing / Unknown",
}

ROAD_TYPE_MAP = {
    1: "Roundabout",
    2: "One way street",
    3: "Dual carriageway",
    6: "Single carriageway",
    7: "Slip road",
    9: "Unknown",
    12: "One way street / Slip road",
    -1: "Missing / Unknown",
}

URBAN_RURAL_MAP = {
    1: "Urban",
    2: "Rural",
    3: "Unallocated",
    -1: "Missing / Unknown",
}

JUNCTION_DETAIL_MAP = {
    0: "Not at junction",
    1: "Roundabout",
    2: "Mini-roundabout",
    3: "T or staggered junction",
    5: "Slip road",
    6: "Crossroads",
    7: "More than 4 arms",
    8: "Private drive or entrance",
    9: "Other junction",
    13: "T or staggered junction",
    16: "Crossroads",
    17: "Roundabout",
    18: "Slip road",
    19: "Other junction",
    -1: "Missing / Unknown",
}

JUNCTION_CONTROL_MAP = {
    -1: "Not at junction / Unknown",
    0: "Not at junction",
    1: "Authorised person",
    2: "Auto traffic signal",
    3: "Stop sign",
    4: "Give way or uncontrolled",
    9: "Unknown",
}

POLICE_FORCE_MAP = {
    1: "Metropolitan Police",
    2: "Cumbria",
    3: "Lancashire",
    4: "Cheshire",
    5: "Merseyside",
    6: "Greater Manchester",
    7: "North Yorkshire",
    10: "Northumbria",
    11: "Durham",
    12: "North Yorkshire",
    13: "West Yorkshire",
    14: "South Yorkshire",
    16: "Humberside",
    17: "Cleveland",
    20: "West Midlands",
    21: "Staffordshire",
    22: "West Mercia",
    23: "Warwickshire",
    30: "Derbyshire",
    31: "Nottinghamshire",
    32: "Lincolnshire",
    33: "Leicestershire",
    34: "Northamptonshire",
    35: "Cambridgeshire",
    36: "Norfolk",
    37: "Suffolk",
    40: "Bedfordshire",
    41: "Hertfordshire",
    42: "Essex",
    43: "Thames Valley",
    44: "Hampshire",
    45: "Surrey",
    46: "Kent",
    47: "Sussex",
    48: "City of London",
    50: "Devon & Cornwall",
    52: "Avon & Somerset",
    53: "Gloucestershire",
    54: "Wiltshire",
    55: "Dorset",
    60: "North Wales",
    61: "Gwent",
    62: "South Wales",
    63: "Dyfed-Powys",
    91: "Police Scotland (North)",
    92: "Police Scotland (North East)",
    93: "Police Scotland (East)",
    94: "Police Scotland (West)",
    95: "Police Scotland (Central)",
    96: "Police Scotland (South)",
    97: "Police Scotland (Highlands)",
    98: "Police Scotland (Islands)",
    99: "Police Scotland",
}

REGION_MAP = {
    "Metropolitan Police": "London",
    "City of London": "London",
    "Greater Manchester": "North West",
    "Lancashire": "North West",
    "Cumbria": "North West",
    "Cheshire": "North West",
    "Merseyside": "North West",
    "West Midlands": "West Midlands",
    "Staffordshire": "West Midlands",
    "West Mercia": "West Midlands",
    "Warwickshire": "West Midlands",
    "West Yorkshire": "Yorkshire & The Humber",
    "South Yorkshire": "Yorkshire & The Humber",
    "North Yorkshire": "Yorkshire & The Humber",
    "Humberside": "Yorkshire & The Humber",
    "Northumbria": "North East",
    "Durham": "North East",
    "Cleveland": "North East",
    "Derbyshire": "East Midlands",
    "Nottinghamshire": "East Midlands",
    "Lincolnshire": "East Midlands",
    "Leicestershire": "East Midlands",
    "Northamptonshire": "East Midlands",
    "Cambridgeshire": "East of England",
    "Norfolk": "East of England",
    "Suffolk": "East of England",
    "Bedfordshire": "East of England",
    "Hertfordshire": "East of England",
    "Essex": "East of England",
    "Thames Valley": "South East",
    "Hampshire": "South East",
    "Surrey": "South East",
    "Kent": "South East",
    "Sussex": "South East",
    "Devon & Cornwall": "South West",
    "Avon & Somerset": "South West",
    "Gloucestershire": "South West",
    "Wiltshire": "South West",
    "Dorset": "South West",
    "North Wales": "Wales",
    "Gwent": "Wales",
    "South Wales": "Wales",
    "Dyfed-Powys": "Wales",
    "Police Scotland": "Scotland",
}

VEHICLE_TYPE_MAP = {
    1: "Pedal cycle",
    2: "Motorcycle 50cc and under",
    3: "Motorcycle 125cc and under",
    4: "Motorcycle over 125cc up to 500cc",
    5: "Motorcycle over 500cc",
    8: "Taxi / Private hire car",
    9: "Car",
    10: "Minibus (8-16 passenger seats)",
    11: "Bus or coach (17 or more pass seats)",
    16: "Ridden horse",
    17: "Agricultural vehicle",
    18: "Tram",
    19: "Van / Goods 3.5 tonnes mgw or under",
    20: "Goods over 3.5t. and under 7.5t",
    21: "Goods 7.5 tonnes mgw and over",
    22: "Mobility scooter",
    23: "Electric motorcycle",
    90: "Other vehicle",
    97: "Motorcycle - unknown cc",
    98: "Goods vehicle - unknown weight",
    -1: "Missing / Unknown",
}

CASUALTY_CLASS_MAP = {
    1: "Driver or rider",
    2: "Vehicle or pillion passenger",
    3: "Pedestrian",
    -1: "Unknown",
}

CASUALTY_SEVERITY_MAP = {
    1: "Fatal",
    2: "Serious",
    3: "Slight",
}

