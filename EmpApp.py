from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import logging
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion


output = {}
table = 'employee'

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

@app.route("/", methods=['GET', 'POST'])
def home():
    db_conn = connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )
    cursor = db_conn.cursor()
    cursor.execute("select * from employee")
    data = cursor.fetchall()  # data from database
    return render_template('ViewSummary.html', value=data)

@app.route("/showaddemp", methods=['GET', 'POST'])
def showaddemp():
    db_conn = connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )
    return render_template('AddEmp.html')

@app.route("/showsummary", methods=['GET', 'POST'])
def showsummary():
    db_conn = connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )
    cursor = db_conn.cursor()
    cursor.execute("select * from employee")
    data = cursor.fetchall()  # data from database
    return render_template('ViewSummary.html', value=data)
    # return render_template('ViewSummary.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    db_conn = connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )
    fmno = request.form['fmno']
    name = request.form['name']
    contact = request.form['contact']
    team = request.form['team']
    location = request.form['location']
    certification = request.form['certification']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    if emp_image_file.filename == "":
       return "Please select a file"

    try:

        cursor.execute(insert_sql, (fmno, name,contact, team, location, certification))
        db_conn.commit()
        # # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "fmno-" + str(fmno) + "_image_file"
        s3 = boto3.resource('s3')

        try:
             print("Data inserted in MySQL RDS... uploading image to S3...")
             s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
             bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
             s3_location = (bucket_location['LocationConstraint'])

             if s3_location is None:
                 s3_location = ''
             else:
                 s3_location = '-' + s3_location

             object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                 s3_location,
                 custombucket,
                 emp_image_file_name_in_s3)

        except Exception as e:
             return str(e)


    except Exception as e:
        print(e)
        logging.info(msg=e);

    finally:
        print("finally")

    cursor.execute("select * from employee")
    data = cursor.fetchall()  # data from database
    return render_template('ViewSummary.html', value=data)
####
@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("GetEmp.html")


@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    fmno = request.form['fmno']

    output = {}
    select_sql = "SELECT fmno, name, contact, team, location from employee where fmno=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql,(fmno))
        result = cursor.fetchone()

        output["fmno"] = result[0]
        print('EVERYTHING IS FINE TILL HERE')
        output["name"] = result[1]
        output["contact"] = result[2]
        output["team"] = result[3]
        output["location"] = result[4]
        print(output["fmno"])
        dynamodb_client = boto3.client('dynamodb', region_name=customregion)
        try:
            response = dynamodb_client.get_item(
                TableName= customtable ,
                Key={
                    'empid': {
                        'N': str(emp_id)
                    }
                }
            )
            pdf_url = response['Item']['pdf_url']['S']

        except Exception as e:
            program_msg = "Flask could not update DynamoDB table with S3 object URL"
            return render_template('addemperror.html', errmsg1=program_msg, errmsg2=e)

    except Exception as e:
        print(e)

    finally:
        cursor.close()

    return render_template("GetEmpOutput.html", fmno=output["fmno"], name=output["name"],
                           contact=output["contact"], team=output["team"], location=output["location"],
                           pdf_url=pdf_url)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
