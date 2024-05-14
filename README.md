## plaitpy - Synthetic data for Delta Lake
This project is a fork of plaitpy Python package. For foundational information refer to [plait.py](https://github.com/plaitpy/plaitpy) 
README in github. To install this specific fork of plaitpy, follow the instructions in the Installation 
section below.

### Project Description
The aim of this project is to generate synthetic data for a fictitious higher education institution. The generated data will then be used to demonstrate the features and capabilities of Datamorph as a powerful tool to load, embellish and curate the data in a delta lake.
The synthetic data for this project is generated in the following three distinct files: 

* undergraduate applicants (i.e., applicants file using applicant.yaml)
* admitted undergraduate applicants (i.e., admits file using admit.yaml)
* enrolled undergraduate students (i.e., students file using enrollment.yaml)

The field that links the applicants and admits files is applicant_id. Once a candidate is admitted and enrolls, 
their applicant_id becomes their student_id. The admits file can then be linked to the students file matching the 
applicant_id to student_id.

### How is this project different from plaitpy?
The following customizations were applied to this fork:

* Changed all `dump(json.load(f))` references in ~/plaitpy/src/template.py to `safe_dump(json.load(f))`
* A number of new templates were introduced in ~/paitpy/templates/undergrad directory
* Additional files were introduced in the ~/paitpy/templates/data directory
### Installation
To install the Python package for generating synthetic data follow the steps below. 
1.	Verify that pip is installed on your machine:
`pip --version`
2.	Clone the repository to your local machine using the following command: 
`git clone https://github.com/dm-advisor/plaitpy.git`
3.	Change directory to the cloned repository’s root directory.
4.	Install the package using pip:
`pip install .` 
5.	To verify the installation, issue the `pip freeze` command and ensure that plaitpy points to the root directory 
of the cloned repository (e.g., plaitpy @ file:///\<local directory\>).
### Usage
Follow the steps below, in the order they are listed, to generate the synthetic data in applicants, admits 
and students files and load them into the bronze layer of the delta lake. Note that you can change the 
year_applied and term_applied values in the `define` section of the applicant.yaml, admit.yaml and enrollment.yaml 
templates in the ~/plaitpy/templates/undergrad directory and repeat the steps below to generate data for additional academic years and terms.
#### Applicants file:
1. Execute the following command in the ~/plaitpy/bin directory to generate the applicants JSON file.
   * `plait.py ../templates/undergrad/applicant.yaml --json --num 250000 > /tmp/applicant_{year}_{term}.json`
   
    where {year} = 2023, 2022, 2021, 2020, or 2019 and {term} = fall
   
    Note 1: If you want to eyeball the above output easier you can execute:

    `python ../src/pretty_json.py /tmp/applicant_{year}_{term}.json > {output-file-name}.json`
  
    Note 2: Because the generated applicants data includes Python structures such as lists and dictionaries, it is
    best to generate the data in json format, as opposed to csv.
2. Upload the plait.py command output file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/applicant
3. Execute the following datamorph pipeline: applicant_data_bronze
4. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.applicant_raw_delta
      COMMENT 'This table stores the university applicants data in delta format'
      LOCATION 's3://datamorph-demo/output/university_athena_bronze/applicant_raw_delta'
      TBLPROPERTIES ('table_type' = 'DELTA');`

    Note: Each time plait.py runs it may generate a handful of duplicate application_ids in the applicant synthetic 
    data. The rows with duplicate application_ids will be excluded using the SQL in the next step. 
    To identify the rows with duplicate application_ids run the following query:

    `SELECT academic_year, academic_term, applicant_id, count(*) as count FROM datamorph_demo.applicant_raw_delta GROUP BY academic_year, academic_term, applicant_id HAVING count(*) > 1;`
#### Admits file:
   5. To synchronize application_id values between applicants and admits files, generate a row_num column by executing the 
   following query in the Athena console. Then download the query results to a file named indexed_applicants.csv:
   
       `SELECT academic_year, academic_term, applicant_id, row_num 
   FROM ( 
       SELECT academic_year, academic_term, applicant_id, row_number() 
              over (order by academic_year, academic_term, applicant_id) as row_num 
       FROM datamorph_demo.applicant_raw_delta 
       WHERE academic_year || academic_term || applicant_id not in (
           select academic_year || academic_term || applicant_id 
           from datamorph_demo.applicant_raw_delta 
           group by academic_year, academic_term, applicant_id having count(*) > 1) 
       ) 
   WHERE academic_year = '{year}' AND academic_term = '{term}' 
   ORDER BY academic_year, academic_term, applicant_id;`
    
       Note 1: {year} = 2023, 2022, 2021, 2020 or 2019 and {term} = 2

       Note 2: The inner WHERE clause in the above query excludes the rows with duplicate 
       application_id values (refer to the note in the previous step). In this situation, the application_id
       of the duplicate rows in the applicants file end up with null values in the admits file. You can
       confirm this by running the following query:

       `WITH temp as ( 
           SELECT a.academic_year, a.academic_term, a.applicant_id as applicant_applicant_id, b.applicant_id as admit_applicant_id 
           FROM datamorph_demo.applicant_raw_delta a 
           LEFT OUTER JOIN datamorph_demo.admission_raw_delta b 
           ON a.applicant_id = b.applicant_id 
           AND a.academic_year = b.academic_year 
           AND a.academic_term = b.academic_term 
       ) select * from temp where admit_applicant_id is null;`

6. Place the indexed_applicants.csv file in ~/plaitpy/templates/data directory. This file will be leveraged by the 
yaml template in the next step.
7. Execute the following command in the ~/plaitpy/bin directory to generate the applicants file.
   * `plait.py ../templates/undergrad/admit.yaml --csv --num 250000 > /tmp/admit_{year}_{term}.csv`

    where {year} = 2023, 2022, 2021, 2020 or 2019 and {term} = fall
8. Upload the generated file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/admission
9. Execute the following datamorph pipeline: admission_data_bronze
10. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.admission_raw_delta
    COMMENT 'This table stores data in delta format about university applicants whose application has been processed'
    LOCATION 's3://datamorph-demo/output/university_athena_bronze/admission_raw_delta'
    TBLPROPERTIES ('table_type' = 'DELTA');`

#### students file:
11. To synchronize application_id values in the admits file with student_id values in the students file generate 
a row_num column by executing the following query in the Athena console. Then download the query results to a file named 
indexed_admissions.csv:

    `SELECT academic_year, academic_term, campus_proposed_code, college_proposed_code, major_proposed_code, applicant_id, row_num 
FROM ( 
	SELECT academic_year, academic_term, campus_proposed_code, college_proposed_code, major_proposed_code, applicant_id, row_number() 
			over (order by academic_year, academic_term, campus_proposed_code, college_proposed_code, major_proposed_code, applicant_id) as row_num 
	FROM datamorph_demo.admission_raw_delta 
	WHERE admit_status_code in ('06','07','08','09','13','35') ) 
WHERE academic_year = '{year}' AND academic_term = '{term}' 
ORDER BY academic_year, academic_term, campus_proposed_code, college_proposed_code, major_proposed_code, applicant_id;`

    Note 1: The inner WHERE clause in the above query includes only applicants with the admit_status_code values
    that are eligible for enrollment.

    Note 2: {year} = 2023, 2022, 2021, 2020 or 2019 and {term} = 2

12. Place the indexed_admissions.csv file in ~/plaitpy/templates/data directory. This file will be leveraged by the 
yaml template in the next step.
13. Execute the following command in the ~/plaitpy/bin directory to generate the students file.
   * `plait.py ../templates/undergrad/enrollment.yaml --csv --num {max-row-nums} > /tmp/enrollment_{year}_{term}.csv`
    
        where {year} = 2023, 2022, 2021, 2020 or 2019 and {term} = fall and {max-row-nums} = the highest value of 
        row_num field in the indexed_admissions.csv file.
    
14. Upload the generated file to the following AWS S3 path:
   * datamorph-demo/datasets/university_data/enrollment
15. Execute the following datamorph pipeline: student_data_bronze
16. Create a delta table that overlays the target dataset from the previous step:

    `CREATE EXTERNAL TABLE IF NOT EXISTS datamorph_demo.student_raw_delta
    COMMENT 'This table stores data in delta format about university admits who have enrolled'
    LOCATION 's3://datamorph-demo/output/university_athena_bronze/student_raw_delta'
    TBLPROPERTIES ('table_type' = 'DELTA');`
17. Now that raw synthetic data has been loaded into delta tables, you can join and query the delta tables
to profile the raw data. Below is a sample query:

    `SELECT a.academic_year, a.academic_term, a.ethnicity, b.gender_identity, c.registration_status_code, count(*) as count
FROM datamorph_demo.applicant_raw_delta a
INNER JOIN datamorph_demo.admission_raw_delta b
ON  a.academic_year = b.academic_year
AND a.academic_term = b.academic_term
AND a.applicant_id = b.applicant_id
INNER JOIN datamorph_demo.student_raw_delta c 
ON  b.academic_year = c.academic_year
AND b.academic_term = c.academic_term
AND b.applicant_id = c.student_id
GROUP BY a.academic_year, a.academic_term, a.ethnicity, b.gender_identity, c.registration_status_code
ORDER BY a.academic_year, a.academic_term, a.ethnicity, b.gender_identity, c.registration_status_code;`
18. Next step is to create and execute the pipelines for the silver and gold layers.
### License

[MIT](https://github.com/plaitpy/plaitpy/blob/master/LICENSE.txt)
