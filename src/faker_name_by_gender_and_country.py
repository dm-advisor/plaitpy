from faker import Faker
from pprint import pprint
import csv

num_recs = 5000

names_by_locale = []
country = None

for locale in ['en_GB', 'en_IE', 'en_IN', 'en_NZ', 'en_TH', 'en_US']:
    for _ in range(num_recs):
        fake = Faker(locale)
        if locale == 'en_GB':
            country = 'United Kingdom'
        elif locale == 'en_IE':
            country = 'Ireland'
        elif locale == 'en_IN':
            country = 'India'
        elif locale == 'en_NZ':
            country = 'New Zealand'
        elif locale == 'en_TH':
            country = 'Thailand'
        elif locale == 'en_US':
            country = 'United States'
        else:
            country = 'Other'
        names_by_locale.append([country, fake.unique.first_name_female(), fake.last_name(), 'F'])
        names_by_locale.append([country, fake.unique.first_name_male(), fake.last_name(), 'M'])

# pprint(names_by_locale)
header = ['Country', 'First_Name', 'Last_Name', 'Gender']
with open('../templates/data/names_by_gender_and_country.csv', 'a', encoding='UTF-8', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    csv_writer.writerows(names_by_locale)
