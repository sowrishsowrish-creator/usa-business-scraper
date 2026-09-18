"""
exporter.py
Handles exporting scraped business data to CSV or Excel
"""

# for writing CSV files
import csv

# for writing Excel files
import openpyxl

# for building the output file path
import os


class DataExporter:

    def __init__(self):
        # column headers for the output file
        self.columns = [
            "Business Name",
            "Business Type",
            "Email",
            "Phone",
            "State",
            "Website"
        ]


    def exportCSV(self, records, filepath):
        # writes all records to a .csv file
        # records is a list of dicts from the scraper

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)

                # write the header row first
                writer.writeheader()

                # write each business record
                for record in records:
                    writer.writerow(record)

            # return a success message
            return f"Saved {len(records)} records to {filepath}"

        except Exception as e:
            return f"Export failed: {e}"


    def exportExcel(self, records, filepath):
        # writes all records to a .xlsx file

        try:
            # create a new workbook and grab the active sheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Business Data"

            # write the header row
            ws.append(self.columns)

            # write each business as a row
            for record in records:
                # get the value for each column, defaulting to "N/A" if not found
                row = [record.get(col, "N/A") for col in self.columns]
                ws.append(row)

            # save the workbook to the given filepath
            wb.save(filepath)

            return f"Saved {len(records)} records to {filepath}"

        except Exception as e:
            return f"Export failed: {e}"