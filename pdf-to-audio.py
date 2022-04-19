# -*- coding: utf-8 -*-
"""
PDF to audio app
Converts PDF file content to .ogg audio file

@author: ANAT-H

English text only.
API : "http://api.voicerss.org/" (Limited to 100KB per request)

All icons from https://icon-icons.com, more detail in attributions.txt

Playing outside of this program:
.ogg file can be played with VLC player.
windows media player, needs OGG Codec Pack, can be found in
https://www.codecguide.com/download_kl.htm > Basic > Download Basic
"""
from pdfminer.high_level import extract_text
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfile
import pygame.mixer as pyx
from math import ceil
import requests
import os

# for local use of .env
from dotenv import load_dotenv 

load_dotenv()

# configure API request 
END_POINT = "http://api.voicerss.org/"
API_KEY= os.environ.get('API_KEY')
HEADERS = {'content-type': 'audio/wav'}
PARAMS = {
      "key": API_KEY,
      "hl": "en-au",
      "v": "Isla",
      "c": "OGG"
      }

# consts & globals
BG='#99ccff'
HOVER='#80bfff'

L_VOICES = {'en-au': ('Isla', 'Evie'),
          'en-ca': ('Clara', 'Mason'),
          'en-gb': ('Nancy', 'Harry'),
          'en-us': ('Amy', 'Mary', 'John', 'Mike')
          }

SPEEDS = {0.75: '-3', 1.0: '0', 1.5: '4', 2.0: '6'}

au_file=None
au_length=None
paused=False
show_vol=False
after_id=None
s_after_id=None # slider update
response=None

# initialize audio player
pyx.init()

# read pdf file
def open_file():
  '''
  Opens dialog to select pdf file and extract text.
  Update API request parameters.

  '''
  filename = askopenfilename(title='Choose file', filetypes=[('PDF Files', '*.pdf')])
  if filename:
    text = extract_text(filename)[:-1]
    PARAMS['src'] = text
    pdf_label['text']=os.path.basename(filename)
    convert_btn.state(['!disabled'])
      
def set_voices_list():
  '''
  Display list of avaiable voices for a specific lingo.
  Update API request parameters.

  '''
  voices['value']=L_VOICES[lingo.get()]
  voice.set(voices['value'][0])
  PARAMS["hl"] = lingo.get()
  
def set_voice(e):
  '''
  Select voice.
  Update API request parameters.
  '''
  PARAMS["v"]=voice.get()

def set_speed(s):
  '''  
  Select reading speed rate.
  Update API request parameters.
  '''
  PARAMS["r"]=SPEEDS[s]

# use API to convert first try with text string  
def convert():
  '''
  Send API requeset and open dialog and save audio file (.OGG)

  '''
  global response, au_length, au_file
  response = requests.get(url=END_POINT, params=PARAMS, headers=HEADERS)
  if response.status_code != 200:
    wav_filename.set('Failed: content too long or unsuitable')
    style.configure("style.TEntry", foreground ='red')
    response.raise_for_status()
  file = asksaveasfile(mode='wb', defaultextension=".ogg", title = "Save..", filetypes=[('OGG Files', '*.ogg')])
  if file:
    style.configure("style.TEntry", foreground ='white')
    file.write(response.content)
    file.close()
    wav_filename.set(os.path.basename(file.name))
    au_file = file.name
    au_length = ceil(pyx.Sound(au_file).get_length()) # in sec
    slider['length']=au_length
    slider['to']=au_length

