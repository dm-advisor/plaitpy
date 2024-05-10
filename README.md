## plait.py
This project is a fork of plait.py. For more information refer to [plait.py](https://github.com/plaitpy/plaitpy) in github.

The main purpose of this project is to generate the following 3 distinct synthetic datasets for a hypothetical higher education institution:
* undergraduate applicants (i.e., applicants file)
* undergraduate admitted candidates (i.e., admits file)
* undergraduate enrolled students (i.e., enrollment file)

### How this project is different from plait.py
The following customizations were applied to this fork:

* Changed all `dump(json.load(f))` references in ~/src/template.py to `safe_dump(json.load(f))`
* A number of new templates were introduced in ~/templates/undergrad directory

### Usage
Follow the steps below, in the order they are listed, to generate and use the synthetic data.
1. Execute the following command in the ~/bin directory to generate the applicants' data.
   * `plait.py ../templates/undergrad/applicant.yaml --json --num 250000 > /tmp/applicant_\<term\>_\<year\>.json`
   
      If you want to eyeball the above output easier you can execute:
   
        `python ../src/pretty_json.py /tmp/applicant_\<term\>_\<year\>.json.json > {output-file-name}.json`
2. Upload the plait.py command output file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/applicant
3. Execute the following datamorph pipeline: appicant_data_bronze
4. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.applicant_raw_delta
      COMMENT 'This table stores the University applicants data in delta format'
      LOCATION 's3://datamorph-demo/output/university_athena_bronze/applicant_raw_delta'
      TBLPROPERTIES ('table_type' = 'DELTA');`
5. To synchronize application_id values between applicants and admits files generate a row_num by executing the following query in the Athena console and download the results to a file named indexed_applicants.csv:
   
   `SELECT applicant_id, row_num FROM (
     SELECT applicant_id,
            row_number() over (order by applicant_id) as row_num
     FROM datamorph_demo.applicant_raw_delta 
   )
   WHERE row_num between 1 and 250000;`

   The query above assumes that you have generated 250,000 applicant records.
6. Place the indexed_applicants.csv file in ~/templates/data directory. This file is used by the template that will be used in the next step.
7. Execute the following command in the ~/bin directory to generate the applicants' data.
   * `plait.py ../templates/undergrad/admit.yaml --json --num 250000 > /tmp/admit_\<term\>_\<year\>.json`
8. Upload the generated file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/admission
9. Execute the following datamorph pipeline: admission_data_bronze
10. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.admission_raw_delta
    COMMENT 'This table stores data in delta format about University applicants who have been admitted'
    LOCATION 's3://datamorph-demo/output/university_athena_bronze/admission_raw_delta'
    TBLPROPERTIES ('table_type' = 'DELTA');`

TODO: complete the above instructions
### License

[MIT](https://github.com/plaitpy/plaitpy/blob/master/LICENSE.txt)
