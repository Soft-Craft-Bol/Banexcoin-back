import cloudinary
import cloudinary.uploader

from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

def upload_raw_file(file_path: str, public_id: str):
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        folder="crypto-reconciliation/uploads",
        public_id=public_id,
        overwrite=True,
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
    }