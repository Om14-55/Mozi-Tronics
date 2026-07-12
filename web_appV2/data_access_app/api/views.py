from django.db import connection
from datetime import datetime,date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import CWDataV2Serializer
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages

# Create your views here.
class Logout(APIView):

    def post(self, request):
        request.session.flush() 
        return redirect('loginPage')


class LoginUser(APIView):

    def post(self, request):
        login_username = request.POST.get('username')
        login_password = request.POST.get('password')

        with connection.cursor() as cursor:
            # 1. Fetch user data by username
            # We select id, password, and username to verify and set sessions
            sql = "SELECT id, username, password FROM v2_test.registrationpage_userprofile WHERE username = %s"
            cursor.execute(sql, [login_username])
            user_data = cursor.fetchone() # Returns a tuple or None

        # 2. Check if user exists
        if user_data:
            # user_data[0] = id, user_data[1] = username, user_data[2] = password
            db_id = user_data[0]
            db_username = user_data[1]
            db_password = user_data[2]

            # 3. Verify Password
            if check_password(login_password, db_password):
                request.session['user_id'] = db_id
                request.session['username'] = db_username
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid Password')
        else:
            messages.error(request, 'User does not exist')

        return redirect('loginPage')


class RegisterUser(APIView):
    
    def post(self, request):
        username = request.POST.get('username_register')
        email = request.POST.get('email_register')
        phoneNo = request.POST.get('phone_number')
        gender = request.POST.get('gender')
        password = request.POST.get('password1')
        password_confirm = request.POST.get('password2')
        client_code = request.POST.get('client_code')
        user_role = request.POST.get('user_role')

        if password != password_confirm:
            messages.error(request, "Passwords do not match!")
            return redirect('registrationPage')

        with connection.cursor() as cursor:
            # 1. Check if Username exists
            cursor.execute("SELECT id FROM v2_test.registrationpage_userprofile WHERE username = %s", [username])
            if cursor.fetchone():
                messages.error(request, "Username already taken.")
                return redirect('registrationPage')

            # 2. Check if Email exists
            cursor.execute("SELECT id FROM v2_test.registrationpage_userprofile WHERE email = %s", [email])
            if cursor.fetchone():
                messages.error(request, "Email already registered.")
                return redirect('registrationPage')

            # 3. Insert new user using Raw SQL
            # Note: We include client_code, fact_code, and user_role as they are your Primary Keys
            try:
                sql = """
                    INSERT INTO v2_test.registrationpage_userprofile 
                    (username, email, phone_number, gender, password, created_at, client_code, user_role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, [
                    username, 
                    email, 
                    phoneNo, 
                    gender, 
                    make_password(password), 
                    datetime.now(),
                    client_code,
                    user_role
                ])
            except Exception as e:
                messages.error(request, f"Database error: {str(e)}")
                return redirect('registrationPage')

        request.session.set_expiry(7*24*60*60)
        messages.success(request, "Registration successful! Please login.")
        return redirect('loginPage')


class GetFactoriesByClientCodes(APIView):

    def get(self, request):

        client_code = request.GET.get('client_code')

        if not client_code:
            return Response({
                "error": "client_code is required"
            }, status=400)
        
        try:

            with connection.cursor() as cursor:

                sql = """
                    SELECT fact_code, factory_name
                    FROM v2_test.factory_master_v2
                    WHERE client_code = %s
                """

                cursor.execute(sql, [client_code])

                factories = [
                    {
                        "fact_code": row[0],
                        "name": row[1]
                    }
                    for row in cursor.fetchall()
                ]

            return Response({
                "factories": factories
            })

        except Exception as e:

            print("Factory Fetch Error:", e)

            return Response({
                "error": "Something went wrong"
            }, status=500)
        

class GetLinesByFactoryAndClient(APIView):

    def get(self, request):
        client_code = request.query_params.get('client_code')
        factory_code = request.query_params.get('fact_code')

        if not client_code or not factory_code:
            return Response(
                {"error": "client_code and fact_code are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT line_no
                    FROM line_master_v2
                    WHERE client_code = %s AND fact_code = %s
                    ORDER BY line_no ASC
                """

                cursor.execute(query, (client_code, factory_code))

                lines = cursor.fetchall()

                data = [row[0] for row in lines]

                return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataRetrieve(APIView):

    def get(self, request):
        client_code = request.query_params.get('client_code')
        fact_code = request.query_params.get('fact_code')
        line_no = request.query_params.get('line_no', 'All') or 'All'
        limit = request.query_params.get('limit', 5)

        try:
            limit = int(limit)
            if limit <= 0:
                return Response({"error": "Limit must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Limit must be a whole number"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not all([client_code, fact_code, line_no]):
            return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Handle dynamic line filter
        line_filter = "AND line_no = %s" if line_no != "All" else ""
        
        with connection.cursor() as cursor:
            query = f"""
                SELECT 
                    sequence_id, dttime, weight, product_status, 
                    sku_name, client_code, sku_code, fact_code, 
                    line_no, batch_no 
                FROM cw_data_v2 
                WHERE client_code = %s AND fact_code = %s {line_filter} 
                ORDER BY sequence_id DESC LIMIT %s
            """
            
            # 2. Build parameter list dynamically
            query_params = [client_code, fact_code]
            if line_no != "All":
                query_params.append(line_no)
            query_params.append(limit) # Limit is always the last parameter

            cursor.execute(query, query_params)
            rows = cursor.fetchall()[::-1]

            data = [
                {
                    "sequence_id": row[0], "dttime": row[1], "weight": row[2], 
                    "product_status": row[3], "sku_name": row[4], "client_code": row[5], 
                    "sku_code": row[6], "fact_code": row[7], "line_no": row[8], "batch_no": row[9]
                } for row in rows
            ]
            return Response(data, status=status.HTTP_200_OK)

       
class DataRetrieveForGraph(APIView):

    def get(self, request):
        limit = request.query_params.get('limit', 5)
        client_code = request.query_params.get('client_code')
        fact_code = request.query_params.get('fact_code')
        line_no = request.query_params.get('line_no')
        
        line_filter = "AND cw.line_no = %s" if line_no != "All" else ""

        try:
            limit = int(limit)
        except ValueError:
            return Response({"error": "Limit must be a whole number"}, status=status.HTTP_400_BAD_REQUEST)
        
        if int(limit) < 0:
            return Response({"error": "Limit can not be a negative number"}, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            query = f"""
                SELECT 
                    cw.sequence_id, cw.dttime, cw.weight, cw.product_status, 
                    cw.sku_code, cw.sku_name, pm.thmin, pm.thmax 
                FROM cw_data_v2 cw
                LEFT JOIN product_master_v2 pm ON cw.sku_code = pm.sku_code
                WHERE cw.client_code = %s  AND cw.fact_code = %s {line_filter}
                ORDER BY cw.sequence_id DESC 
                LIMIT %s
            """

            query_params = [client_code, fact_code]
            if line_no != "All":
                query_params.append(line_no)
            query_params.append(limit)

            cursor.execute(query, query_params)
            rows = cursor.fetchall()[::-1]

            all_data_list = []
            for row in rows:
                all_data_list.append({
                    'sequence_id': row[0],
                    'date_time': row[1].strftime('%H:%M:%S') if row[1] else "N/A",
                    'weight': row[2],
                    'status': row[3],
                    'product_code': row[4],
                    'product_name': row[5],
                    'lower_threshold': row[6] if row[6] is not None else "N/A",
                    'upper_threshold': row[7] if row[7] is not None else "N/A",
                })
            
            return Response({'all_data': all_data_list}, status=status.HTTP_200_OK)
        

class DataInsertUpdateDelete(APIView):

    # def post(self, request):
    #     serializer = CWDataV2Serializer(data=request.data)
    #     if serializer.is_valid():
    #         weight = serializer.validated_data['weight'] 
    #         product_status = serializer.validated_data['product_status']
    #         sku_name = serializer.validated_data['sku_name']
    #         client_code = serializer.validated_data['client_code']
    #         sku_code = serializer.validated_data['sku_code']
    #         fact_code = serializer.validated_data['fact_code']
    #         line_no = serializer.validated_data['line_no']
    #         batch_no = serializer.validated_data['batch_no']

    #         with connection.cursor() as cursor:
    #             query = "INSERT INTO cw_data_v2 (dttime, weight, product_status, sku_name, client_code, sku_code, fact_code, line_no, batch_no) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)"
    #             cursor.execute(query, (weight, product_status, sku_name, client_code, sku_code, fact_code, line_no, batch_no))
    #             return Response({"message": "Data Inserted"}, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def get(self, request):
        serializer = CWDataV2Serializer(data=request.query_params)

        if serializer.is_valid():
            # print("serializer_valid,status",serializer.validated_data)
            weight = serializer.validated_data['weight'] 
            product_status = serializer.validated_data['product_status']
            sku_name = serializer.validated_data['sku_name']
            client_code = serializer.validated_data['client_code']
            sku_code = serializer.validated_data['sku_code']
            fact_code = serializer.validated_data['fact_code']
            line_no = serializer.validated_data['line_no']
            batch_no = serializer.validated_data['batch_no']
            current_time = serializer.validated_data['timestamp']
            # print(f"ALL DATA FETCHED --> weight: {weight}, product_status: {product_status}, sku_name: {sku_name}, client_code: {client_code}, sku_code: {sku_code}, fact_code: {fact_code}, line_no: {line_no}, batch_no: {batch_no}")

            with connection.cursor() as cursor:
                query = """
                    INSERT INTO cw_data_v2 
                    (dttime, weight, product_status, sku_name, client_code, sku_code, fact_code, line_no, batch_no) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    current_time, weight, product_status, sku_name, client_code,
                    sku_code, fact_code, line_no, batch_no
                ))

            return Response({"message": "Data Inserted"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def put(self, request, pk):
        serializer = CWDataV2Serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                query = "UPDATE cw_data_v2 SET weight=%s, product_status=%s, sku_name=%s, client_code=%s, sku_code=%s, fact_code=%s, line_no=%s, batch_no=%s WHERE sequence_id=%s"

                cursor.execute(query, (
                    data['weight'], data['product_status'], data['sku_name'], 
                    data['client_code'], data['sku_code'], data['fact_code'], 
                    data['line_no'], data['batch_no'], pk
                ))
                
                if cursor.rowcount == 0:
                    return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
                
                return Response({"message": "Data Updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM cw_data_v2 WHERE sequence_id=%s", [pk])
            
            if cursor.rowcount == 0:
                return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
                
            return Response({"message": "Data Deleted"}, status=status.HTTP_204_NO_CONTENT)
        

class GetDataByDate(APIView):

    def get(self, request, *args, **kwargs):
        search_date = request.GET.get('date_search')

        if not search_date:
            search_date = date.today().strftime("%Y-%m-%d")
            #return Response({'error': 'No date provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        cursor = connection.cursor()
        with cursor:
            query = "SELECT * FROM datewise_consolidated_table WHERE production_date = %s"
            cursor.execute(query, (search_date,))
                
            data_list_by_date = []
            rows = cursor.fetchall()

            if not rows:
                return Response({'data_by_date': [], 'message': 'No data found!'}, status=status.HTTP_200_OK)

            for row in rows:
                data_list_by_date.append({
                    'sequence_number': row[0],
                    'production_date': row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else row[1],
                    'product_code': row[2],
                    'total_passed_count': row[3],
                    'total_passed_weight': row[4],
                    'total_rejected_count': row[5],
                    'total_rejected_weight': row[6],
                    'total_count': row[7],
                    'total_weight': row[8] 
                })

        return Response({'data_by_date': data_list_by_date}, status=status.HTTP_200_OK)

    
class DataByClientFactoryAndLine(APIView):

    def get(self, request, *args, **kwargs):
        client_code = request.query_params.get('client_code')
        fact_code = request.query_params.get("fact_code")
        line_no = request.query_params.get("line_no")
        material_cost = 50

        if not all([client_code, fact_code, line_no]):
            return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

        line_filter = "AND line_no = %s" if line_no != "All" else ""

        target_query = f"""
            SELECT 
                SUM(production_target) AS production_target,
                SUM(cases_packed_target) AS cases_packed_target  
            FROM target_master_v2
            WHERE production_date = CURDATE() AND client_code = %s AND fact_code = %s {line_filter}
        """
        
        with connection.cursor() as cursor:
            params = [client_code, fact_code]
            if line_no != "All": params.append(line_no)
            
            cursor.execute(target_query, params)
            row = cursor.fetchone()
            target = int(row[0] or 0)
            cases_packed_target = int(row[1] or 0)

        data_query = f"""
            SELECT 
                SUM(total_count) AS production_today,
                GREATEST(0, ((%s - SUM(total_count)) * 100.0 / NULLIF(%s, 0))) AS below_target_percentage,
                SUM(total_rejected_count) * 100.0 / NULLIF(SUM(total_count), 0) AS line_rejection_rate,
                SUM(total_overweight) / 1000 AS total_overweight_in_kg,
                SUM(total_overweight) AS total_overweight_in_gm,
                (SUM(total_overweight) / 1000) * %s AS total_overweight_cost,
                SUM(total_overweight_count) AS total_overweight_unit,
                SUM(total_underweight_count) AS total_underweight_unit,
                SUM(total_passed_count) AS total_cases_packed
            FROM datewise_consolidated_table
            WHERE fact_code = %s {line_filter} AND production_date = CURDATE()
        """

        with connection.cursor() as cursor:
            data_params = [target, target, material_cost, fact_code]
            if line_no != "All": data_params.append(line_no)
            
            cursor.execute(data_query, data_params)
            row = cursor.fetchone()

            data = {
                "target": target,
                "cases_packed_target": cases_packed_target,
                "production_today": row[0] or 0,
                "below_target_percentage": round(float(row[1] or 0), 2),
                "line_rejection_rate": round(float(row[2] or 0), 2),
                "total_overweight_in_kg": round(float(row[3] or 0), 2),
                "total_overweight_in_gm": round(float(row[4] or 0), 2),
                "total_overweight_cost": round(float(row[5] or 0), 2),
                "total_overweight_unit": int(row[6] or 0),
                "total_underweight_unit": int(row[7] or 0),
                "total_cases_packed": int(row[8] or 0)
            }

        return Response(data, status=status.HTTP_200_OK)



# get sku_code and sku_name for simulator  and call in client_main.py 

# class Getsku_codeAndsku_nameByFactoryAndClient(APIView):

#     def get(self, request):
#         client_code = request.query_params.get('client_code')

#         if not client_code :
#             return Response(
#                 {"error": "client_code are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             with connection.cursor() as cursor:
#                 # FIX: Sorted by sku_code instead of line_no
#                 query = """
#                     SELECT sku_code, sku_name, thmin, thmax
#                     FROM product_master_v2
#                     WHERE client_code = %s 
#                     ORDER BY sku_code ASC
#                 """

#                 cursor.execute(query, (client_code))
#                 lines = cursor.fetchall()

#                 # FIX: Map both properties to a JSON-compatible dictionary array

#                 data = [row[0] for row in lines]

#                 return Response(data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class Getsku_codeAndsku_nameByFactoryAndClient(APIView):

    def get(self, request):
        client_code = request.query_params.get('client_code')

        if not client_code:
            return Response(
                {"error": "client_code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT sku_code, sku_name, thmin, thmax
                    FROM product_master_v2
                    WHERE client_code = %s 
                    ORDER BY sku_code ASC
                """
                # CRITICAL FIX: Pass query params as a tuple or list (client_code,)
                cursor.execute(query, (client_code,))
                products = cursor.fetchall()

                # CRITICAL FIX: Map all properties into a JSON-compatible dictionary array
                data = [
                    {
                        "sku_code": row[0],
                        "sku_name": row[1],
                        "thmin": float(row[2]) if row[2] is not None else 0.0,
                        "thmax": float(row[3]) if row[3] is not None else 0.0
                    }
                    for row in products
                ]

                return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# get line_no and batch_no for simulator and call in client_main.py 

class GetLineNoAndBatchNoByFactoryAndClient(APIView):

    def get(self, request):
        client_code = request.query_params.get('client_code')
        factory_code = request.query_params.get('fact_code')

        if not client_code or not factory_code:
            return Response(
                {"error": "client_code and fact_code are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT line_no, batch_no 
                    FROM batch_master_v2
                    WHERE client_code = %s AND fact_code = %s
                    ORDER BY line_no ASC
                """
                cursor.execute(query, (client_code, factory_code))
                lines = cursor.fetchall()

                # CRITICAL FIX: Package both line_no and batch_no into key-value pairs
                data = [
                    {
                        "line_no": row[0],
                        "batch_no": row[1]
                    }
                    for row in lines
                ]
                
                return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#################################################################################

# api of android app

###############################################################
#api for registeration meta data 
class RegistrationMetadataAPI(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            # 1. Fetch Clients
            cursor.execute("SELECT client_code, name FROM client_master_v2 ORDER BY client_code LIMIT 18446744073709551615 OFFSET 1")
            clients = cursor.fetchall()

            # 2. Fetch User Roles
            cursor.execute("SELECT user_role, role_details FROM role_master_v2 ORDER BY id ASC")
            roles = cursor.fetchall()

        # Safely extract values from the tuples (item[0] and item[1])
        client_list = [
            {"client_code": item[0], "name": item[1]} 
            for item in clients
        ]
        
        role_list = [
            {"user_role": item[0], "role_details": item[1]} 
            for item in roles
        ]

        # Use DRF's Response object
        return Response({
            "clients": client_list,
            "roles": role_list
        }, status=status.HTTP_200_OK)





class LoginUserAPI_APP(APIView):
    def post(self, request):
        login_username = request.data.get('username')
        login_password = request.data.get('password')

        if not login_username or not login_password:
            return Response({"success": False, "error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        username_clean = login_username.strip()

        with connection.cursor() as cursor:
            
            sql = """
                SELECT id, username, password, client_code 
                FROM v2_test.registrationpage_userprofile 
                WHERE LOWER(username) = LOWER(%s)
            """
            cursor.execute(sql, [username_clean])
            user_data = cursor.fetchone()

        if user_data:
            db_id = user_data[0]
            db_username = user_data[1]
            db_password = user_data[2]
            db_client_code = user_data[3]

            if check_password(login_password, db_password):
                all_clients = []  
                
                
                if db_username.lower() == 'admin' or db_client_code == 0:
                    user_role = "admin"
                    client_code = 0
                    client_name = "Admin Workspace"
                    
                   
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT client_code, name FROM v2_test.client_master_v2")
                        rows = cursor.fetchall()
                        all_clients = [{"client_code": row[0], "client_name": row[1]} for row in rows]
                
                
                else:
                    user_role = "client"
                    client_code = db_client_code if db_client_code is not None else 101
                    client_name = f"Client {client_code}"
                    
                
                    all_clients = [{
                        "client_code": client_code,
                        "client_name": client_name
                    }]

               
                return Response({
                    "success": True,
                    "message": "Login successful",
                    "user_id": db_id,
                    "username": db_username,
                    "user_role": user_role,
                    "client_code": client_code,  
                    "client_name": client_name,
                    "all_clients": all_clients   
                }, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "error": "Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"success": False, "error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)



class RegisterApp(APIView):

    def post(self, request):

        username = request.data.get("username")
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")
        gender = request.data.get("gender")
        password = request.data.get("password")
        client_code = request.data.get("client_code")
        user_role = request.data.get("user_role")

        if not username or not email or not password:
            return Response(
                {"message": "Username, Email and Password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM registrationpage_userprofile WHERE username=%s",
                [username]
            )

            if cursor.fetchone():
                return Response(
                    {"message": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cursor.execute(
                """
                INSERT INTO registrationpage_userprofile
                (username,email,phone_number,gender,password,created_at,client_code,user_role)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    username,
                    email,
                    phone_number,
                    gender,
                    make_password(password),
                    datetime.now(),
                    client_code,
                    user_role
                ]
            )

        return Response(
            {"message": "Registration Successful"},
            status=status.HTTP_201_CREATED
        )