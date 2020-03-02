# Airflow Project
## AWS Configuration
### Create new AWS User & IAM Role
1. Create IAM User, this user Access key ID & Secret access key will be used in Airflow Admin Connections ```bks_airflow_rs_user```

2. Create IAM Role ( myRedshiftRole )
    * ARN : arn:aws:iam::416729034818:user/bks_airflow_rs_user
    * Attach policies (Read only access would be OK but tested with full access)
        * AmazonRedshiftFullAccess  
        * AmazonS3FullAccess                  

### Create Redshift Cluster (Tested access using SQL Workbench)
* Create Redshift Cluster ( Click Quick Launch Cluster )
    * Cluster Name : redshift-cluster-1
    * Node Type : dc2.large
    * Nodes : 2
    * Zone : us-west-2d
    * Endpoint : redshift-cluster-1.cspd8jlneitf.us-west-2.redshift.amazonaws.com:5439/dev
    * Port : 5439
    * Database Name : udacity
    * User : awsuser
    * Password : <>
    * Network : vpc-0d76e975
    * VPC Security Group: <> group name: redshift_security_group Inbound: Redshift/TCP/5439/0.0.0.0/0 (For testing else whitewash IPrange)
    * Publicly accessible: Yes
    

## Start Airflow
* Start Project Workspace and  use below command to start Airflow ```/opt/airflow/start.sh```
Airflow -> Admin -> Connections. Create two new connections. 
    * aws-creditials - IAM User (Access key ID/Token as username and password)
    * redshift - Database user & password
    
* Run DAG