# player funcations
def update_time_lbl(sec):
  '''
  Update the player slider track time label, when changed manually.

  Parameters
  ----------
  sec : STR
    The current time received from slider variable.

  '''
  sec=ceil(float(sec))
  h = sec//3600   # hours
  m = (sec//60)%60   # minutes
  s = sec%60   # seconds
  t_lbl.set(f'{h:02}:{m:02}:{s:02}')
  pyx.music.play(0,sec)
  if paused==True:
    pyx.music.pause()

def update_time_lbl_auto(sec):
  '''
  Update the player slider track time label,
  when changed automatically as track plays.

  Parameters
  ----------
  sec : STR
    The current time taken from slider variable.

  '''
  sec=int(sec)
  h = sec//3600   # hours
  m = (sec//60)%60   # minutes
  s = sec%60   # seconds
  t_lbl.set(f'{h:02}:{m:02}:{s:02}')
  
def update_time():
  '''
  manages the updating of the player slider time label,
  by schedule.

  '''
  global s_after_id 
  t.set(t.get()+1)
  update_time_lbl_auto(t.get())
  s_after_id = window.after(1000, update_time) 
  
def play_pause():
  '''
  Controls the play/pause/unpuase actions.

  '''
  global paused, after_id, s_after_id 
  if au_file:
    # play
    if not pyx.music.get_busy() and paused==False:
      slider.state(['!disabled'])
      pyx.music.load(au_file)
      pyx.music.play()
      s_after_id = window.after(1000, update_time) 
      play_pause_btn['image']=pause_btn_img 
    # pause  
    elif pyx.music.get_busy() and paused==False:      
        paused=True
        pyx.music.pause()
        window.after_cancel(s_after_id)
        play_pause_btn['image']=play_btn_img
    # unpause    
    elif paused==True:
        paused=False
        pyx.music.unpause()
        s_after_id = window.after(1000, update_time)
        play_pause_btn['image']=pause_btn_img   
    after_id = window.after(1000, reset_player)  
  else:
    wav_filename.set('no audio file loaded')

def backwards():
  '''
  rewinds the track by five seconds.

  '''
  if au_file and (slider.state()==()):  
    pos = max(float(t.get())-5, 0)
    t.set(pos)
    pyx.music.set_pos(pos)

  
def forwards():
  '''
  fast forward the track by five seconds.

  '''
  if au_file and (slider.state()==()): 
    pos = min(float(t.get())+5, au_length-1)
    t.set(pos)
    pyx.music.set_pos(pos) 
  

def reset_player():
  '''
  Reset player state and cancel scheduled tasks.

  '''
  global after_id
  if not pyx.music.get_busy() and paused==False:
    if after_id:
      window.after_cancel(after_id)
    if s_after_id:
     window.after_cancel(s_after_id)
    t.set(0)
    update_time_lbl_auto(t.get())
    play_pause_btn['image']=play_btn_img
    slider.state(['disabled'])
  else:
    after_id = window.after(500, reset_player) 

    
def stop():
  '''
  Stop track and cancel scheduled tasks.
  '''
  global paused
  pyx.music.stop()
  paused=False
  reset_player()
  

def show_volume_scale():
  '''
  display volume slider
  '''
  global show_vol
  if show_vol==False:
    vol_slider.grid(column=7, row=8, rowspan=3, pady=(10,0), sticky=(W))
    show_vol=True
  elif show_vol==True:
    show_vol=False
    vol_slider.grid_forget()

  
def set_volume(volume):
  '''
  adjust volume 

  Parameters
  ----------
  volume : STR
    The current volume value received from slider variable.

  '''
  volume = float(volume)
  pyx.music.set_volume(volume)
  if vol.get()==0.0:
    volume_btn['image']=mute_btn_img
  else:
    volume_btn['image']=volume_btn_img
    
      
# quit    
def wquit():
  '''
  remove all pending tasks and exit.
  '''
  if after_id:
    window.after_cancel(after_id)  
  if s_after_id:
    window.after_cancel(s_after_id)  
  pyx.quit()  
  window.destroy()  

# create tkinter interface

### main window ###
window = Tk()
window.title("pdf to audio")
window.iconbitmap("images/Speaker_icon-icons.com_54138.ico")
window.minsize(425,425)

window.resizable(False, False)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)


### Styles ###
style = ttk.Style()
style.theme_use('alt')
# frames
style.configure('style.TFrame', background=BG)
style.configure('titleframe.TFrame', background=BG)
style.configure('openframe.TFrame', background=BG)
style.configure('convertframe.TFrame', background=BG)
style.configure('player.TFrame', background=BG)
# labels
style.configure('title.TLabel', background=BG, foreground='#1a53ff', font=('TkDefaultFont', 18, 'bold'))
style.configure('style.TLabel', background=BG)
# buttons
style.configure('style.TButton', background=BG)
style.configure('player.TButton', relief='flat', borderwidth=0, focuscolor='none', background=BG)
style.map('TButton', background=[('active',HOVER)])
style.configure('style.TRadiobutton', width=15, background=BG)
style.map('TRadiobutton', background=[('active',HOVER)])
# combobox
style.configure('style.TCombobox')
style.map('TCombobox', fieldbackground=[('readonly','white')], selectbackground=[('readonly','white')], selectforeground=[('readonly','black')])
# Entry
style.configure("style.TEntry", foreground ='white', lightcolor='black')
style.map('TEntry', fieldbackground=[('readonly', 'black')])
# Scales
style.configure("style.Horizontal.TScale", background=BG, troughcolor='black')
style.map('TScale', background=[('disabled',BG)])
style.configure("style.Vertical.TScale", background=BG, troughcolor='black', foreground='red')


### main frame ###
frame = ttk.Frame(window, padding='40 25 40 40', style='style.TFrame')
frame.grid(column=0, row=0, sticky=(N ,W, E, S))

### title frame ###
titleframe = ttk.Frame(frame, padding='10 0 10 0', style='player.TFrame')
titleframe.grid(column=0, row=0, columnspan=4, sticky=(N ,W, E, S))

### open file frame ###
openframe = ttk.Frame(frame, padding='10 0 10 0', style='openframe.TFrame')
openframe.grid(column=0, row=1, columnspan=4, sticky=(N ,W, E, S))

### convert file frame ###
convertframe = ttk.Frame(frame, padding='10 0 10 0', style='convertframe.TFrame')
convertframe.grid(column=0, row=7, columnspan=4, sticky=(N ,W, E, S))

### player frame ###
player = ttk.Frame(frame, padding='10 0 10 0', style='player.TFrame')
player.grid(column=1, row=8, columnspan=4, sticky=(N ,W, E, S))


### content ###
ttk.Label(titleframe, text='Convert PDF file to Audio', style='title.TLabel').grid(column=0, row=0)

## open file
ttk.Button(openframe, text="Open", command=open_file, style='style.TButton').grid(column=0, row=1, pady=10)
pdf_label = ttk.Label(openframe, text='choose *.pdf file', style='style.TLabel')
pdf_label.grid(column=1, row=1, pady=3, padx=3) 

## choosing a voice 
ttk.Label(frame, text='English Lingo:', style='style.TLabel').grid(column=0, row=2, padx=10)
##choose lingo
lingo = StringVar(value='en-au') 
ttk.Radiobutton(frame, text='Australia', variable=lingo ,value='en-au', command=set_voices_list, style='style.TRadiobutton').grid(column=1, row=2)
ttk.Radiobutton(frame, text='Canada', variable=lingo ,value='en-ca', command=set_voices_list, style='style.TRadiobutton').grid(column=1, row=3)
ttk.Radiobutton(frame, text='Great Britain', variable=lingo ,value='en-gb', command=set_voices_list, style='style.TRadiobutton').grid(column=1, row=4)
ttk.Radiobutton(frame, text='United States', variable=lingo ,value='en-us', command=set_voices_list, style='style.TRadiobutton').grid(column=1, row=5)

## choose voice
ttk.Label(frame, text='Voice:', style='style.TLabel').grid(column=2, row=2)
voice=StringVar()
voices = ttk.Combobox(frame, textvariable=voice, width=6, style='style.TCombobox')
voices.state(['readonly'])
# default values
voices['value']=L_VOICES[lingo.get()]
voice.set(voices['value'][0])
voices.bind('<<ComboboxSelected>>', set_voice)
voices.grid(column=3, row=2)

## choose speed
ttk.Label(frame, text='Speed X', style='style.TLabel').grid(column=0, row=6, padx=8, pady=15, sticky=(N,S,E))
speed=DoubleVar()
playing_speeds = [0.75, 1.0, 1.5, 2.0]
play_rate=OptionMenu(frame, speed, *playing_speeds, command=set_speed)
play_rate.config(bg=BG, activebackground=HOVER, highlightthickness=0)
play_rate.grid(column=1, row=6, pady=15, sticky=W) 
speed.set(playing_speeds[1])

## convertion 
convert_btn=ttk.Button(convertframe, text="Convert", command=convert, style='style.TButton')
convert_btn.grid(column=0, row=7, pady=20) 
convert_btn.state(['disabled'])
wav_filename=StringVar(value='*.ogg')
wav_label=ttk.Entry(convertframe, textvariable=wav_filename, width=40, style='style.TEntry')
wav_label.grid(column=1, row=7, columnspan=4, padx=10, pady=5, ipady=3) 
wav_label.state(['readonly'])

# player
t=DoubleVar(value=0) # time in seconds
t_lbl=StringVar(value='00:00:00')
slider_pos = ttk.Label(player, textvariable=t_lbl, style='style.TLabel')
slider_pos.grid(column=5, row=9, pady=5, sticky=E) 
slider = ttk.Scale(player, orient=HORIZONTAL, variable=t, from_=0.0, style="style.Horizontal.TScale", command=update_time_lbl)
slider.grid(column=1, row=9, columnspan=4, pady=5, padx=3, sticky=(W,E)) 
slider.state(['disabled'])

bwd_btn_img = PhotoImage(file="images/player_rew_arrow_10200.png")
bwd_btn = ttk.Button(player, image=bwd_btn_img, compound='image', style='player.TButton', command=backwards)
bwd_btn.grid(column=1, row=10) 

fwd_btn_img = PhotoImage(file="images/player_fwd_arrow_10204.png")
fwd_btn = ttk.Button(player, image=fwd_btn_img, compound='image', style='player.TButton', command=forwards)
fwd_btn.grid(column=2, row=10) 

play_btn_img = PhotoImage(file="images/playerplayarrow_jugador_jueg_10201.png")
pause_btn_img = PhotoImage(file="images/playpause_jugado_10203.png")
play_pause_btn = ttk.Button(player, image=play_btn_img, compound='image', style='player.TButton', command=play_pause)
play_pause_btn.grid(column=3, row=10) 

stop_btn_img = PhotoImage(file="images/player_stop_10198.png")
stop_btn = ttk.Button(player, image=stop_btn_img, compound='image', style='player.TButton', command=stop)
stop_btn.grid(column=4, row=10) 

volume_btn_img = PhotoImage(file="images/VolumePressed_26955.png")
mute_btn_img = PhotoImage(file="images/mute.png")
volume_btn = ttk.Button(player, image=volume_btn_img, compound='image', style='player.TButton', command=show_volume_scale)
volume_btn.grid(column=5, row=10, padx=(22,0), pady=(0,5), sticky=(E,S)) 

vol=DoubleVar(value=1.0) 
vol_slider = ttk.Scale(player, orient=VERTICAL, variable=vol, length=50.0, from_=1.0, to=0, style="style.Vertical.TScale", command=set_volume)


window.protocol('WM_DELETE_WINDOW', wquit)
window.mainloop()



