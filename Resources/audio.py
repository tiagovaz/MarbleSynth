from pyo import *
from config import config
import os

# Dump function to pass to TrigFunc before deleting AudioNode objects
# Je cherche encore s'il n'y a pas une solution interne a l'objet...
#def dump():
#    pass
    
class AudioNode:
    """
    Class parente des processus audio. Cette classe prend en charge la gestion
    des parametres `p1` et `p2` (position X-Y des cercles), l'envoi du son vers
    les HPs ou vers d'autres objets audio ainsi que l'entree du clavier midi pour
    donner la frequence de base aux differents sons de synthese.
    
    arguments:
        mode : int, mode de conversion des notes midi. 0 = midi, 1 = Hz, 2 = transpo.

    """
    def __init__(self, mode=1):
        self.vnode = None
        self.chnls = config["chnls"]
        self.table1 = LinTable()
        self.table2 = LinTable()
        self._notein = Notein(poly=10, scale=mode)
        self._bendin = Bendin(brange=2, scale=1)
        self.pitch = self._notein["pitch"] * self._bendin
        self.amp = MidiAdsr(self._notein["velocity"], attack=0.005, decay=0.1, sustain=0.7, release=1)
        self._trig = Thresh(self._notein["velocity"])
        self._func = TrigFunc(self._trig, self.go, range(10))
        self.p1 = TrigLinseg(self._trig, [(0,0), (1,0)])
        self.p2 = TrigLinseg(self._trig, [(0,0), (1,0)])
        self._endFunc = TrigFunc(self.p1["trig"], self.end, range(10))

    def cleanup(self):
        self._func.cleanFuncRefs()
        self._endFunc.cleanFuncRefs()
        self.vnode = None
        
    def go(self, arg):
        self.vnode.startMarble(arg)

    def end(self, arg):
        self.vnode.endMarble(arg)
        
    def setVisualNode(self, node):
        self.vnode = node

    def replaceTable(self, which, table):
        pts = len(table)
        step = 1.0 / (pts-1)
        final_list = []
        for i, value in enumerate(table):
            final_list.append( (i*step, value) )
        if which == 1:
            self.p1.replace(final_list)
        elif which == 2:
            self.p2.replace(final_list)

    def setP1(self, x):
        self.table1.replace([(0,x), (8192,x)])

    def setP2(self, x):
        self.table2.replace([(0,x), (8192,x)])

    def setAmp(self, x):
        self.amp.mul = x

    def out(self):
        self.outmix.out()
        return self

    def sig(self):
        return self.outmix

# Liste des modules disponibles pour l'ajout dynamique
audio_modules = []

extern_path = os.path.join(os.getcwd(), "externals")
extern_modules = os.listdir(extern_path)
for file in extern_modules:
    if file.endswith(".py"):
        execfile(os.path.join(extern_path, file), locals())
        audio_modules.append(CLASS)
        


