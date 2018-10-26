#========================================================#
# PyLevelizor - An audio leveling program
# v0.1
#========================================================#

#Imports=================================================#
import math
import sys,os
from time import sleep
from datetime import datetime,timedelta
from colorama import init,Fore,Back,Style
init(autoreset=True) #colors init
from types import SimpleNamespace
import audioop
#Audio Codecs
import wave
#========================================================#

#Globals=================================================#
ver=0.1
styles=SimpleNamespace(**{'header':Fore.CYAN+Style.BRIGHT, 'warn':Fore.YELLOW+Style.BRIGHT,'error':Fore.RED+Style.BRIGHT,
                        'good':Fore.GREEN+Style.BRIGHT,'loading':Fore.CYAN+Style.BRIGHT,'debug':Fore.MAGENTA+Style.BRIGHT,
                        'reset':Style.RESET_ALL})
is_executable = getattr(sys, 'frozen', False)
script_dir = os.path.dirname(sys.executable) if is_executable else os.path.dirname(os.path.realpath(sys.argv[0]))
resources_dir=os.path.join(sys._MEIPASS, 'resources') if is_executable else os.path.join(os.path.join(script_dir,'..'),'resources') #pylint: disable=E1101
supported_inputs=['.wav']
supported_outputs=supported_inputs
supported_options={'-p':'Pause at each error, giving a yes/no prompt','-d':'Print debug information'}
#========================================================#

#Functions===============================================#
def askYN(question:str,default=''):
    """
    Asks the user a yes/no question until a valid input is given.\n
    <question>: The question to ask\n
    <default>: (Optional) A default option to give
    """
    response='0'
    qText=(question+('['+default.lower().strip()+']') if default.strip() and default.lower().strip()[0] in ('y','n') else question)+': '
    while response.lower().strip()[0] not in ('y','n'):
        response=input(qText)
        if not response.strip() or response.isspace():
            if default.lower().strip() in ('y','n'): response=default.lower().strip()
    return response.lower().strip()[0]=='y'

def getArguments(args):
    inputFiles=[]
    options=[]
    #Get Options
    for arg in args:
        if not os.path.isfile(arg) and arg.strip()[0]=='-':
            if arg.strip() in supported_options.keys():
                options.append(arg)
            else:
                print(styles.warn+'Invalid option "'+arg+'".')
                if '-p' in options and not askYN('Continue and ignore?','y'):
                    call_exit()
    #Get Files
    for arg in (args):
        fileName,extension=os.path.splitext(arg)
        
        #Valid file
        if os.path.splitext(arg)[1] in supported_inputs:
            if os.path.isfile(arg):
                #If it can actually be accessed
                if os.access(arg,os.R_OK):
                    inputFiles.append(arg)
                else:
                    print(styles.warn+'Could not open "'+os.path.basename(arg)+'".')
                    if '-p'  in options and not askYN('Continue and ignore?','y'):
                        call_exit()
            else:
                print(styles.warn+'File "'+os.path.basename(arg)+'" does not exist.')
                if '-p'  in options and not askYN('Continue and ignore?','y'):
                    call_exit()
        #Not a file or directory (shouldn't happen with drag-and-drop)
        elif extension.isspace() or not extension:
            continue
        #A directory
        elif os.path.isdir(arg):
            print(styles.warn+'Directory drag-and-drop is not currently supported, so the directory "'+os.path.basename(arg)+'" will not be loaded.')
            if '-p' in options and not askYN('Continue and ignore?','y'):
                call_exit()
        else:
            print(styles.warn+'"'+extension+'" files are not currently supported, so the file "'+os.path.basename(arg)+'" will not be loaded.')
            if '-p' in options and not askYN('Continue and ignore?','y'):
                call_exit()
    return inputFiles,options

def truncate(data:str,length:int,append:str=''):
    """
    Truncates a string to the given length
    :param data: The string to truncate
    :param length: The length to truncate to
    :param append: Text to append to the end of truncated string
    """
    return (data[:length]+append) if len(data)>length else data

