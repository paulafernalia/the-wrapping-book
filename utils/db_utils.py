from decouple import config
from supabase import create_client, Client
from utils import data_utils
import mimetypes

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
