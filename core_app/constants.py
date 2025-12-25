NON_DB_FIELDS = [
    'is_dropdown',
    'is_report',
    'is_user_app',    
    'pagination',
    'search',
    'limit',
    'offset',
    'page',
    'page_size',
    'o',
]

CLERK_DEPARTMENT = "clerk"
SHOP_DEPARTMENT = "shop"
CUT_DEPARTMENT = "cut"
FIT_DEPARTMENT = "fit"
DELIVERY_DEPARTMENT = "delivery"
RECEIVED_DEPARTMENT = "received"
ERECT_DEPARTMENT = "erect"
WELD_DEPARTMENT = "weld"
DELIVERY_3P_DEPARTMENT = "delivery 3p"
                                         

DEPARTMENT_JSON = [
    {
        "id": 1,
        "name": CLERK_DEPARTMENT,
        "description": "Initial data entry, job assignment, or documentation handling.",
    },
    {
        "id": 2,
        "name": SHOP_DEPARTMENT,
        "description": "Internal shop work; possibly planning, material preparation, or initial job routing.",
    },
    {
        "id": 3,
        "name": CUT_DEPARTMENT,
        "description": "Raw material cutting (steel, metal sheets, etc.).",
    },
    {
        "id": 4,
        "name": FIT_DEPARTMENT,
        "description": "Shaping into the desired shape.",
    },
    {
        "id": 5,
        "name": DELIVERY_DEPARTMENT,
        "description": "Logistics team ships the fitted items to the site.",
    },
    {
        "id": 6,
        "name": RECEIVED_DEPARTMENT,
        "description": "Client or site team confirms receipt of materials.",
    },
    {
        "id": 7,
        "name": ERECT_DEPARTMENT,
        "description": "Final erection/installation of the delivered components at the construction site.",
    },
    {
        "id": 8,
        "name": WELD_DEPARTMENT,
        "description": "Welding of the components.",
    },
    {
        "id": 9,
        "name": DELIVERY_3P_DEPARTMENT,
        "description": "Logistics team ships the fitted items to the site.",
    }
]

DEPARTMENT_CHOICES = [
    (1, CLERK_DEPARTMENT),
    (2, SHOP_DEPARTMENT),
    (3, CUT_DEPARTMENT),
    (4, FIT_DEPARTMENT),
    (5, DELIVERY_DEPARTMENT),
    (6, RECEIVED_DEPARTMENT),
    (7, ERECT_DEPARTMENT),
    (8, WELD_DEPARTMENT),
    (9, DELIVERY_3P_DEPARTMENT),
]

TEST_OTP = "123123"

PRODUCTION_CATEGORIES_DATA = [
  { "id": "columns", "name": "Columns" },
  { "id": "beams", "name": "Beams" },
  { "id": "joists", "name": "Joists" },
  { "id": "joist braces", "name": "Joist Braces" },
  { "id": "parapets", "name": "Parapets" },
  { "id": "window channels", "name": "Window Channels" },
  { "id": "cross bracing", "name": "Cross Bracing" },
  { "id": "roof bracing", "name": "Roof Bracing" },
  { "id": "rtus", "name": "RTUs" },
  { "id": "stairs", "name": "Stairs" },
  { "id": "handrails", "name": "Handrails" },
  { "id": "roof hatch", "name": "Roof Hatch" },
  { "id": "roof access ladder", "name": "Roof Access Ladder" },
  { "id": "girts", "name": "Girts" },
  { "id": "knee bracing", "name": "Knee Bracing" },
  { "id": "roof deck", "name": "Roof Deck" },
  { "id": "perimeter angle", "name": "Perimeter Angle" },
  { "id": "base plates", "name": "Base Plates" },
  { "id": "anchor bolts", "name": "Anchor Bolts" },
  { "id": "embed plates", "name": "Embed Plates" },
  { "id": "garbage enclosure", "name": "Garbage Enclosure" },
  { "id": "bollards", "name": "Bollards" },
]
