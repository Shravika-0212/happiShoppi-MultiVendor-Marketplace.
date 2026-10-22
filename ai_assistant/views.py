import os

from django.shortcuts import render
from django.http import JsonResponse

from dotenv import load_dotenv
from google import genai

from dashboard.models import Product, Category


load_dotenv()


# =========================================================
# AI ASSISTANT PAGE
# =========================================================

def ai_assistant(request):

    return render(
        request,
        'ai_assistant/ai_chat.html'
    )


# =========================================================
# SEARCH HAPPISHOPPI PRODUCTS
# =========================================================

def search_products(message):

    message_lower = message.lower()

    products = Product.objects.select_related(
        'category'
    ).all()

    results = []


    # =====================================================
    # CHECK PRICE
    # =====================================================

    max_price = None

    words = message_lower.split()

    for i in range(len(words)):

        if words[i] in [
            "under",
            "below",
            "upto"
        ]:

            if i + 1 < len(words):

                price_text = words[i + 1]

                price_text = price_text.replace(
                    "₹",
                    ""
                )

                try:

                    max_price = float(
                        price_text
                    )

                except ValueError:

                    pass


    # =====================================================
    # CHECK CATEGORY
    # =====================================================

    category_name = None

    categories = Category.objects.all()


    for category in categories:

        category_text = (
            category.category_name.lower()
        )


        # Exact category name
        if category_text in message_lower:

            category_name = (
                category.category_name
            )

            break


        # Electronics variations
        if category_text == "electronics":

            if (
                "electronic" in message_lower
                or "electronics" in message_lower
            ):

                category_name = (
                    category.category_name
                )

                break


    # =====================================================
    # FILTER PRODUCTS
    # =====================================================

    for product in products:


        # -------------------------------------------------
        # CATEGORY FILTER
        # -------------------------------------------------

        if category_name:

            if (
                product.category.category_name
                != category_name
            ):

                continue


        # -------------------------------------------------
        # PRICE FILTER
        # -------------------------------------------------

        if max_price is not None:

            if float(product.price) > max_price:

                continue


        results.append(product)


    return results


# =========================================================
# AI CHAT
# =========================================================

def ai_chat(request):

    if request.method != 'POST':

        return JsonResponse({

            'response':
                'Invalid request.'

        })


    message = request.POST.get(
        'message',
        ''
    ).strip()


    if not message:

        return JsonResponse({

            'response':
                'Please enter a message.'

        })


    message_lower = message.lower()


    # =====================================================
    # SIMPLE GREETINGS
    # =====================================================

    greetings = [

        'hi',
        'hello',
        'hey',
        'hii',
        'hiii',
        'good morning',
        'good afternoon',
        'good evening'

    ]


    if message_lower in greetings:

        return JsonResponse({

            'response':
                "Hello! 👋 Welcome to happiShoppi. "
                "How can I help you with your shopping today?"

        })


    # =====================================================
    # SEARCH HAPPISHOPPI PRODUCTS
    # =====================================================

    products = search_products(
        message
    )


    # =====================================================
    # PRODUCT COUNT
    # =====================================================

    if (
        "how many" in message_lower
        and "product" in message_lower
    ):

        count = len(products)


        if count == 0:

            return JsonResponse({

                'response':
                    "Sorry, I couldn't find any "
                    "matching products on happiShoppi."

            })


        return JsonResponse({

            'response':
                f"There are {count} matching "
                f"products available on happiShoppi."

        })


    # =====================================================
    # CHECK IF THIS IS A PRODUCT QUESTION
    # =====================================================

    product_words = [

        'product',
        'products',
        'item',
        'items',

        'electronic',
        'electronics',

        'wear',

        'shirt',
        'shirts',

        'saree',
        'sarees',

        'kurti',
        'kurtis',

        'laptop',
        'laptops',

        'phone',
        'phones',

        'mobile',
        'mobiles',

        'shoes',
        'shoe',

        'footwear',

        'beauty',

        'accessories',
        'accessory'

    ]


    is_product_question = False


    for word in product_words:

        if word in message_lower:

            is_product_question = True

            break


    # =====================================================
    # RETURN PRODUCT DATA DIRECTLY
    # =====================================================

    if is_product_question:


        if not products:

            return JsonResponse({

                'response':
                    "Sorry, I couldn't find a matching "
                    "product on happiShoppi."

            })


        response_text = (
            "Here are the products I found on "
            "happiShoppi:\n\n"
        )


        for product in products[:10]:

            response_text += (

                f"• {product.product_name}\n"

                f"  Category: "
                f"{product.category.category_name}\n"

                f"  Price: ₹{product.price}\n"

                f"  Stock: "
                f"{product.stock_quantity}\n\n"

            )


        return JsonResponse({

            'response':
                response_text

        })


    # =====================================================
    # GEMINI API KEY
    # =====================================================

    api_key = os.getenv(
        'GEMINI_API_KEY'
    )


    if not api_key:

        return JsonResponse({

            'response':
                'AI service is not configured. '
                'Please check the API key.'

        })


    try:

        # =================================================
        # CONNECT TO GEMINI
        # =================================================

        client = genai.Client(

            api_key=api_key

        )


        # =================================================
        # GET LIMITED PRODUCT DATA
        # =================================================

        all_products = (
            Product.objects
            .select_related('category')
            .all()[:20]
        )


        product_data = []


        for product in all_products:

            product_data.append(

                f"""
Product Name: {product.product_name}
Category: {product.category.category_name}
Description: {product.description}
Price: ₹{product.price}
Stock: {product.stock_quantity}
"""

            )


        products_text = "\n".join(
            product_data
        )


        # =================================================
        # AI PROMPT
        # =================================================

        prompt = f"""
You are happiShoppi AI Assistant.

You are a friendly shopping assistant for the
happiShoppi multi-vendor e-commerce website.

Here is some actual happiShoppi product data:

{products_text}

Customer message:

{message}

Rules:

1. Be friendly and helpful.

2. Use happiShoppi product data when relevant.

3. Never invent happiShoppi products.

4. Use ₹ for prices.

5. Keep your answer short and easy to understand.

6. If the customer is just chatting, respond naturally.

7. If the customer asks about a product that is not
available in the provided data, clearly say that
you could not find it on happiShoppi.
"""


        # =================================================
        # SEND MESSAGE TO GEMINI
        # =================================================

        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt

        )


        ai_response = response.text


        return JsonResponse({

            'response':
                ai_response

        })


    except Exception as error:

        print("=" * 50)

        print("GEMINI ERROR:")

        print(error)

        print("=" * 50)


        return JsonResponse({

            'response':
                'Sorry, the AI service is temporarily '
                'unavailable. Please try again.'

        })