from django.shortcuts import render, redirect
from django.views import View
from django.db import connection
from django.http import JsonResponse
from datetime import date

# Create your views here.
class Dashboard(View):

    def get(self, request):

        user_id = request.session.get('user_id')

        if not user_id:
            return redirect('loginPage')

        try:

            today_str = date.today().strftime('%Y-%m-%d')

            # ✅ Fetch logged-in user
            with connection.cursor() as cursor:

                sql = """
                    SELECT *
                    FROM v2_test.registrationpage_userprofile
                    WHERE id = %s
                """

                cursor.execute(sql, [user_id])

                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()

            # ✅ No user found
            if not row:
                request.session.flush()
                return redirect('loginPage')

            user_dict = dict(zip(columns, row))

            with connection.cursor() as cursor:

                sql = """
                    SELECT name
                    FROM v2_test.client_master_v2
                    WHERE client_code = %s
                """

                cursor.execute(sql, [user_dict['client_code']])

                result = cursor.fetchone()

                if result:
                    user_dict['client_name'] = result[0]

            context = {
                'user': user_dict,
                'default_date':today_str
            }

            # ✅ Admin user
            with connection.cursor() as cursor:

                if user_dict.get('username', '').lower() == 'admin':

                    sql = """
                        SELECT client_code, name
                        FROM v2_test.client_master_v2
                        WHERE client_code != 0
                        AND LOWER(name) != 'admin';
                    """

                    cursor.execute(sql)

                    context['client_info'] = cursor.fetchall()
                    print(data for data in context)

                    context['is_admin'] = True
                # ✅ Normal user
                else:

                    sql = """
                        SELECT fact_code, factory_name
                        FROM v2_test.factory_master_v2
                        WHERE client_code = %s
                    """

                    cursor.execute(sql, [user_dict['client_code']])

                    context['factories'] = [
                        {
                            'fact_code': row[0],
                            'name': row[1]
                        }
                        for row in cursor.fetchall()
                    ]
                print(data for data in context)
            return render(request, "dashboard.html", context)

        except Exception as e:

            print("Dashboard Error:", e)

            request.session.flush()

            return redirect('loginPage')
    
    