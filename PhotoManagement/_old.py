import os
import sys
from datetime import datetime
import time
from time import strptime
import json
from pathlib import Path

import numpy as np
import piexif
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


class PhotoProcessor (object):
    def __init__(self, dest_dir):
        self.dprec = ''
        self.dest_dir = dest_dir

    def get_created_time_from_json(self, pth):
        json_pth = pth + '.json'
        if not os.path.exists(json_pth):
            return None,None

        f = open(json_pth, 'r')
        dat = json.load(f)
        f.close()
        ts = int(dat['photoTakenTime']['timestamp'])
        dt = datetime.fromtimestamp(ts)
        ct = dt.strftime("%Y:%m:%d %H:%M:%S").encode("utf-8")

        return dt,ct

    def process_png(self, pth):
        print("Traitement %s" % pth)
        return self.process_video(pth)

        # parser = createParser(pth)
        # metadata = extractMetadata(parser)
        # d = metadata.exportDictionary()

    def process_manually(self, pth):
        d = input("Date JJ/MM/AAAA [%s] : " % self.dprec)
        if d == '':
            d = self.dprec
        self.dprec = d
        j,m,a = [int(x) for x in d.split('/')]
        dt = datetime(year=a, month=m, day=j, hour=12, minute=0, second=0)
        ct = "%.4i:%.2i:%.2i 12:00:00" % (a,m,j)
        ct = ct.encode('utf-8')

        return dt,ct

    def process_exif(self, pth):
        print("Traitement %s" % pth)
        _,ext = os.path.splitext(pth.lower())
        s = os.stat(pth)
        dt = datetime.fromtimestamp(s.st_ctime)
        ct = dt.strftime("%Y:%m:%d %H:%M:%S").encode("utf-8")

        d1 = None
        d2 = None

        exif_dict = piexif.load(pth)
        if not 'Exif' in exif_dict.keys():
            exif_keys['Exif'] = {}

        if 36868 in exif_dict["Exif"]:
            d1 = exif_dict["Exif"][36868]
        if 36867 in exif_dict["Exif"]:
            d2 = exif_dict["Exif"][36867]

        try:
            ct1 = d1
            dt1 = datetime.strptime(d1.decode('utf-8'), '%Y:%m:%d %H:%M:%S')
            d1_ok = True
        except:
            d1_ok = False

        try:
            ct2 = d2
            dt2 = datetime.strptime(d2.decode('utf-8'), '%Y:%m:%d %H:%M:%S')
            d2_ok = True
        except:
            d2_ok = False

        if not d1_ok or not d2_ok or np.abs((dt1-dt2).total_seconds()) < 86400:
            if d1_ok:
                # d1 : b'2019:12:20 21:41:36'
                dt = datetime.strptime(d1.decode('utf-8'), '%Y:%m:%d %H:%M:%S')
                ct = d1
            elif d2_ok:
                dt = datetime.strptime(d2.decode('utf-8'), '%Y:%m:%d %H:%M:%S')
                ct = d2
            else:
                dt,ct = self.get_created_time_from_json(pth)
                if dt is None:
                    try:
                        ds = os.path.split(pth)[-1][6:-9]
                        dt = datetime.strptime(ds, '%y-%m-%d %H-%M-%S')
                        ct = dt.strftime("%Y:%m:%d %H:%M:%S").encode("utf-8")
                    except:
                        print("[ERREUR]Analyse de %s -> %s" % (pth,ds))
                        dt = None

                if dt is None:
                    print("[ERREUR]Aucune date trouvee dans EXIF", pth)
                    dt,ct = self.process_manually(pth)

        else:
            print('[ERREUR]Dates incoherentes',pth, d1,d2)
            return

        exif_dict["Exif"][36868] = ct
        exif_dict["Exif"][36867] = ct

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes,pth)

        return dt

    def process_video(self, pth):
        print("Traitement %s" % pth)
        _,ext = os.path.splitext(pth.lower())
        dt,ct = self.get_created_time_from_json(pth)
            
        if dt is None:
                try:
                    ds = os.path.split(pth)[-1][6:-9]
                    dt = datetime.strptime(ds, '%y-%m-%d %H-%M-%S')
                    ct = dt.strftime("%Y:%m:%d %H:%M:%S").encode("utf-8")
                except:
                    print("[ERREUR]Analyse de %s -> %s" % (pth,ds))
                    dt = None
            
        if dt is None:
            print("[ERREUR]Aucune date trouvee pour vidéo", pth)
            dt,ct = self.process_manually(pth)

        return dt

    def move_file(self, pth, type, dt):
        if dt is None:
            print("[ERREUR]Impossible de déterminer la date de prise de vue de %s" % pth)
            return

        _,ext = os.path.splitext(pth.lower())
        modTime = time.mktime(dt.timetuple())
        os.utime(pth, (modTime, modTime))
        dr = os.path.join(self.dest_dir, "%.4i" % dt.year, "%.2i" % dt.month)
        Path(dr).mkdir(parents=True, exist_ok=True)
        # Photo 19-12-27 13-49-15 0265
        Y = dt.year
        M = dt.month
        D = dt.day
        h = dt.hour
        m = dt.minute
        s = dt.second
        new_pth = os.path.join(dr,"%s %.2i-%.2i-%.2i %.2i-%.2i-%.2i 0001%s" % (type,Y,M,D,h,m,s,ext))
        os.rename(pth, new_pth)

    def run(self, root):
        for dirpath, dirnames, filenames in os.walk(root):
            for fic in filenames:
                pth = os.path.join(dirpath,fic)
                _,ext = os.path.splitext(fic.lower())
                if ext == '.jpg' or ext == '.jpeg' or ext == '.tiff':
                    dt = self.process_exif(pth)
                    # dt = self.process_png(pth)
                    self.move_file(pth, 'Photo', dt)
                elif ext == '.png' or ext == '.heic' or ext == '.gif':
                    dt = self.process_png(pth)
                    self.move_file(pth, 'Photo', dt)
                elif ext == '.mov' or ext == '.mp4' or ext == '.avi' or ext == '.mpg' or ext == '.m4v':
                    dt = self.process_video(pth)
                    self.move_file(pth, 'Video', dt)
                elif ext == '.json':
                    pass
                else:
                    print("[ERREUR]%s : extension inconnu" % pth)

                # exit(0)

a = PhotoProcessor(sys.argv[1])
# a.run('Takeout')
a.run('a_traiter')
