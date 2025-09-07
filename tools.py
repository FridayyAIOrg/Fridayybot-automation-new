# tools.py
import asyncio
from io import BytesIO
from urllib.parse import urlencode
import aiohttp
from openai import AsyncOpenAI

from config import OPENROUTER_API_KEY


client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

base_url = "https://dev.fridayy.ai"

# -------------------------
# AUTH & STORE FUNCTIONS
# -------------------------

async def auth_vendor(phone_no):
    async with aiohttp.ClientSession() as session:
        async with session.post(base_url + "/ocr/auth/vendor/", json={"phone_no": phone_no}) as response:
            data = await response.json()
            return {
                "user_token": data.get("access_token"),
                "store_id": data.get("store_id"),
                "new_user": data.get("new_user")
            }

async def create_store(categories, token):
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(base_url + "/ocr/create_store/", json={"categories": categories}, headers=headers) as response:
            data = await response.json()
            return {"store_id": data.get("id")}

# -------------------------
# PRODUCT CREATION FLOW
# -------------------------

async def create_product(
    image_urls,
    store_id,
    product_name,
    MRP,
    application,
    material,
    auth_token
):
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
        # ---------- Upload Product Images ----------
        files = []
        for i, url in enumerate(image_urls):
            async with session.get(url) as response:
                if response.status == 200:
                    image_content = BytesIO(await response.read())
                    files.append(('images', (f'image_{i}.jpg', image_content, 'image/jpeg')))
                else:
                    print(f"Failed to download image from {url}")

        data = aiohttp.FormData()
        data.add_field('store_id', str(store_id))
        for field_name, file_tuple in files:
            filename, file_obj, content_type = file_tuple
            data.add_field(field_name, file_obj.getvalue(), filename=filename, content_type=content_type)

        async with session.post(f"{base_url}/bot/upload_image/", data=data, headers=headers) as response:
            upload_result = await response.json()

        # Extract product_id from upload response
        product_id = upload_result.get("product_id")
        if not product_id:
            return {"error": "Failed to get product_id from upload response", "upload_result": upload_result}

        # ---------- Generate Description ----------
        payload = {
            "product_id": product_id,
            "product_name": product_name,
            "mrp": MRP,
            "application": application,
            "material": material
        }
        async with session.post(f"{base_url}/bot/generate_description/", json=payload, headers=headers) as response:
            description_result = await response.json()

    return {
        "upload_result": upload_result,
        "description_result": description_result
    }

