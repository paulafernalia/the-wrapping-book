from decouple import config
from supabase import create_client, Client
from utils import data_utils

SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_KEY = config("SERVICE_ROLE_KEY")
SUPABASE_TABLE = config("SUPABASE_TABLE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_carries():
    columns = ["name", "longtitle", "position", "size", "mmposition"]
    column_str = ",".join(columns)
    SUPABASE_TABLE = config("SUPABASE_TABLE")

    response = (
        supabase.table(SUPABASE_TABLE)
        .select(column_str)
        .eq("tutorial", True)
        .execute()
    )

    carries = [
        data_utils.Carry(
            r["name"],
            r["longtitle"], 
            r["mmposition"],
            r["position"],
            r["size"]
        ) for r in response.data
    ]

    return carries