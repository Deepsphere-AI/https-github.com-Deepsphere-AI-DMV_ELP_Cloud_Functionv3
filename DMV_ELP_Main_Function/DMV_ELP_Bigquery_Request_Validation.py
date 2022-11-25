"""

-----------------------------------------------------------------------------------------------------------------------------------------------------

© Copyright 2022, California, Department of Motor Vehicle, all rights reserved.
The source code and all its associated artifacts belong to the California Department of Motor Vehicle (CA, DMV), and no one has any ownership
and control over this source code and its belongings. Any attempt to copy the source code or repurpose the source code and lead to criminal
prosecution. Don't hesitate to contact DMV for further information on this copyright statement.

Release Notes and Development Platform:
The source code was developed on the Google Cloud platform using Google Cloud Functions serverless computing architecture. The Cloud
Functions gen 2 version automatically deploys the cloud function on Google Cloud Run as a service under the same name as the Cloud
Functions. The initial version of this code was created to quickly demonstrate the role of MLOps in the ELP process and to create an MVP. Later,
this code will be optimized, and Python OOP concepts will be introduced to increase the code reusability and efficiency.
____________________________________________________________________________________________________________
Development Platform                | Developer       | Reviewer   | Release  | Version  | Date
____________________________________|_________________|____________|__________|__________|__________________
Google Cloud Serverless Computing   | DMV Consultant  | Ajay Gupta | Initial  | 1.0      | 09/18/2022

-----------------------------------------------------------------------------------------------------------------------------------------------------

"""

from google.cloud import bigquery
import pandas as pd
import datetime
import os


def GetCurrentDateRequestCount():
    vAR_client = bigquery.Client()
    vAR_table_name = "DMV_ELP_REQUEST"
    vAR_query_job = vAR_client.query(
        " SELECT count(1) as cnt FROM "+ "`"+os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_table_name+"`"+  " where date(created_dt) = current_date() "
    )

    vAR_results = vAR_query_job.result()  # Waits for job to complete.
    print('Current Date Request Count - ',vAR_results)
    for row in vAR_results:
        vAR_request_count = row.get('cnt')
    return vAR_request_count


def ReadNotProcessedRequestData():
    vAR_client = bigquery.Client()
    vAR_request_table_name = "DMV_ELP_REQUEST"
    vAR_response_table_name = "DMV_ELP_MLOPS_RESPONSE"
    vAR_sql =(
        "select * from `"+ os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_request_table_name+"`"+" where LICENSE_PLATE_CONFIG not in (select LICENSE_PLATE_CONFIG from `" +os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_response_table_name+"`"+" where date(created_dt) = current_date() group by LICENSE_PLATE_CONFIG,RUN_ID having RUN_ID=max(RUN_ID)) and date(created_dt)=current_date() order by REQUEST_ID"
    )

    vAR_df = vAR_client.query(vAR_sql).to_dataframe()
    return vAR_df


def InsertRequesResponseMetaData(vAR_number_of_configuration,vAR_max_plate_desc_count,vAR_s3_url):
   vAR_df = pd.DataFrame()
   vAR_rownum = 1
   if GetMetadatarownum() is not None:
      if GetMetadatarownum()>0:
         vAR_df['ROWNUM'] = 1*[vAR_rownum+1]
   else:
      vAR_df['ROWNUM'] = 1*[vAR_rownum]
   vAR_df['TOTAL_NUMBER_OF_ORDERS'] = 1*[vAR_number_of_configuration]
   vAR_df['CREATED_DT'] = 1*[datetime.datetime.utcnow()]
   vAR_df['CREATED_USER'] = 1*[os.environ["GCP_USER"]]
   vAR_df['REQUEST_FILE_NAME'] = 1*[vAR_s3_url]
   vAR_df['MAX_PLATE_TYPE_DESC_COUNT'] = 1*[vAR_max_plate_desc_count]
   client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])

   # Define table name, in format dataset.table_name
   table = os.environ["GCP_BQ_SCHEMA_NAME"]+'.DMV_ELP_REQUEST_RESPONSE_METADATA'
   job_config = bigquery.LoadJobConfig(autodetect=True,write_disposition="WRITE_APPEND",)
   job = client.load_table_from_dataframe(vAR_df, table,job_config=job_config)

   job.result()  # Wait for the job to complete.
   table_id = os.environ["GCP_PROJECT_ID"]+'.'+table
   table = client.get_table(table_id)  # Make an API request.
   print(
         "Loaded {} rows and {} columns to {}".format(
               table.num_rows, len(table.schema), table_id
         )
      )
   

def GetMetadatarownum():
    vAR_client = bigquery.Client()
    vAR_table_name = "DMV_ELP_REQUEST_RESPONSE_METADATA"
    vAR_query_job = vAR_client.query(
        " SELECT max(ROWNUM) as rownumber FROM `"+os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_table_name+"`"
    )

    vAR_results = vAR_query_job.result()  # Waits for job to complete.
    print('Current Date Request Count - ',vAR_results)
    for row in vAR_results:
        vAR_request_count = row.get('rownumber')
    return vAR_request_count


def GetCurrentDateResponseCount():
    vAR_response_count = 0
    vAR_client = bigquery.Client()
    vAR_table_name = "DMV_ELP_MLOPS_RESPONSE"
    vAR_query_job = vAR_client.query(
        " SELECT count(1) as cnt,RUN_ID FROM "+ "`"+os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_table_name+"`"+  " where date(created_dt) = current_date() group by RUN_ID having RUN_ID=max(RUN_ID)  order by RUN_ID desc limit 1 "
    )

    vAR_results = vAR_query_job.result()  # Waits for job to complete.
    print('Total number of processed records - ',vAR_results)
    for row in vAR_results:
        vAR_response_count = row.get('cnt')
    return vAR_response_count

def GetMetadataTotalRecordsToProcess():
    vAR_client = bigquery.Client()
    vAR_table_name = "DMV_ELP_REQUEST_RESPONSE_METADATA"
    vAR_query_job = vAR_client.query(
        " SELECT TOTAL_NUMBER_OF_ORDERS FROM `"+os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_table_name+"`" + " where date(created_dt) = current_date() order by CREATED_DT desc limit 1"
    )

    vAR_results = vAR_query_job.result()  # Waits for job to complete.
    for row in vAR_results:
        vAR_total_orders = row.get('TOTAL_NUMBER_OF_ORDERS')
    return vAR_total_orders


def GetRequestFileName():
    vAR_client = bigquery.Client()
    vAR_table_name = "DMV_ELP_REQUEST_RESPONSE_METADATA"
    vAR_query_job = vAR_client.query(
        " SELECT REQUEST_FILE_NAME FROM `"+os.environ["GCP_PROJECT_ID"]+"."+os.environ["GCP_BQ_SCHEMA_NAME"]+"."+vAR_table_name+"`" + " where date(created_dt) = current_date() order by CREATED_DT desc limit 1"
    )

    vAR_results = vAR_query_job.result()  # Waits for job to complete.
    for row in vAR_results:
        vAR_request_file_name = row.get('REQUEST_FILE_NAME')
    return vAR_request_file_name