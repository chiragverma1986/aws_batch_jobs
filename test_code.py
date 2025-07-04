import os
import re
import sys
import math
import uuid
import json
import time
import boto3
import pyodbc
import random
import locale
import logging
import decimal
import teradata
import datetime
import calendar
import teradatasql
from datetime import date
from datetime import timedelta
from calendar import monthrange
from openpyxl import load_workbook
from email.mime.text import MIMEText
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import NoCredentialsError
from email.mime.application import MIMEApplication

def get_aws_params():
    
    try:
      env = os.environ["Environment"]
      secret = os.environ["TestSecret"]
    except KeyError as e:
      error_message = 'Required environment variables are missing {}'.format(e)
      raise Exception(error_message)

    parameters = {
        'env': env,
        'secret': secret
    }
    return parameters

def get_secret(secret_name):

  region_name = "us-west-2"
  session = boto3.session.Session()
  client = session.client(service_name='secretsmanager',region_name=region_name)
  get_secret_value_response = client.get_secret_value(SecretId=secret_name)
  return get_secret_value_response

# MAIL THE REPORT TO THE STAKEHOLDERS

def send_ses_email(sender_email, recipient_email_list, subject, email_body, attachment_files,file_names):
    
    """
        ##function sends email using SES given the required parameters.
        :param sender_email:
        :param recipient_email_list:
        :param subject:
        :param email_body:
        :param attachment_file:
        :return True/False:
    """

    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email_list
        msg_body = MIMEMultipart('alternative')
        textpart = MIMEText(email_body.encode('utf-8'), 'plain', 'utf-8')
        msg_body.attach(textpart)
        msg.attach(msg_body)

        for attachment_file, file_name in zip(attachment_files, file_names):
           with open(attachment_file, 'rb') as file:
            attachment = MIMEApplication(file.read(), Name=file_name)
            msg.attach(attachment)

        client = boto3.client('ses', region_name='us-west-2')
        response = client.send_raw_email(
            Source=sender_email,
            Destinations=recipient_email_list.split(','),
            RawMessage={'Data': msg.as_string(), }
        )
    except ClientError as e:
        return e
    else:
        text = response['MessageId']
        return text
    
def convert_date(input_date):

    if input_date == None:
      input_date =  datetime.now()
      print(input_date)
    currmonth = str(input_date)[:4]+str(input_date)[5:7]
    lastmonth =  int(str(input_date)[5:7])-1
    
    if lastmonth >=1 and lastmonth <=9 :
        peryrmonth =str(input_date)[:4]+'0'+str(lastmonth)
    elif lastmonth >=10 and lastmonth <=12 :
        peryrmonth =str(input_date)[:4]+str(lastmonth)
    elif lastmonth == 0:
        peryrmonth = str(int(str(input_date)[:4])-1)+'12'
    current_year = int(str(input_date)[:4])
    per_year = current_year-1
    current_month = int(str(input_date)[5:7])
    if current_month == 1:
        previous_month =12
    else:
        previous_month = int(str(input_date)[5:7]) -1
    thismonth=str(calendar.month_abbr[current_month]).upper() +"-"+str(input_date)[2:4]
    thismonth1=str(calendar.month_abbr[current_month]).upper() +"-"+str(input_date)[:4]
    
    if previous_month <10:
        previous_month = "0"+ str(previous_month)
        
    NoOfDays =  monthrange(int(str(current_year)), int(str(previous_month)))[1]
    
    if current_month ==1:
        lastmonthfirstday1 = str(per_year)+"-"+str(previous_month)+"-"+"01"
        lastmonthlastday1 = str(per_year)+"-"+str(previous_month)+"-"+ str(NoOfDays)
    else:
        lastmonthfirstday1 = str(current_year)+"-"+str(previous_month)+"-"+"01"
        lastmonthlastday1 = str(current_year)+"-"+str(previous_month)+"-"+ str(NoOfDays)
        
    return (currmonth,peryrmonth,lastmonthfirstday1,lastmonthlastday1,thismonth,thismonth1,per_year)

