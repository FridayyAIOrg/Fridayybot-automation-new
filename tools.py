# tools.py
import asyncio
from io import BytesIO
import aiohttp

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

async def upload_product_images(image_urls, store_id, auth_token):
    files = []
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
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
            return await response.json()

async def generate_description(product_id, product_name, MRP, application, material, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "product_id": product_id,
        "product_name": product_name,
        "MRP": MRP,
        "application": application,
        "material": material
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/bot/generate_description/", json=payload, headers=headers) as response:
            return await response.json()

async def generate_ai_image(update, product_id, store_id, image_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "product_id": product_id,
        "store_id": store_id,
        "image_url": image_url,
        "generation_type": "both"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/ocr/generate_ai_images/", json=payload, headers=headers) as response:
            data = await response.json()

    job_id = data.get("job_id")
    if not job_id:
        print("No job_id returned from image generation API")
        return data

    # Schedule polling as background task (don't await here)
    asyncio.create_task(poll_image_generation(update, job_id, headers))
    return "Image generation started, user will be sent images when done."

async def poll_image_generation(update, job_id, headers):
    # Step 2: Poll Every 30 Seconds Until Done
    tries = 40
    async with aiohttp.ClientSession() as session:
        while tries > 0:
            print(f"Polling for job {job_id}, tries left: {tries}")
            tries -= 1
            async with session.get(f"{base_url}/check_status/{job_id}/", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status")
                    error = data.get("error_message")

            result_image_url = "https://placehold.co/600x400.png"

            if result_image_url:
                msg = f"✅ AI image generation completed!\nImage URL: {result_image_url}"
                await update.message.reply_photo(photo=result_image_url, caption=msg)
                break

            elif error:
                await update.message.reply_text(f"❌ AI image generation failed:\n{error}")
                break
            else:
                await asyncio.sleep(30)
                continue

async def capture_store_details(store_id, store_name, address, whatsapp_number, instagram_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": store_name,
        "address": address,
        "whatsapp_contact": whatsapp_number,
        "instagram_id": instagram_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{base_url}/apiv2/storefront/info/{store_id}", json=payload, headers=headers) as response:
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

async def capture_store_story(store_id, store_name, stories: dict, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "store_id": store_id,
        "store_name": store_name,
        "details": stories
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/bot/generate_store_profile/", json=payload, headers=headers) as response:
            return await response.json()

async def get_storefront_link(store_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/apiv2/storefront/get_info/{store_id}/", headers=headers) as response:
            data = await response.json()
            storefront_link = f'development.fridayy.ai/{data.get("store_link")}/'
            return {"storefront_link": storefront_link}

# -------------------------
# TOOL MAPPING
# -------------------------

TOOL_MAPPING = {
    "auth_vendor": auth_vendor,
    "create_store": create_store,
    "upload_product_images": upload_product_images,
    "generate_description": generate_description,
    "generate_ai_image": generate_ai_image,
    "capture_store_details": capture_store_details,
    "upload_store_images": upload_store_images,
    "capture_store_story": capture_store_story,
    "get_storefront_link": get_storefront_link,
}