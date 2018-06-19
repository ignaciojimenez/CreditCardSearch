import re
import time
import sys
import getopt
import os
import zipfile
# Installed modules
import xlrd


def checksum(string):
    '''
    Check the Luhn algorithm on the given string
    Returns True/False
    '''
    odd_sum = sum(list(map(int, string))[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in list(map(int, string))[-2::-2]])
    return ((odd_sum + even_sum) % 10 == 0)


def searchInLine(textLine, line_position, cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given plain text line
    Prints the credit card match if it occurs
    Retuns 1 if a CC is found 0 if not
    '''
    # TODO Search for multiple matches within single line
    counter = 0
    for regEx in regex_list:
        m = re.search(r"%s" % regEx[1].rstrip(), textLine)
        if m:
            if checksum(m.group(0)):
                if mask:
                    print(cc_path + "\t" + line_position + "\t" + regEx[0].rstrip() + "\t" +
                          m.group(0)[:6] + "******" + m.group(0)[-4:])
                else:
                    print(cc_path + "\t" + line_position + "\t" +
                          regEx[0].rstrip() + "\t" + m.group(0))
                counter += 1
    return counter


def textFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given plain text file
    Retuns int total of credit cards found
    '''
    counter = 0
    line_counter = 1
    with open(cc_path, 'r', encoding="latin-1") as cc_file_data:
        for cc_file_line in cc_file_data:
            counter += searchInLine(cc_file_line, "Line_" +
                                    str(line_counter), cc_path, regex_list, mask)
            line_counter += 1
    return counter


def ExcelFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given Excel File
    Retuns int total of credit cards found
    '''
    counter = 0
    with xlrd.open_workbook(cc_path) as wb:
        for sheet in wb.sheets():
            for row in range(sheet.nrows):
                counter += searchInLine(','.join(sheet.row_values(row)),
                                        str(sheet.name) + "_row" + str(row), cc_path, regex_list, mask)
    return counter


def zipFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given zip File
    Retuns int total of credit cards found
    '''
    # TODO Iterate over the whole path
    zfile = zipfile.ZipFile(cc_path)
    for finfo in zfile.infolist():
        ifile = zfile.open(finfo)
        # line_list = ifile.readline()
        print("TODO: ZIP --> " + str(ifile))
        # searchInFile(ifile, regex_list, mask)
    return 0


def searchInFile(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given file
    Retuns int total of credit cards found, -1 if file is not supported
    '''
    if any(cc_path[-3:].lower() in s for s in ['xls', 'xlsx']):
        return ExcelFSearch(cc_path, regex_list, mask)
    elif any(cc_path[-3:].lower() in s for s in ['zip']):
        return zipFSearch(cc_path, regex_list, mask)
    elif any(cc_path[-3:].lower() in s for s in unsupported_files):
        print(cc_path + " --> Unsupported file")
        return -1
    else:
        # TODO Auto-find out if file can be read as plain text
        return textFSearch(cc_path, regex_list, mask)


if __name__ == '__main__':
    # reading input options
    inputfile = ''
    inputdir = ''
    masking = True
    # TODO Output file
    # TODO Useful Command Help text
    # TODO quiet option 1 --> Hide credit card details
    # TODO quiet option 2 --> Hide every file detail (only total execution)
    # TODO Change separator in stdout from \t to ',' for CSV ready processing
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:d:m")
    except getopt.GetoptError:
        # TODO Read current dir files as the default option
        print('Syntax: CreditCardSearch.py -i <inputfile> -d <inputdirectory> [-m] ')
        sys.exit(2)
    if not opts:
        print('Syntax: CreditCardSearch.py -i <inputfile> -d <inputdirectory> [-m] ')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage CreditCardSearch.py -i <inputfile> -d <inputdirectory> -o <outputfile> -m')
            sys.exit()
        elif opt in ("-i"):
            inputfile = arg
        elif opt in ("-d"):
            inputdir = arg
        elif opt in ("-m"):
            masking = False

    # File extension support variables
    # TODO Zip, PDF, docx, pptx, etc.
    tested_files = ['txt', 'csv', 'xls', 'xlsx', 'rtf', 'xml', 'html', 'json']
    unsupported_files = ['doc', 'docx', 'pdf', 'pptx',
                         'zip', 'jpg', 'gif', 'png', 'mp3', 'mp4', 'wav', 'aiff', 'mkv', 'avi']

    # Print memo when the script starts
    print("[" + time.ctime() + "] CreditCardSearch started")

    # Read CSV regex file to be tested
    regex_path = 'regexcard.csv'
    regex_list = []
    with open(regex_path, 'r') as regex_file:
        for line in regex_file:
            line_list = line.rstrip().split(',')
            regex_list.append(line_list)

    # If the script has received a directory to search
    if inputdir:
        count_cc_total = 0  # Total credit cards found in files
        count_nocc_files = 0  # Files containing no credit cards
        count_discarded_files = 0  # Files discarded because they are not supported
        count_cc_files = 0  # Files containing credit cards

        # Loop over the given path
        for root, dirs, files in os.walk(inputdir):
            for filename in files:
                count_fichero = searchInFile(
                    os.path.join(root, filename), regex_list, masking)
                # If CC found
                if count_fichero > 0:
                    count_cc_files += 1
                    print(os.path.join(root, filename) + " --> " +
                          str(count_fichero) + " credit cards in file")
                # If no CC found
                elif count_fichero == 0:
                    print(os.path.join(root, filename) + " --> " +
                          str(count_fichero) + " credit cards in file")
                    count_nocc_files += 1
                # If file was discarded
                elif count_fichero < 0:
                    count_discarded_files += 1
                    count_fichero = 0
                # Add total CC found during execution
                count_cc_total += count_fichero

        print("\n[" + time.ctime() + "] ")
        print("--- Execution Summary ---")
        print(str(count_cc_files + count_discarded_files + count_nocc_files) + "\tFiles read")
        print(str(count_cc_files + count_nocc_files) + "\tFiles analyzed")
        print(str(count_cc_files) + "\tFiles including credit cards")
        print(str(count_cc_total) + "\tTotal credit cards found")
        print("\n--- Disclaimer ---")
        print("CreditCardSearch tries to read data included in any file and excludes known unsuppoted files")
        print("Tested files include: %s" % ','.join(tested_files))
        print("Unsupported files include: %s" % ','.join(unsupported_files))

    # If the script received a single file to analyze
    elif inputfile:
        print(inputfile + " --> " + str(searchInFile(inputfile,
                                                     regex_list, masking)) + " credit cards in file\n")
        print("\n[" + time.ctime() + "] CreditCardSearch End")
