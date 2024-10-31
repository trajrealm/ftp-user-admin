import csv

def find_signal(file_name):
    with open('/Users/triloke/VSCodeProjects/ftp-user-admin/data/signal_data_links.csv', mode='r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row

        for row in reader:
            fn = row[2].split("/")[-1]
            prefix = "_".join(fn.split("_")[:-2])
            print(prefix)

    return None  # Return None if no match found

# Example usage
input_file_name = 'TM1_History_2024_202403.zip'
signal = find_signal(input_file_name)
print(signal)  # Output: TM1-US