def call_exit(message='Press return to exit...'):
    """
    Gracefully exit on user pressing return.\n
    <message>: Message to prompt the user to press return
    """
    print(styles.warn+message,end='')
    input()
    sys.exit(0)

def sec_to_time(sec:float):
    """

    """
    minutes, seconds = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    periods = [('h', int(hours)), ('m', int(minutes)), ('s', int(seconds))]
    time_string = ':'.join('{}{}'.format(value, name)
                            for name, value in periods
                            if value)
    return time_string

def comstr(val):
    """
    Return a comma-separated string representing the given value\n
    EG: 1000000->1,000,000
    """
    return ('{:,}'.format(val))

def loading_bar(curr,total,length=50,prefix='Progress:',suffix='',decimals=1,fill='='):
    new_total=total-1
    percent=round(100*(float(curr)/float(new_total)),decimals)
    if decimals==0:
        percent=int(percent)
    if percent==loading_bar.oldpercent and percent!=100:
        return
    loading_bar.oldpercent=percent
    filled_length=int(length*curr//new_total)
    bar=styles.loading+fill*filled_length+'-'*(length-filled_length)
    print(prefix+'['+bar+'] '+str(percent)+'%'+' '+suffix,end='\r')
    
    if curr==new_total:
        print()
loading_bar.oldpercent=-1

def level_wav(file_path:str):
    input_file=wave.open(file_path)
    print(styles.good+'File: '+os.path.basename(file_path)+', Channels: '+str(input_file.getnchannels())+
    ' ('+('mono' if +input_file.getnchannels()==1 else 'stereo')+'), Sample Rate: '+str(input_file.getframerate())+
    'hz, Length: '+sec_to_time(input_file.getnframes()/float(input_file.getframerate())))
    sample_size=input_file.getsampwidth()*input_file.getnchannels()
    #Extra debug info
    if '-d' in options:
        print(styles.debug+'DEBUG: '+styles.good+'Total Samples: '+comstr(input_file.getnframes())+
        ', Sample Size: '+str(sample_size)+' bytes ('+str(sample_size*8)+' bits)')

    #Read Frames
    nframes=input_file.getnframes()
    total_amp=0
    totalIters=0
    for i in range (nframes):
        frame=input_file.readframes(1)
        total_amp+=audioop.rms(frame,sample_size)
          

        loading_bar(totalIters,nframes*2,prefix='Averaging: ')
        totalIters+=1
        
    avg_amp=total_amp/nframes
    print('Power: '+str(avg_amp)+' dB: '+str(10*math.log(avg_amp)))
    
    #Get Average
    #max_level=audioop.avgpp(frames,2)
    #print('Max: '+str(max_level))
    input_file.close()
#========================================================#

#Startup=================================================#
print(styles.header+'<<<PyLevelizor '+str(ver)+', by wolfinabox>>>')
if os.name!='nt':
    print('Sorry, this application currently only supports Windows.')
    input('Press return to exit...')
    sys.exit(-1)
#Arguments
#No args provided
if len(sys.argv)==1:
    print('To use PyLevelizor, drag and drop source audio files onto this executable.\nOr, run it from a terminal.')
    print('Supported filetypes: '+styles.good+', '.join(supported_inputs))
    print('Supported options:')
    for key,val in supported_options.items():
        print(styles.good+key+styles.reset+' : '+val)
    call_exit()
#Get Arguments
input_files=[]
options=[]
input_files,options=getArguments(sys.argv[1:])

#If no valid input files
if not input_files:
    print('No valid input files loaded.')
    call_exit()
#========================================================#

#Work====================================================#

print('Leveling files: '+', '.join([os.path.basename(f) for f in input_files])+'...')
#Actually do the stuff the program is meant to do here :P
#========================================================#
for f in input_files:
    fname,fext=os.path.splitext(f)
    fpath=os.path.abspath(f)
    #Audio Types
    if fext=='.wav':
        level_wav(fpath)        
#Finish==================================================#
print(styles.good+'All files completed!')
#call_exit()
#========================================================#