def generate(Start_Date,End_Date):
    
    try:
      arguments = json.loads(str(sys.argv[1]))
      Start_Date = arguments['Start_Date']
      End_Date = arguments['End_Date']
      Recipient_Email_List = arguments['Notified_To']
      Input_Start_Date = Start_Date
      Input_End_Date = End_Date
    except Exception as e:
      error_message = 'Required input dates are missing {}'.format(e)
      raise Exception(error_message)
    try:
      if Start_Date == "YYYY-MM-DD": 
         Start_Date = datetime.date.today()
      else:
         Start_Date = datetime.datetime.strptime(Start_Date, "%Y-%m-%d").date()
      # Get the first day of the month
      get_first_day_of_the_month = Start_Date.replace(day=1)
      # Get the last day of the month
      get_last_day_of_the_month = Start_Date.replace(day=calendar.monthrange(Start_Date.year, Start_Date.month)[1])

      Start_Date = get_first_day_of_the_month
      End_Date = get_last_day_of_the_month
      Input_Start_Date = Start_Date
      Input_End_Date = End_Date
    except ValueError as e:
      error_message = 'Invalid Date Format{}'.format(e)
      raise ValueError(e)
    try:
      test_secret = os.environ["TestSecret"]
      region_name = "us-west-2"
      params = get_aws_params()
      env = params['env']
      db_secret = get_secret(params['secret'])
      secret = json.loads(db_secret['SecretString'])
      recipient_email_address = secret['recipient_email_address']
      sender_email_address = secret['sender_email_address']

    except KeyError as e:
      error_message = 'Missing expected key in secret {}'.format(e)
      raise Exception(error_message)
    
    start_date = convert_date(Input_Start_Date)[0]
    peryrmont = convert_date(Input_Start_Date)[1]
    lastmonthfirstday1 = convert_date(Input_Start_Date)[2]
    
    try:
      get_edw_excel_file_path = "/tmp/test_report.xlsx"
    except Exception as e:
      error_message = 'Error running Report : {}'.format(e)
      raise Exception(error_message)
    try:
      # Sending email for reports
      subject = "Reports ".format(env=env.upper())
      sender_email = sender_email_address
      recipient_list = recipient_email_address
      recipient_email_list = Recipient_Email_List
      email_body = f'Hello Team, \n\n' + f'Please find the following attached Reports from "{Start_Date}" to "{End_Date}".\n\n' + f'1. Test Report\n\n' + f'Thanks\n' + f'Team'
      file_name = "Test Report_from_{from_date}_to_{to_date}.xlsx".format(from_date=Start_Date,to_date=End_Date)
      attachment_files = [get_excel_file_path] 
      file_names = [file_name]
      message_id = send_ses_email(sender_email, recipient_email_list, subject, email_body, attachment_files, file_names)
      if message_id:
        success_message = "Email sent successfully"
      else:
        error_message = "Email not sent successfully"
      # Return a structured response with execution status
      return {
            "status": "success",
            "message": "Report generation completed successfully."
        }
    except Exception as e:
      error_message = 'Report generation failed. Error: {}'.format(e)
      return {
            "status": "failure",
            "message": f"Report generation failed: {str(e)}"
        }
    

if __name__ == '__main__':
    
    # CREATING A LOGGER

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Batch] %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # UNIQUE ID TO IDENTIFY BATCH RUNS

    service = "test"
    service_id = uuid.uuid1().hex
    secret = os.environ["TestSecret"]
    region_name = "us-west-2"
    params = get_aws_params()
    env = params['env']
    test_secret = get_secret(params['secret'])
    secret = json.loads(test_secret['SecretString'])
    recipient_email_address = secret['recipient_email_address']
    sender_email_address = secret['sender_email_address']

    app_name = "reports-batch-{}".format(env)
    
    try:
          arguments = json.loads(str(sys.argv[1]))
          Start_Date = arguments['Start_Date']
          End_Date = arguments['End_Date']
          Recipient_Email_List = arguments['Notified_To']
    except Exception as e:
          error_message = 'Unexpected Error when getting the input parameters from batch job{}'.format(e)
          raise Exception(e)
    
    try:
      if Start_Date == "YYYY-MM-DD": 
         Start_Date = datetime.date.today()
      else:
         Start_Date = datetime.datetime.strptime(Start_Date, "%Y-%m-%d").date()
      # Get the first day of the month
      get_first_day_of_the_month = Start_Date.replace(day=1)
      # Get the last day of the month
      get_last_day_of_the_month = Start_Date.replace(day=calendar.monthrange(Start_Date.year, Start_Date.month)[1])

      Start_Date = get_first_day_of_the_month
      End_Date = get_last_day_of_the_month
    except ValueError as e:
      error_message = 'Invalid Date Format{}'.format(e)
      raise ValueError(e)

    generate(Start_Date,End_Date)
