from faker import Faker
from pprint import pprint
import csv

num_recs = 5000

addresses_by_locale = []
country = None

for locale in ['en_AU', 'en_BD', 'en_CA', 'en_GB', 'en_IE', 'en_IN', 'en_NZ',  'en_PH']:
    for _ in range(num_recs):
        fake = Faker(locale)
        if locale == 'en_AU':
            country = 'Australia'
        elif locale == 'en_BD':
            country = 'Bangladesh'
        elif locale == 'en_CA':
            country = 'Canada'
        elif locale == 'en_GB':
            country = 'United Kingdom'
        elif locale == 'en_IE':
            country = 'Ireland'
        elif locale == 'en_IN':
            country = 'India'
        elif locale == 'en_NZ':
            country = 'New Zealand'
        elif locale == 'en_PH':
            country = 'Philippines'
        else:
            country = 'Other'
        addresses_by_locale.append([country, fake.street_address().replace('\n', ' '), fake.city(), fake.postcode()])

# pprint(addresses_by_locale)

header = ['Country', 'Street', 'City', 'Postal_Code']
with open('../templates/data/foreign_addresses.csv', 'a', encoding='UTF-8', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    csv_writer.writerows(addresses_by_locale)