async def generate_ai_image_old(update, image_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "image_url": image_url,
        "generation_type": "both",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/ocr/generate_ai_images/", json=payload, headers=headers) as response:
            data = await response.json()

    job_id = data.get("job_id")
    if not job_id:
        return data

    # Schedule polling as background task (don't await here)
    asyncio.create_task(poll_image_generation(update, job_id, headers))
    return "Image generation started, user will be sent images when done."

import aiohttp
import traceback

async def generate_ai_image(update, auth_token, product_id, store_id, product_name, image_url):
    try:
        # Step 1: Call the API to generate the image
        try:
            completion = await client.chat.completions.create(
                model="google/gemini-2.5-flash-image-preview",
                modalities=["image", "text"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Product in the photo is {product_name}. Create a background for it showing it being used."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"{image_url}"
                                }
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            return f"Error during AI image generation API call: {str(e)}\n{traceback.format_exc()}"

        # Step 2: Extract Data URL
        try:
            data_url = completion.choices[0].message.images[0].get("image_url", {}).get("url")
            if not data_url:
                return "⚠️ AI image generation failed: No image returned."
        except Exception as e:
            return f"Error extracting Data URL: {str(e)}\n{traceback.format_exc()}"

        # Step 3: Convert Data URL to base64
        try:
            base64_str = data_url.split(",")[1]
        except Exception as e:
            return f"Error converting Data URL to Base64: {str(e)}\n{traceback.format_exc()}"

        # Step 4: Upload the AI image to your server
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            payload = {
                "product_id": product_id,
                "store_id": store_id,
                "generation_type": "ai",
                "base64_image": base64_str
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/bot/upload_ai_image/", json=payload, headers=headers) as response:
                    try:
                        data = await response.json()
                    except Exception:
                        return "Failed to upload AI image, ask user to retry"
            if response.status == 401 or (
                isinstance(data, dict)
                and data.get("code") == "token_not_valid"
            ):
                return "Authentication failed. Please re-authenticate."
            uploaded_image_url = data.get("ai_image_url")
            if not uploaded_image_url:
                return "No image URL returned from your server after upload."
        except Exception as e:
            return f"Error uploading AI image to server: {str(e)}\n{traceback.format_exc()}"

        await update.message.reply_photo(photo=uploaded_image_url, caption="✅ AI image generated successfully!")
        return "AI image generation completed and saved to product."

    except Exception as e:
        # Fallback for any unexpected errors
        return f"Unexpected error: {str(e)}\n{traceback.format_exc()}"

async def poll_image_generation(update, job_id, headers):
    # Step 2: Poll Every 30 Seconds Until Done
    tries = 40
    async with aiohttp.ClientSession() as session:
        while tries > 0:
            tries -= 1
            async with session.get(f"{base_url}/ocr/check_status/{job_id}/", headers=headers) as response:
                print(f"Polling for job {job_id}, tries left: {tries}")
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status")
                    result_image_urls = data.get("result_image_url", [])
                    error = data.get("error_message")
                    if status == "completed" and isinstance(result_image_urls, list):
                        # Send all available images
                        for image in result_image_urls:
                            image_type = image.get("type")
                            image_url = image.get("value")
                            if image_url and image_type:
                                caption = f"✅ {image_type.capitalize()} image generated!"
                                #process_llm(update, f"User has been sent the image: {image_type.capitalize()} ")
                                await update.message.reply_photo(photo=image_url, caption=caption)
                        break

                    elif error:
                        await update.message.reply_text(f"❌ AI image generation failed:\n{error}")
                        break

            await asyncio.sleep(30)

async def capture_store_details(store_id, store_name, address, whatsapp_number, instagram_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": store_name,
        "store_address_line_1": address,
        "whatsapp_number": whatsapp_number,
    }
    if instagram_id:
        payload["instagram_id"] = instagram_id
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{base_url}/apiv2/storefront/info/{store_id}/", json=payload, headers=headers) as response:
            return await response.json()

async def upload_store_images(store_id, image_urls, image_type, auth_token):
    files = []
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(image_urls):
            async with session.get(url) as response:
                if response.status == 200:
                    image_content = BytesIO(await response.read())
                    files.append(('file', (f'image_{i}.jpg', image_content, 'image/jpeg')))
                else:
                    print(f"Failed to download image from {url}")

        data = aiohttp.FormData()
        data.add_field('store_id', str(store_id))
        data.add_field('type', image_type)
        
        for field_name, file_tuple in files:
            filename, file_obj, content_type = file_tuple
            data.add_field(field_name, file_obj.getvalue(), filename=filename, content_type=content_type)

        async with session.put(f"{base_url}/apiv2/about_images/", data=data, headers=headers) as response:
            return await response.json()

async def capture_store_story(store_id, store_name, stories: dict, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "store_id": store_id,
        "store_name": store_name,
        "details": stories
    }

    async with aiohttp.ClientSession() as session:
        # First API call: generate store profile
        async with session.post(
            f"{base_url}/bot/generate_store_profile/",
            json=payload,
            headers=headers
        ) as response:
            profile_response = await response.json()
        # Second API call: update storefront info
        update_payload = {"is_storefront_exists": True}
        async with session.put(
            f"{base_url}/apiv2/storefront/info/{store_id}/",
            json=update_payload,
            headers=headers
        ) as update_response:
            update_result = await update_response.json()
        async with session.get(
            f"{base_url}/apiv2/storefront/get_info/{store_id}/",
            headers=headers
        ) as response:
            data = await response.json()
            storefront_link = f'development.fridayy.ai/{data.get("store_link")}/'
    return {"profile_response": profile_response, "update_result": update_result, "storefront_link": storefront_link}

async def get_storefront_link(store_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/apiv2/storefront/get_info/{store_id}/",
            headers=headers
        ) as response:
            data = await response.json()

            if data.get("is_storefront_exists"):
                storefront_link = f'development.fridayy.ai/{data.get("store_link")}/'
                return {"storefront_link": storefront_link}
            else:
                return {"storefront_link": None, "message": "Storefront does not exist yet, ask the user to set it up with reference flow."}

# -------------------------
# NEW: PRODUCT & STOREFRONT MANAGEMENT
# -------------------------

async def get_all_products(store_id, auth_token):
    """
    GET /ocr/get_all_products/?store_id={store_id}
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/ocr/get_all_products/",
            params={"store_id": str(store_id)},
            headers=headers
        ) as response:
            return await response.json()

async def get_product_by_id(product_id, auth_token):
    """
    GET /ocr/store/product/{product_id}
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/ocr/store/product/{product_id}",
            headers=headers
        ) as response:
            return await response.json()

async def get_storefront_details(store_id, auth_token):
    """
    GET /ocr/storefront/get_info/{store_id}
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/ocr/storefront/get_info/{store_id}",
            headers=headers
        ) as response:
            return await response.json()
        
async def update_product(
    product_id: int,
    auth_token: str,
    product_name: str = None,
    mrp: float = None,
    is_visible_in_storefront: bool = None,
    short_description: str = None,
    introduction: str = None,
    key_features: list = None,
    benefits_and_applications: list = None,
    inventory: int = None
):
    """
    PUT /ocr/store/product/{product_id}/
    Updates product fields. All params optional.
    """

    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {}

    if product_name is not None:
        payload["product_name"] = product_name
    if mrp is not None:
        payload["mrp"] = mrp
    if is_visible_in_storefront is not None:
        payload["is_visible_in_storefront"] = is_visible_in_storefront
    if short_description is not None:
        payload["short_description"] = short_description
    if introduction is not None:
        payload["introduction"] = introduction
    if key_features is not None:
        payload["key_features"] = key_features
    if benefits_and_applications is not None:
        payload["benefits_and_applications"] = benefits_and_applications
    if inventory is not None:
        payload["inventory"] = inventory

    async with aiohttp.ClientSession() as session:
        async with session.put(
            f"{base_url}/ocr/store/product/{product_id}/",
            json=payload,
            headers=headers
        ) as response:
            return await response.json()

async def update_storefront_info(store_id, storefront_payload, auth_token):
    """
    PUT /apiv2/storefront/info/{store_id}/
    Body: storefront payload (name, store_address_line_1, store_address_line_2, whatsapp_number, phone_number,
          instagram_id, description, email, about_store, what_we_do, etc.)
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.put(
            f"{base_url}/apiv2/storefront/info/{store_id}/",
            json=storefront_payload,
            headers=headers
        ) as response:
            return await response.json()

async def generate_product_edit_link(phone: str, product_id: int) -> str:
    """
    Generate one-click product edit link.
    
    Args:
        phone (str): Phone number linked to the store.
        product_id (int): Product ID to edit.
    
    Returns:
        str: One-click product edit link.
    """
    params = urlencode({"phone": phone, "productId": product_id})
    return f"https://development.fridayy.ai/edit/product?{params}"


async def generate_store_edit_link(phone: str) -> str:
    """
    Generate one-click store edit link.
    
    Args:
        phone (str): Phone number linked to the store.
    
    Returns:
        str: One-click store edit link.
    """
    params = urlencode({"phone": phone})
    return f"https://development.fridayy.ai/edit/store?{params}"

# -------------------------
# TOOL MAPPING
# -------------------------

TOOL_MAPPING = {
    "auth_vendor": auth_vendor,
    "create_store": create_store,
    "create_product": create_product,
    "generate_ai_image": generate_ai_image,
    "capture_store_details": capture_store_details,
    "upload_store_images": upload_store_images,
    "capture_store_story": capture_store_story,
    "get_storefront_link": get_storefront_link,
    "get_all_products": get_all_products,
    "get_product_by_id": get_product_by_id,
    "get_storefront_details": get_storefront_details,
    "update_product": update_product,
    "generate_product_edit_link": generate_product_edit_link,
    "generate_store_edit_link": generate_store_edit_link,
}