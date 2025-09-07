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
            "name": "create_product",
            "description": "Create a new product by uploading images and generating a description. Requires a bearer auth token.",
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
                "product_name": {
                "type": "string",
                "description": "Name of the product"
                },
                "MRP": {
                "type": "number",
                "description": "Maximum retail price of the product"
                },
                "application": {
                "type": "string",
                "description": "Intended application or use of the product"
                },
                "material": {
                "type": "string",
                "description": "Material composition of the product"
                },
                "auth_token": {
                "type": "string",
                "description": "Bearer token for authentication"
                }
            },
            "required": ["image_urls", "store_id", "product_name", "MRP", "application", "material", "auth_token"]
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
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product"
                    }
                },
                "required": ["product_id", "store_id", "image_url", "product_name"]
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
            "description": "Update a product by ID. Only allows updating specific editable fields. Requires bearer auth.",
            "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                "type": "string",
                "description": "Product ID to update"
                },
                "auth_token": {
                "type": "string",
                "description": "Bearer token for authentication"
                },
                "product_name": {
                "type": "string",
                "description": "Name of the product"
                },
                "mrp": {
                "type": "number",
                "description": "Price of the product (MRP)"
                },
                "is_visible_in_storefront": {
                "type": "boolean",
                "description": "Whether the product is visible in the storefront"
                },
                "short_description": {
                "type": "string",
                "description": "Short description of the product"
                },
                "introduction": {
                "type": "string",
                "description": "Introduction or overview of the product"
                },
                "key_features": {
                "type": "array",
                "items": { "type": "string" },
                "description": "List of key features"
                },
                "benefits_and_applications": {
                "type": "array",
                "items": { "type": "string" },
                "description": "List of benefits and applications"
                },
                "inventory": {
                "type": "integer",
                "description": "Available inventory quantity"
                }
            },
            "required": ["product_id", "auth_token"]
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
    },
    {
        "type": "function",
        "function": {
        "name": "generate_product_edit_link",
        "description": "Generate a one-click link to edit a specific product in the store dashboard.",
        "parameters": {
            "type": "object",
            "properties": {
            "phone": {
                "type": "string",
                "description": "Phone number linked to the store."
            },
            "product_id": {
                "type": "integer",
                "description": "Product ID to edit."
            }
            },
            "required": ["phone", "product_id"]
        }
        }
    },
    {
        "type": "function",
        "function": {
        "name": "generate_store_edit_link",
        "description": "Generate a one-click link to edit the store details in the dashboard.",
        "parameters": {
            "type": "object",
            "properties": {
            "phone": {
                "type": "string",
                "description": "Phone number linked to the store."
            }
            },
            "required": ["phone"]
        }
        }
    },
]
