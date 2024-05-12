## plait.py - Synthetic data for Delta Lake
This project is a fork of plait.py. For foundational information refer to [plait.py](https://github.com/plaitpy/plaitpy) in github.

The main purpose of this project is to generate the following 3 distinct synthetic datasets for a 
hypothetical higher education institution:
* undergraduate applicants (i.e., applicants file)
* undergraduate admitted candidates (i.e., admits file)
* undergraduate enrolled students (i.e., enrollment file)

The field that links the applicants and admits files is: applicant_id. Once a candidate is admitted 
and enrolls, their applicant_id becomes their student_id. The admits file can then be linked to the
enrollment file matching applicant_id to student_id.

### How this project is different from plait.py
The following customizations were applied to this fork:

* Changed all `dump(json.load(f))` references in ~/plaitpy/src/template.py to `safe_dump(json.load(f))`
* A number of new templates were introduced in ~/paitpy/templates/undergrad directory

### Usage
Follow the steps below, in the order they are listed, to generate synthetic data for applicants, admits 
and enrollment files and load them into the bronze layer of the delta lake.
#### Applicants file:
1. Execute the following command in the ~/plaitpy/bin directory to generate the applicants' data.
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

    Note: Each time plait.py runs it may generate a handful of duplicate application_ids in the applicant synthetic 
    data. The rows with duplicate application_ids will be dropped using the SQL in the next step. 
    To identify the rows with duplicate application_ids run the following query:

    `SELECT academic_year, academic_term, applicant_id, count(*) as count FROM datamorph_demo.applicant_raw_delta GROUP BY academic_year, academic_term, applicant_id HAVING count(*) > 1;`
#### Admits file:
5. To synchronize application_id values between applicants and admits files generate a row_num by executing the 
following query in the Athena console and download the results to a file named indexed_applicants.csv:
   
    `SELECT academic_year, academic_term, applicant_id, row_num 
    FROM (
           SELECT academic_year, academic_term, applicant_id,
                  row_number() over (order by academic_year, academic_term, applicant_id) as row_num
           FROM datamorph_demo.applicant_raw_delta 
           WHERE academic_year || academic_term || applicant_id not in (select academic_year || academic_term || applicant_id from datamorph_demo.applicant_raw_delta group by academic_year, academic_term, applicant_id having count(*) > 1)
         )
    WHERE academic_year = '2023'
    AND   academic_term = '2'
    ORDER BY academic_year, academic_term, applicant_id`
    
    Note: The AND in the last WHERE clause in the above query excludes the rows with duplicate 
application_id values (refer to the note in the previous step). 

6. Place the indexed_applicants.csv file in ~/plaitpy/templates/data directory. This file will be leveraged by the 
yaml template in the next step.
7. Execute the following command in the ~/plaitpy/bin directory to generate the applicants' data.
   * `plait.py ../templates/undergrad/admit.yaml --csv --num 250000 > /tmp/admit_\<term\>_\<year\>.csv`
8. Upload the generated file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/admission
9. Execute the following datamorph pipeline: admission_data_bronze
10. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.admission_raw_delta
    COMMENT 'This table stores data in delta format about University applicants who have been admitted'
    LOCATION 's3://datamorph-demo/output/university_athena_bronze/admission_raw_delta'
    TBLPROPERTIES ('table_type' = 'DELTA');`

#### Enrollment file:
11. To synchronize application_id values in the admits file with student_id values in the enrollment file generate 
a row_num by executing the following query in the Athena console and download the results to a file named 
indexed_admissions.csv:

    `SELECT academic_year, academic_term, applicant_id, row_num 
    FROM (
           SELECT academic_year, academic_term, applicant_id,
                  row_number() over (order by academic_year, academic_term, applicant_id) as row_num
           FROM datamorph_demo.admission_raw_delta 
           WHERE admit_status_code in ('06','07','08','09','13','35')
         )
    WHERE academic_year = 2023
    AND   academic_term = 2
    ORDER BY academic_year, academic_term, applicant_id`

Note: The inner WHERE clause in the above query includes only applicants with the admit_status_code values
that are eligible for enrollment.
Place the indexed_admissions.csv file in ~/plaitpy/templates/data directory. This file will be leveraged by the 
yaml template in the next step.
12. Execute the following command in the ~/plaitpy/bin directory to generate the applicants' data.
   * `plait.py ../templates/undergrad/enrollment.yaml --csv --num {max-row-nums} > /tmp/enrollment_\<term\>_\<year\>.csv`
    where {max-row-nums} is the highest value of row_num in the indexed_admissions.csv file.
14. Upload the generated file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/enrollment
14. Execute the following datamorph pipeline: enrollment_data_bronze
15. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.enrollment_raw_delta
    COMMENT 'This table stores data in delta format about University applicants who have enrolled'
    LOCATION 's3://datamorph-demo/output/university_athena_bronze/enrollment_raw_delta'
    TBLPROPERTIES ('table_type' = 'DELTA');`
16. Now that raw synthetic data has been loaded in delta tables in the bronze layer you can proceed 
by executing the pipelines for the silver and gold layers.

TODO: Finalize the above instructions
### License

[MIT](https://github.com/plaitpy/plaitpy/blob/master/LICENSE.txt)
