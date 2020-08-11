import numpy as np 
import pandas
import os

def get_filenames(path, contains, does_not_contain=['~', '.pyc']):
    cmd = 'ls ' + '"' + path + '"'
    ls = os.popen(cmd).read()
    all_filelist = ls.split('\n')
    try:
        all_filelist.remove('')
    except:
        pass
    filelist = []
    for i, filename in enumerate(all_filelist):
        if contains in filename:
            fileok = True
            for nc in does_not_contain:
                if nc in filename:
                    fileok = False
            if fileok:
                filelist.append( os.path.join(path, filename) )
    return filelist

def load_buffers_from_file(filename, data_type, number_fill_bytes, number_data_records=10):
    # nested datatype
    dt = np.dtype([('head', '<u4'), ('buff', data_type, (number_data_records,)), ('tail', 'i1', number_fill_bytes)])

    # read the data
    data = np.fromfile(filename, dtype=dt)
    correct_number_data_records = data['head'][0] # the correct number

    if correct_number_data_records != number_data_records:
        dt = np.dtype([('head', '<u4'), ('buff', data_type, (correct_number_data_records,)), ('tail', 'i1', number_fill_bytes)])
        data = np.fromfile(filename, dtype=dt)

    return np.hstack( data['buff'] )

def discover_number_of_fill_bytes_and_data_records(filename, data_type, 
                                                   number_data_records=5, number_fill_bytes=90,
                                                   verbose = False):
    '''
    filename: of binary file
    data_type: like this:
    
        data_type = [('millis', '<u4'),  # uint32_t time;
             ('lat', np.single), # uint32_t test1;
             ('lon', np.single),
             ('gps_time', '<u4'),
             ('gps_date', '<u4'),
             ('wind', 'S128')] # char test2[24];
             
    number_data_records: guess of how many records per buffer
    number_fill_bytes: MINIMUM guess of how many fill_bytes (try what the teensy says minus 4 or more)
    
    '''
    
    dt = np.dtype([('head', '<u4'), ('buff', data_type, (number_data_records,)), ('tail', 'i1', number_fill_bytes)])

    # read the data
    data = np.fromfile(filename, dtype=dt)
    number_data_records = data['head'][0] # the correct number
    
    while np.std(data['head']) > 0:
        number_fill_bytes += 1
        
        dt = np.dtype([('head', '<u4'), ('buff', data_type, (number_data_records,)), ('tail', 'i1', number_fill_bytes)])
        data = np.fromfile(filename, dtype=dt)
        
        if verbose:
            print (number_fill_bytes, np.std(data['head']) )
            
    return number_data_records, number_fill_bytes

def load_data_from_directory(data_directory, data_type, number_data_records, number_fill_bytes): 
    filenames = get_filenames(data_directory, '.bin')
    df = None
    for filename in filenames:
        data_buff = load_buffers_from_file(filename, data_type, number_fill_bytes, number_data_records)
        if df is None:
            df = pandas.DataFrame(data_buff)
        else:
            df = pandas.concat([df, pandas.DataFrame(data_buff)], ignore_index=True)

    return df

if __name__ == '__main__':

    # where your binary data files are
    data_directory = 'sample_data'

    # data column names and corresponding types based on the struct_t in the teensy firmware
    # see: https://numpy.org/devdocs/user/basics.types.html
    data_type = [('time', '<u4'),  # uint32_t time;
                 ('test1', '<u4'), # uint32_t test1;
                 ('test2', 'S24')] # char test2[24];

    filenames = get_filenames(data_directory, '.bin')
    guess_number_data_records = 5
    guess_min_number_fill_bytes = 2
    number_data_records, number_fill_bytes = discover_number_of_fill_bytes_and_data_records(filenames[0], data_type, 
                                                                                           number_data_records=guess_number_data_records, 
                                                                                           number_fill_bytes=guess_min_number_fill_bytes,
                                                                                           verbose = False)
    print(number_data_records, number_fill_bytes)

    dataframe = load_data_from_directory(data_directory, data_type, number_data_records, number_fill_bytes)
    print(dataframe)





