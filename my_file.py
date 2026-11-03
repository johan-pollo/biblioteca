# Set your Cloudinary credentials
# ==============================
from dotenv import load_dotenv
load_dotenv()

# Import the Cloudinary libraries
# ==============================
import cloudinary
from cloudinary import CloudinaryImage
import cloudinary.uploader
import cloudinary.api

# Import to format the JSON responses
# ==============================
import json

# Set configuration parameter: return "https" URLs by setting secure=True  
# ==============================
config = cloudinary.config(secure=True)

# Log the configuration
# ==============================
print("****1. Set up and configure the SDK:****\nCredentials: ", config.cloud_name, config.api_key, "\n")


def uploadImage():
    # Upload the image and get its URL
    # ==============================
    # Set the asset's public ID and allow overwriting the asset with new versions
    cloudinary.uploader.upload(
        "https://cloudinary-devs.github.io/cld-docs-assets/assets/images/butterfly.jpeg",
        public_id="quickstart_butterfly",
        unique_filename=False,
        overwrite=True
    )

    # Build the URL for the image and save it in the variable 'srcURL'
    srcURL = CloudinaryImage("quickstart_butterfly").build_url()

    # Log the image URL to the console. 
    print("****2. Upload an image****\nDelivery URL: ", srcURL, "\n")


def getAssetInfo():
    # Get and use details of the image
    # ==============================
    image_info = cloudinary.api.resource("quickstart_butterfly")
    print("****3. Get and use details of the image****\nUpload response:\n", json.dumps(image_info, indent=2), "\n")

    # Assign tags to the uploaded image based on its width. Save the response to the update in the variable 'update_resp'.
    if image_info["width"] > 900:
        update_resp = cloudinary.api.update("quickstart_butterfly", tags="large")
    elif image_info["width"] > 500:
        update_resp = cloudinary.api.update("quickstart_butterfly", tags="medium")
    else:
        update_resp = cloudinary.api.update("quickstart_butterfly", tags="small")

    # Log the new tag to the console.
    print("New tag: ", update_resp["tags"], "\n")


def createTransformation():
    # Transform the image
    # ==============================
    transformedURL = CloudinaryImage("quickstart_butterfly").build_url(width=100, height=150, crop="fill")

    # Log the URL to the console
    print("****4. Transform the image****\nTransformation URL: ", transformedURL, "\n")


def main():
    uploadImage()  
    getAssetInfo()
    createTransformation()


if __name__ == "__main__":
    main()
