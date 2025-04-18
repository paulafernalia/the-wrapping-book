from decouple import config
from supabase import create_client, Client
from utils import data_utils
import mimetypes
import os

SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_KEY = config("SERVICE_ROLE_KEY")
SUPABASE_CARRY_TABLE = config("SUPABASE_CARRY_TABLE")
SUPABASE_RATING_TABLE = config("SUPABASE_RATING_TABLE")
SUPABASE_BUCKET = config("SUPABASE_BUCKET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

COLUMNS = [
    "name", "longtitle", "position",
    "size", "mmposition", "difficulty"
]

def update_value_in_table(carryname):
    try:
        # Perform the update on the table
        response = supabase.table(SUPABASE_CARRY_TABLE).update(
            {"tutorial": True}  # Column to update and its new value
        ).eq("name", carryname).execute()

        # Check if the update was successful
        if response is not None:
            print(f"Successfully updated tutorial to True")
        else:
            print("Failed to update:", response.error_message)
    except Exception as e:
        print(f"Error updating value: {e}")


def upload_png_files(file_paths):
    storage = supabase.storage.from_(SUPABASE_BUCKET)

    for file_path in file_paths:
        file_name = os.path.basename(file_path)

        # Check if file already exists
        try:
            existing_files = storage.list("", {"limit": 1000})  # Or use a folder path if needed
            existing_names = [item["name"] for item in existing_files]

            if file_name in existing_names:
                print(f"Skipped {file_name} (already exists)")
                continue
        except Exception as e:
            print(f"Error checking {file_name}: {e}")
            continue

        # Upload file
        with open(file_path, "rb") as f:
            try:
                print(f"Uploading {file_name}...")
                storage.upload(
                    path=file_name,
                    file=f,
                    file_options={"content-type": "image/png", "upsert": "false"},
                )
                print(f"Uploaded {file_name}")
            except Exception as e:
                print(f"Failed to upload {file_name}: {e}")


def get_carries():
    main_table_columns = ",".join(COLUMNS)

    response = (
        supabase.table(SUPABASE_CARRY_TABLE)
        .select(f"""
            name, 
            longtitle, 
            position, 
            size, 
            mmposition,
            {SUPABASE_RATING_TABLE}(difficulty)
        """)
        .eq("tutorial", True)
        .execute()
    )

    carries = [
        data_utils.Carry(
            r["name"],
            r["longtitle"], 
            r["mmposition"],
            r["position"],
            r["size"],
            r["wrappinggallery_rating"]["difficulty"]
        ) for r in response.data
    ]

    return carries


def get_carry_by_name(carryname):
    main_table_columns = ",".join(COLUMNS)

    response = (
        supabase.table(SUPABASE_CARRY_TABLE)
        .select(f"""
            name, 
            longtitle, 
            position, 
            size, 
            mmposition,
            {SUPABASE_RATING_TABLE}(difficulty)
        """)
        .eq("tutorial", True)
        .eq("name", carryname)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None  # or raise an exception if preferred

    r = response.data[0]
    return data_utils.Carry(
        r["name"],
        r["longtitle"],
        r["mmposition"],
        r["position"],
        r["size"],
        r["wrappinggallery_rating"]["difficulty"]
    )


def get_tutorial_steps_by_carry(name_filter):
    """
    Gets images from a Supabase storage bucket where filename contains a specific string
    
    Args:
        name_filter (str): String to filter filenames by (will match if filename contains this string)
        folder_path (str, optional): Optional folder path within the bucket. Defaults to "".
    
    Returns:
        dict: Dictionary containing list of images with their data and URLs, or error message
    """
    try:
        # List all files in the specified bucket and folder
        response = supabase.storage.from_(SUPABASE_BUCKET).list("", {"limit": 1000})
        
        if not response:
            return {"data": None, "error": "No files found or error listing files"}
        
        # Filter for image files
        image_files = []
        for file in response:
            file_name = file.get("name")
            if file_name:
                # Prepare strings for comparison based on case sensitivity setting
                
                # Check if file is an image and name contains the filter string
                mime_type, _ = mimetypes.guess_type(file_name)
                if mime_type and mime_type.startswith('image/') and file_name.startswith(name_filter + "_step"):
                    # Generate public URL for the image
                    signed_url_response = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                        file_name, expires_in=3600
                    )
                    
                    if "signedURL" in signed_url_response:
                        image_files.append({
                            "name": file_name,
                            "url": signed_url_response["signedURL"],
                        })

        return {"data": image_files, "error": None}
    
    except Exception as e:
        return {"data": None, "error": str(e)}
