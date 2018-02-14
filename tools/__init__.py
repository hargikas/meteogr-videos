"""Various Helper Functions"""
import errno
import os


def print_progress(iteration, total, prefix='', suffix='', decimals=1,
                   length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def sane_arguments(fire_input):
    """Transform the argument into a list of strings or a list of integers"""
    type_of = type(fire_input).__name__
    result = []

    # Try to convert possible
    if ((type_of == 'str') or (type_of == 'int') or (type_of == 'float')):
        result = [fire_input]
    elif type_of == 'list':
        result = fire_input[:]
    elif type_of == 'tuple':
        result = list(fire_input)
    elif type_of == 'dict':
        result = [key for key in fire_input]

    result = [int(i) if type(i).__name__ == 'float' else i for i in result]
    return result


def silentremove(fname):
    """Remove a file and supress any errors if the file doesn't exist"""
    if fname is not None:
        try:
            os.remove(fname)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise
