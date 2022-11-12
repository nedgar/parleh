import argparse
from parleh import Parleh

parser = argparse.ArgumentParser(description='Extract roles from all people records and output CSV.')
parser.add_argument('role_field', type=str, help='the role field to extract')

args = parser.parse_args()
parleh = Parleh()
df = parleh.extract_roles(args.role_field)
print(df.to_csv())
