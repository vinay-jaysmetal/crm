

import json

from rest_framework.exceptions import ValidationError

# from UserApp.utils import OPTIONS_JSON


# def validate_category(category_name, category_data):
#     """
#     Validates a category field (e.g., basic_details, physical_appearance) against the JSON schema.

#     Parameters:
#     - category_name (str): The main category to validate, e.g., 'basic_details', 'physical_appearance'.
#     - category_data (dict or str): The input dictionary for the category. 

#     Raises:
#     - ValidationError: If an unknown key is found or if a value is invalid.
    
#     Returns:
#     validated data
#     """
#     errors = []
#     return_data = {}
#     # If category_data is a string, try to parse it as JSON
#     if isinstance(category_data, str):
#         try:
#             category_data = json.loads(category_data)
#         except json.JSONDecodeError:
#             raise ValidationError({category_name: f"Invalid JSON format for {category_name}."})

#     # Get the expected schema for this category
#     category_schema = OPTIONS_JSON.get(category_name, {})
#     if not category_schema:
#         raise ValidationError({category_name: f"Unknown category '{category_name}' in JSON schema."})

#     for key, value in category_data.items():
#         print("key ",key," value ",value)
#         # Check if the key exists in JSON schema
#         if key not in category_schema:
#             # errors.append(f"Unknown key '{key}' in {category_name}. Expected keys: {list(category_schema.keys())}")
#             print(f"Removed Unknown key '{key}' in {category_name}. Expected keys: {list(category_schema.keys())}")
#             continue  # Skip further validation for this key
        
#         return_data.update({key:value})

#         # Check if the value exists for the given key in JSON schema
#         valid_values = category_schema[key]
#         if not isinstance(valid_values, dict):
#             continue

#         if str(value) and str(value) not in valid_values:
#             errors.append(f"Invalid value '{value}' for key '{key}' in {category_name}. Expected values: {list(valid_values.keys())}")
            

#     if errors:
#         raise ValidationError({category_name: errors})
#     print("return data ",return_data)
#     return return_data


# # Example usage in a request
# def custom_validate_request(data):
#     try:
#         # Assume data is a dictionary containing all categories (basic_details, physical_appearance, etc.)
#         categories_to_validate = list(OPTIONS_JSON.keys())
        
#         for category in categories_to_validate:
#             validated_categories = {}
#             category_data = data.get(category)
#             if category_data:
#                 print("Validating category ", category, category_data)
#                 validated_categories = validate_category(category, category_data)
                
#             data[category] = validated_categories
        
#         data["highlight_tags"] = json.loads( data.get("highlight_tags", "[]"))
        
#         return data
#     except Exception as e:
#         print("Error in custom validation ", e)
#         raise ValidationError({"error": str(e)})