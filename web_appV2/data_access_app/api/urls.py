from django.urls import path
from .views import DataRetrieve,RegisterApp, LoginUserAPI_APP, DataInsertUpdateDelete, DataRetrieveForGraph, GetDataByDate, DataByClientFactoryAndLine, GetLinesByFactoryAndClient, GetFactoriesByClientCodes, Logout, LoginUser, RegisterUser,Getsku_codeAndsku_nameByFactoryAndClient,GetLineNoAndBatchNoByFactoryAndClient,RegistrationMetadataAPI


# collection of api endpoints
urlpatterns = [
    path('data_retrieve/', DataRetrieve.as_view()),
    path('data_retrieve_for_graph/', DataRetrieveForGraph.as_view()),
    path('data_insert_update_delete/', DataInsertUpdateDelete.as_view()),
    path('data_insert_update_delete/<int:pk>/', DataInsertUpdateDelete.as_view()),
    path('data_retrieve_by_date/', GetDataByDate.as_view()),
    path('data_by_client_factory_and_line/', DataByClientFactoryAndLine.as_view()),
    path('lines_by_fact_and_client_code/', GetLinesByFactoryAndClient.as_view()),
    path('get-factory-by-client-code/', GetFactoriesByClientCodes.as_view()),
    path('logout/', Logout.as_view()),
    path('login/', LoginUser.as_view()),
    path('registeruser/', RegisterUser.as_view()),
    path('get-sku_code-and-sku_name/',Getsku_codeAndsku_nameByFactoryAndClient.as_view()),
    path('get-line_no-and-batch_no/',GetLineNoAndBatchNoByFactoryAndClient.as_view()),

    path('registration-metadata/', RegistrationMetadataAPI.as_view(), name='api_registration_metadata'),
    path('login_app/', LoginUserAPI_APP.as_view(), name='login_api'),
     path('registeruser_app/', RegisterApp.as_view()),
]