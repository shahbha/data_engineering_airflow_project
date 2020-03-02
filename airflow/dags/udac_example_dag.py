from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator
from load_dim_subdag import load_dim_table_dag
from airflow.operators import (StageToRedshiftOperator, LoadFactOperator,
                                LoadDimensionOperator, DataQualityOperator)
from helpers import SqlQueries
from helpers import CreateTables


# AWS_KEY = os.environ.get('AWS_KEY')
# AWS_SECRET = os.environ.get('AWS_SECRET')

default_args = {
    'owner': 'udacity',
    'start_date': datetime(2020, 2, 29),
}

# Initialize subdag variables
parent_task_id = 'udac_example_dag'
start_date=datetime.utcnow()

dag = DAG(parent_task_id,
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

# Create Staging tables
create_staging_events = PostgresOperator(
    task_id="create_staging_events",
    dag=dag,
    postgres_conn_id="redshift",
    sql=CreateTables.create_staging_events
)

create_songs_table = PostgresOperator(
    task_id="create_staging_songs",
    dag=dag,
    postgres_conn_id="redshift",
    sql=CreateTables.create_staging_songs
)

# Populate staging tables
stage_events_to_redshift = StageToRedshiftOperator(
    task_id="Stage_events",
    dag=dag,
    table="staging_events",
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="log_data",
    more_options="format as json 's3://udacity-dend/log_json_path.json'"
)

stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='Stage_songs',
    dag=dag,
    table="staging_songs",
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="song_data",
    more_options="json 'auto' compupdate off region 'us-west-2'"
)

# Create fact table : songplays
create_songplays = PostgresOperator(
    task_id="create_songplays",
    dag=dag,
    postgres_conn_id="redshift",
    sql=CreateTables.create_songplays
)

load_songplays_table = LoadFactOperator(
    task_id='Load_songplays_fact_table',
    dag=dag,
    redshift_conn_id="redshift",
    table="songplays",
    sql_source=SqlQueries.songplay_table_insert
)


# Create & Load dimension tables
# artists table
load_artists_dimension_table_task_id = "artists_subdag"
load_artists_dimension_table = SubDagOperator(
    subdag=load_dim_table_dag(
        parent_dag_name=parent_task_id,
        task_id=load_artists_dimension_table_task_id,
        redshift_conn_id="redshift",
        table="artists",
        create_sql_stmt=CreateTables.create_artists,
        select_stmt=SqlQueries.artist_table_insert,
        append_rows=False,
        start_date=start_date
    ),
    task_id=load_artists_dimension_table_task_id,
    dag=dag,
)

# songs table
load_songs_dimension_table_task_id = "songs_subdag"
load_songs_dimension_table = SubDagOperator(
    subdag=load_dim_table_dag(
        parent_dag_name=parent_task_id,
        task_id=load_songs_dimension_table_task_id,
        redshift_conn_id="redshift",
        table="songs",
        create_sql_stmt=CreateTables.create_songs,
        select_stmt=SqlQueries.song_table_insert,        
        append_rows=False,
        start_date=start_date
    ),
    task_id=load_songs_dimension_table_task_id,
    dag=dag,
)

# users table
load_users_dimension_table_task_id = "users_subdag"
load_users_dimension_table = SubDagOperator(
    subdag=load_dim_table_dag(
        parent_dag_name=parent_task_id,
        task_id=load_users_dimension_table_task_id,
        redshift_conn_id="redshift",
        table="users",
        create_sql_stmt=CreateTables.create_users,
        select_stmt=SqlQueries.user_table_insert,        
        append_rows=False,
        start_date=start_date
    ),
    task_id=load_users_dimension_table_task_id,
    dag=dag,
)

# time table
load_time_dimension_table_task_id = "time_subdag"
load_time_dimension_table = SubDagOperator(
    subdag=load_dim_table_dag(
        parent_dag_name=parent_task_id,
        task_id=load_time_dimension_table_task_id,
        redshift_conn_id="redshift",
        table="time",
        create_sql_stmt=CreateTables.create_time,
        select_stmt=SqlQueries.time_table_insert,        
        append_rows=False,
        start_date=start_date
    ),
    task_id=load_time_dimension_table_task_id,
    dag=dag,
)

# Data Quality Checks Operator
run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    dag=dag,
    redshift_conn_id="redshift",
    tables=['songplays', 'users', 'artists', 'songs', 'time']    
)


end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

# ETL Data pipeline

# Stage 1
start_operator >> create_staging_events
start_operator >> create_songs_table

# Stage 2
create_staging_events >> stage_events_to_redshift
create_songs_table >> stage_songs_to_redshift

# Stage 3
stage_events_to_redshift >> create_songplays
stage_songs_to_redshift >> create_songplays

# Stage 4
create_songplays >> load_songplays_table

# Stage 5
load_songplays_table >> load_users_dimension_table
load_songplays_table >> load_songs_dimension_table
load_songplays_table >> load_artists_dimension_table
load_songplays_table >> load_time_dimension_table

# Stage 6
load_users_dimension_table >> run_quality_checks
load_songs_dimension_table >> run_quality_checks
load_artists_dimension_table >> run_quality_checks
load_time_dimension_table >> run_quality_checks

# Stage 7 
run_quality_checks >> end_operator
