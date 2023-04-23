--
-- Providence
-- Pipelines
-- YNAB External Table DDL
--
CREATE EXTERNAL TABLE {{ params.redshift_external_schema }}.{{ params.redshift_table }} (
  id varchar,
  name varchar,
  last_modified_on varchar,
  first_month varchar,
  last_month varchar,
  date_format struct<format:varchar>,
  currency_format struct<iso_code:varchar,example_format:varchar,decimal_digits:int,decimal_separator:varchar,symbol_first:boolean,group_separator:varchar,currency_symbol:varchar,display_symbol:boolean>,
  accounts array<struct<id:varchar,name:varchar,type:varchar,on_budget:boolean,closed:boolean,note:varchar,balance:int,cleared_balance:int,uncleared_balance:int,transfer_payee_id:varchar,deleted:boolean>>,
  payees array<struct<id:varchar,name:varchar,hidden:varchar,deleted:boolean,transfer_account_id:varchar>>,
  payee_locations array<struct<id:varchar,payee_id:varchar,latitude:varchar,longitude:varchar,deleted:boolean>>,
  category_groups array<struct<id:varchar,name:varchar,hidden:boolean,deleted:boolean,transfer_account_id:varchar>>,
  categories array<struct<id:varchar,category_group_id:varchar,name:varchar,hidden:boolean,original_category_group_id:varchar,note:varchar,budgeted:int,activity:int,balance:int,goal_type:varchar,goal_creation_month:varchar,goal_target:int,goal_target_month:varchar,goal_percentage_complete:int,deleted:boolean>>,
  months array<struct<month:varchar,note:varchar,income:int,budgeted:int,activity:int,to_be_budgeted:int,age_of_money:int,deleted:boolean,categories:array<struct<id:varchar,category_group_id:varchar,name:varchar,hidden:boolean,original_category_group_id:varchar,note:varchar,budgeted:int,activity:int,balance:int,goal_type:varchar,goal_creation_month:varchar,goal_target:int,goal_target_month:varchar,goal_percentage_complete:int,deleted:boolean>>>>,
  transactions array<struct<id:varchar,date:varchar,amount:int,memo:varchar,cleared:varchar,approved:boolean,flag_color:varchar,account_id:varchar,payee_id:varchar,category_id:varchar,transfer_account_id:varchar,transfer_transaction_id:varchar,matched_transaction_id:varchar,import_id:varchar,deleted:boolean>>,
  subtransactions array<struct<id:varchar,scheduled_transaction_id:varchar,amount:int,memo:varchar,payee_id:varchar,category_id:varchar,transfer_account_id:varchar,deleted:boolean,transaction_id:varchar>>,
  scheduled_transactions array<struct<id:varchar,date_first:varchar,date_next:varchar,frequency:varchar,amount:int,memo:varchar,flag_color:varchar,account_id:varchar,payee_id:varchar,category_id:varchar,transfer_account_id:varchar,deleted:boolean>>,
  scheduled_subtransactions array<varchar>,
  _ynab_src_scraped_on varchar
)
PARTITIONED BY (date varchar) ROW
FORMAT
  SERDE 'org.openx.data.jsonserde.JsonSerDe'
  STORED AS TEXTFILE
    LOCATION 's3://{{ params.s3_bucket }}/providence/grade=raw/source=uob/'
