import json
from core_app.constants import PRODUCTION_CATEGORIES_DATA, TEST_OTP
from django_solvitize.utils.GlobalFunctions import ValidateRequest, ResponseFunction
from django.core.mail import send_mail

import string
import random
import pandas as pd
import os

from jaysmetal_backend.celery import app


def filter_valid_fields(model, data):
    """
    Filters out keys that are not fields in the given model.

    :param model: The Django model class
    :param data: The request data (dict-like)
    :return: A filtered dictionary with only valid model fields
    """
    model_fields = {field.name for field in model._meta.fields}  # Get model field names
    return {key: value for key, value in data.items() if key in model_fields}


def get_bool_value(value):
    true_list = ["1", "true", "True", True, 1]
    false_list = ["0", "false", "False", False, 0]
    if value in true_list:
        return True
    elif value in false_list:
        return False
    else:
        return None


def verify_otp(otp):
    """
    Verify the OTP for a user.

    """
    
    # Get the OTP from the request
    
    if otp == TEST_OTP:
        return True  # For testing purposes, always return True if OTP is "123123"
    

def validate_request(request, required_fields: list = []):
    """
    Validate the request data for login
    """
    required = required_fields
    validation_errors = ValidateRequest(required, request.data)

    if len(validation_errors) > 0:
        return ResponseFunction(0, validation_errors[0]["error"], {})
    else:
        print("Received required Fields")
        return True


def validate_fablist_file(file_obj):
    """
    Validates fablist_file for correct format, required columns, and proper data types.
    Returns: (is_valid: bool, data: list | error_message: str)
    """
    try:
        filename = file_obj.name
        ext = os.path.splitext(filename)[1].lower()

        if ext not in [".csv", ".xls", ".xlsx"]:
            return False, "Invalid file format. Only CSV, XLS, XLSX are allowed."

        # Read file
        if ext == ".csv":
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_excel(file_obj)
            
        # Normalize column headers to lowercase
        df.columns = [col.lower().strip() for col in df.columns]


        # Required columns
        required_columns = {"name", "qty", "kg"}
        missing = required_columns - set(df.columns)
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"
        
        # Optional columns
        has_profile = "profile" in df.columns
        has_description = "description" in df.columns

        records = []
        row_errors = []
        
        
        
        # set of valid ids (lowercase)
        VALID_CATEGORY_IDS = {item["id"].lower() for item in PRODUCTION_CATEGORIES_DATA}

        for index, row in df.iterrows():
            row_number = index + 2  # 1-based indexing + header
            categories = []
            try:
                name = str(row["name"]).strip()
                if not name:
                    raise ValueError("Name cannot be empty")

                qty_raw = row["qty"]
                kg_raw = row["kg"]

                # Convert qty to int
                try:
                    qty = int(float(qty_raw))
                except:
                    raise ValueError("Qty must be an integer")

                # Convert kg to float
                try:
                    kg = float(kg_raw)
                except:
                    raise ValueError("Kg must be a number")

                # --- NEW CATEGORY PARSING ---
                import math

                categories_raw_value = row.get("categories", "")
                print("categories_raw", categories_raw_value)
                

                
                if categories_raw_value is None or (isinstance(categories_raw_value, float) and math.isnan(categories_raw_value)):
                    categories = []
                else:
                    categories_raw = str(categories_raw_value).strip()
                    if categories_raw:
                        
                        print("++++++++. categories_raw", categories_raw)
                        
                        categories = [cat.strip().lower() for cat in categories_raw.split(",") if cat.strip()]
                        
                        categories_set = set(categories)
                        
                        # subset check
                        if not categories_set.issubset(VALID_CATEGORY_IDS):
                            invalid = categories_set - VALID_CATEGORY_IDS
                            raise ValueError(f"Invalid category id(s): {sorted(invalid)}")

                    else:   
                        categories = []

                
                # categories_raw = str(row.get("categories", "")).strip()
                # if categories_raw:
                #     categories = [cat.strip() for cat in categories_raw.split(",") if cat.strip()]
                # else:
                #     categories = []
                    
                print("categories", categories)
                # ----------------------------

                profile = str(row["profile"]).strip() if has_profile else ""
                description = str(row["description"]).strip() if has_description else ""

                records.append(
                    {
                        "name": name,
                        "profile": profile,
                        "description": description,
                        "categories": categories,  # this is now a python list
                        "qty": qty,
                        "kg": kg,
                    }
                )

            except Exception as e:
                row_errors.append(f"Row {row_number} ({name}): {str(e)}")

        if row_errors:
            return False, "File contains errors: " + ", ".join(row_errors)

        return True, records

    except Exception as e:
        return False, f"Error reading fablist file: {str(e)}"


@app.task#(bind=True)
def django_send_email(payload):

    from jaysmetal_backend.settings import DEFAULT_FROM_EMAIL

    res = send_mail(
        subject=payload["subject"],
        message=payload["body"],
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[payload["to_email"]],
    )
    print("Email sent", res)


def generate_password(length=8, type="strong"):
    """
    Generate a random password of the given length and type.

    Parameters:
        length (int): The length of the password. Must be greater than 0.
        type (str, optional): The type of password to generate. Defaults to "strong".
            - "numeric": A password consisting of only numbers.
            - "alphabets": A password consisting of only alphabets.
            - "alphanumeric": A password consisting of both numbers and alphabets.
            - "strong": A password consisting of numbers, alphabets, and symbols.

    Returns:
        str: The generated password.
    """
    if length <= 0:
        raise ValueError("Length must be greater than 0")

    numbers = string.digits
    letters = string.ascii_letters
    symbols = string.punctuation

    if type == "numeric":
        charset = numbers
    elif type == "alphabets":
        charset = letters
    elif type == "alphanumeric":
        charset = letters + numbers
    elif type == "strong":
        charset = letters + numbers + symbols
    else:
        raise ValueError(
            "Invalid type. Use 'numeric', 'alphabets', 'alphanumeric', or 'strong'"
        )

    password = "".join(random.choice(charset) for _ in range(length))
    return password
