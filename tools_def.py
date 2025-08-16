# tools_def.py
tools = [
    {
        "type": "function",
        "function": {
            "name": "auth_vendor",
            "description": "Authenticate a vendor using their phone number",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_no": {"type": "string"}
                },
                "required": ["phone_no"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_store",
            "description": "Create a store for the vendor based on business categories. A store must not be created without user's explicit confirmation of category selection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "Animals & Pet Supplies", "Apparel & Accessories", "Arts & Entertainment",
                                "Baby & Toddler", "Bundles", "Business & Industrial", "Cameras & Optics",
                                "Electronics", "Food, Beverages & Tobacco", "Furniture", "Gift Cards",
                                "Hardware", "Health & Beauty", "Home & Garden", "Luggage & Bags", "Mature",
                                "Media", "Office Supplies", "Product Add-Ons", "Religious & Ceremonial",
                                "Services", "Software", "Sporting Goods", "Toys & Games", "Uncategorized",
                                "Vehicles & Parts"
                            ]
                        }
                    },
                    "token": {"type": "string"}
                },
                "required": ["categories", "token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_product_images",
            "description": "Upload product images from Telegram URLs to the server. Requires a bearer auth token.",
            "parameters": {
                "type": "object",
                "properties": {
                "image_urls": {
                    "type": "array",
                    "items": { "type": "string" },
                    "maxItems": 2,
                    "description": "Image URLs (e.g., from Telegram) to be uploaded"
                },
                "store_id": {
                    "type": "string",
                    "description": "The store ID to associate the images with"
                },
                "auth_token": {
                    "type": "string",
                    "description": "Bearer token for authentication"
                }
                },
                "required": ["image_urls", "store_id", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_description",
            "description": "Generate the product description using product details. Requires a bearer auth token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": { "type": "string" },
                    "product_name": { "type": "string" },
                    "MRP": { "type": "number" },
                    "application": { "type": "string" },
                    "material": { "type": "string" },
                    "auth_token": {
                    "type": "string",
                    "description": "Bearer token for authentication"
                    }
                },
                "required": ["product_id", "product_name", "MRP", "application", "material", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ai_image",
            "description": "Generate AI-enhanced images for a product. It triggers the job and notifies the user asynchronously once done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The unique ID of the product to generate images for"
                    },
                    "store_id": {
                        "type": "string",
                        "description": "The store ID that the product belongs to"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "URL of the input image to enhance"
                    },
                    "auth_token": {
                        "type": "string",
                        "description": "Bearer token for authentication"
                    }
                },
                "required": ["product_id", "store_id", "image_url", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_store_details",
            "description": "Capture store name, address, WhatsApp number, and Instagram ID. Requires store_id and auth_token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string" },
                    "store_name": { "type": "string" },
                    "address": { "type": "string" },
                    "whatsapp_number": { "type": "string" },
                    "instagram_id": { "type": "string" },
                    "auth_token": { "type": "string" }
                },
                "required": ["store_name", "store_id", "address", "whatsapp_number", "instagram_id", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_store_images",
            "description": "Upload workspace/process images. Requires image URLs, store_id, and auth_token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string" },
                    "image_urls": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "image_type": {
                        "type": "string",
                        "enum": ["about", "what_we_do"]
                    },
                    "auth_token": { "type": "string" }
                },
                "required": ["store_id", "image_urls", "image_type" "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_store_story",
            "description": "Capture the user’s story details about their process and challenges. Requires store_id, stories (a dict of 3 story types), and auth_token.",
            "parameters": {
            "type": "object",
            "properties": {
                "store_id": { "type": "string" },
                "store_name": { "type": "string" },
                "stories": {
                "type": "object",
                "description": "A mapping of story types to story texts.",
                "properties": {
                    "process_speciality": { "type": "string" },
                    "time_for_one_product": { "type": "string" },
                    "challenges": { "type": "string" }
                },
                "required": ["process_speciality", "time_for_one_product", "challenges"]
                },
                "auth_token": { "type": "string" }
            },
            "required": ["store_id", "store_name", "stories", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_storefront_link",
            "description": "Get the public storefront link for the user to share.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string" },
                    "auth_token": { "type": "string" }
                },
                "required": ["store_id", "auth_token"]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "get_all_products",
            "description": "Fetch all products for a given store. Requires bearer auth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string", "description": "Store ID" },
                    "auth_token": { "type": "string", "description": "Bearer token" }
                },
                "required": ["store_id", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_product",
            "description": "Update a product by ID using a full product payload. Requires bearer auth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": { "type": "string", "description": "Product ID to update" },
                    "product_payload": {
                        "type": "object",
                        "description": "Full product object to PUT (fields like product_info, product_name, mrp, images, visibility, descriptions, features, etc.)"
                    },
                    "auth_token": { "type": "string", "description": "Bearer token" }
                },
                "required": ["product_id", "product_payload", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_storefront_info",
            "description": "Update storefront info (name, address lines, phones, instagram_id, description, email, about_store, what_we_do, etc.). Requires bearer auth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string", "description": "Store ID" },
                    "storefront_payload": {
                        "type": "object",
                        "description": "Full storefront info object to PUT"
                    },
                    "auth_token": { "type": "string", "description": "Bearer token" }
                },
                "required": ["store_id", "storefront_payload", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_storefront_details",
            "description": "Fetch detailed storefront info for a given store. Requires bearer auth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": { "type": "string", "description": "Store ID" },
                    "auth_token": { "type": "string", "description": "Bearer token" }
                },
                "required": ["store_id", "auth_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_by_id",
            "description": "Get all product details by id. Requires bearer auth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": { "type": "string", "description": "Product ID to update" },
                    "auth_token": { "type": "string", "description": "Bearer token" }
                },
                "required": ["product_id", "auth_token"]
            }
        }
    }
]
