from django.shortcuts import render
from django.db import connection

from dashboard.models import Review


def home(request):

    search_query = request.GET.get(
        'q',
        ''
    ).strip()

    category_id = request.GET.get(
        'category',
        ''
    ).strip()


    categories = []
    products = []


    # =====================================================
    # GET REVIEW TABLE NAME
    # =====================================================

    review_table = Review._meta.db_table


    with connection.cursor() as cursor:

        # =================================================
        # GET CATEGORIES
        # =================================================

        cursor.execute("""
            SELECT
                id,
                category_name,
                description
            FROM categories
            ORDER BY category_name
        """)

        category_rows = cursor.fetchall()


        for row in category_rows:

            categories.append({

                'id': row[0],

                'category_name': row[1],

                'description': row[2],

            })


        # =================================================
        # BASE PRODUCT QUERY
        # =================================================

        base_query = f"""
            SELECT
                p.id,
                p.product_name,
                p.description,
                p.price,
                p.stock_quantity,
                p.product_image,
                c.id,
                c.category_name,

                COUNT(r.id) AS review_count,

                COALESCE(
                    AVG(r.rating),
                    0
                ) AS average_rating

            FROM products p

            INNER JOIN categories c
                ON p.category_id = c.id

            LEFT JOIN {review_table} r
                ON p.id = r.product_id
        """


        # =================================================
        # SEARCH
        # =================================================

        if search_query:

            cursor.execute(
                base_query
                + """
                WHERE
                    p.product_name LIKE %s
                    OR p.description LIKE %s
                    OR c.category_name LIKE %s

                GROUP BY
                    p.id,
                    p.product_name,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.product_image,
                    c.id,
                    c.category_name

                ORDER BY p.created_at DESC
                """,
                [

                    f'%{search_query}%',

                    f'%{search_query}%',

                    f'%{search_query}%'

                ]
            )


        # =================================================
        # CATEGORY
        # =================================================

        elif category_id:

            cursor.execute(
                base_query
                + """
                WHERE c.id = %s

                GROUP BY
                    p.id,
                    p.product_name,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.product_image,
                    c.id,
                    c.category_name

                ORDER BY p.created_at DESC
                """,
                [

                    category_id

                ]
            )


        # =================================================
        # ALL PRODUCTS
        # =================================================

        else:

            cursor.execute(
                base_query
                + """
                GROUP BY
                    p.id,
                    p.product_name,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.product_image,
                    c.id,
                    c.category_name

                ORDER BY p.created_at DESC

                LIMIT 12
                """
            )


        product_rows = cursor.fetchall()


        # =================================================
        # CONVERT PRODUCT ROWS
        # =================================================

        for row in product_rows:

            average_rating = float(
                row[9] or 0
            )

            review_count = int(
                row[8] or 0
            )


            products.append({

                'id': row[0],

                'product_name': row[1],

                'description': row[2],

                'price': row[3],

                'stock_quantity': row[4],

                'product_image': row[5],

                'category_id': row[6],

                'category_name': row[7],

                # REVIEW DATA
                'review_count': review_count,

                'average_rating': average_rating,

            })


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        'categories': categories,

        'products': products,

        'search_query': search_query,

        'selected_category': category_id,

    }


    return render(

        request,

        'home.html',

        context

    )