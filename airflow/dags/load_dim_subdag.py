import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from operators.has_rows import HasRowsOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators import (LoadDimensionOperator)
import logging

# Create a table if it does not exist, and then load data into that table from S3. 
# Peform check if rows are loaded else DAG will fail.



def load_dim_table_dag(
        parent_dag_name,
        task_id,
        redshift_conn_id,
        table,
        create_sql_stmt,
        select_stmt,
        append_rows,
        *args, **kwargs):
    
    dag = DAG(
        f"{parent_dag_name}.{task_id}",
        **kwargs
    )

    insert_sql = """
        INSERT INTO {}
        {}
        ;
    """
    
    create_dimtable_task = PostgresOperator(
        task_id=f"create_{table}_table",
        dag=dag,
        postgres_conn_id=redshift_conn_id,
        sql=create_sql_stmt
    )

    
    insert_to_table = LoadDimensionOperator(
        task_id=f"insert_into_{table}",
        dag=dag,
        redshift_conn_id="redshift",
        table=table,
        sql_source=select_stmt,
        append_rows=append_rows
    )
    
    # Quality check
    check_task = HasRowsOperator(
        task_id=f"check_{table}_data",
        dag=dag,
        redshift_conn_id=redshift_conn_id,
        table=table
    )

    create_dimtable_task >> insert_to_table
    insert_to_table >> check_task
    
    return dag
