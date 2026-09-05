"""Optional interactive evidence viewer. Headless tests do not require Tk/Pillow."""
import argparse,pathlib,tkinter as tk
from PIL import Image,ImageTk
p=argparse.ArgumentParser();p.add_argument('folder',nargs='?',default='reports/captures/play');a=p.parse_args()
files=sorted(pathlib.Path(a.folder).glob('frame_*.ppm'),key=lambda f:int(f.stem.split('_')[1]))
if not files:raise SystemExit('No captured PPM frames in '+a.folder)
root=tk.Tk();root.title('Dr. Micro HDL simulation captures');label=tk.Label(root);label.pack();caption=tk.Label(root);caption.pack()
def show(n):
 f=files[int(float(n))];im=Image.open(f).transpose(Image.Transpose.ROTATE_90).resize((448,512),Image.Resampling.NEAREST);pic=ImageTk.PhotoImage(im);label.configure(image=pic);label.image=pic;caption.configure(text=str(f))
slider=tk.Scale(root,from_=0,to=len(files)-1,orient=tk.HORIZONTAL,length=448,command=show);slider.pack();show(0)
root.bind('<Right>',lambda e:slider.set(min(len(files)-1,slider.get()+1)));root.bind('<Left>',lambda e:slider.set(max(0,slider.get()-1)));root.mainloop()
