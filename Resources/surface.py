import wx
from audio import audio_modules

class Node:
    """
    La classe Node sert a gerer la position et le comportement d'un
    cercle (associe a un objet audio) sur la surface de dessin. Autant
    de Node doivent etre crees qu'il y a d'objets audio dans le processus.
    
    arguments:
        x : int, position de depart sur l'axe des X
        y : int, position de depart sur l'axe des Y
        col : tuple RGB, couleur asociee au Node
        audio_mod : module audio asociee au Node

    """
    def __init__(self, x, y, col, audio_mod):
        self.w, self.h = 400, 400
        self.pos = (x, y)
        self.col = col
        self.alpha = 128
        self.module = audio_mod
        self.module.setVisualNode(self)
        self.traj = []
        self.marbles = [None for i in range(10)]

    def delete(self):
        # Elimine les references qui peuvent causer conflit
        #self.module.setVisualNode(None)
        self.module.cleanup()
        #self.module._func.function = dump
        #self.module._endFunc.function = dump

    # Dictionnaire de sauvegarde.
    # self.module.__class__ contient une reference a la classe audio du module
    # audio_modules.index(x) retourne la position de la valeur donnee en "x".
    def getCurrentState(self):
        d = {"pos": self.pos,
             "col": self.col,
             "alpha": self.alpha,
             "traj": self.traj,
             "module": self.module.name}
        return d

    # Assigne le data a l'ouverture d'un fichier
    def setState(self, d):
        self.col = d["col"]
        self.traj = d["traj"]
        self.setAlpha(d["alpha"])
        self.setPos(d["pos"])

    def setSize(self, w, h):
        self.w = w
        self.h = h

    def setNormPos(self, x, y):
        self.module.setP1(x)
        self.module.setP2(y)
        
    def setPos(self, pt):
        self.pos = (pt[0], pt[1])
        if self.traj != []:
            self.createAudioLines()

    def getPos(self):
        return self.pos
 
    def getCol(self):
        return self.col

    def getAlpha(self):
        return self.alpha
    
    def setAlpha(self, alpha):
        self.alpha = alpha
        self.module.setAmp(alpha/255.)

    def contains(self, pt):
        """"
        Retourne True si la position donnee en argument (position de la
        souris en pixel) se trouve a l'interieur du rectangle `area`.

        """
        area = wx.Rect(self.pos[0]-7, self.pos[1]-7, 15, 15)
        if area.Contains(pt):
            return True
        else:
            return False

    def initTraj(self):
        self.traj = [(0,0)]
    
    def addTrajPoint(self, pos):
        posx = pos[0] - self.pos[0]
        posy = pos[1] - self.pos[1]
        self.traj.append((posx, posy))
        self.createAudioLines()
    
    def createAudioLines(self):
        p1 = []
        p2 = []
        for p in self.traj:
            x = (p[0]+self.pos[0]) / float(self.w)
            y = 1 - (p[1]+self.pos[1]) / float(self.h)
            p1.append(x)
            p2.append(y)
        self.module.replaceTable(1, p1)
        self.module.replaceTable(2, p2)

    def getDraw(self):
        return [(p[0]+self.pos[0], p[1]+self.pos[1]) for p in self.traj]
        
    def startMarble(self, num):
        if len(self.traj) > 0:
            self.marbles[num] = self.traj[0]

    def endMarble(self, num):
        self.marbles[num] = None

    def updateMarble(self, num):
        return (self.module.p1.get(all=True)[num], self.module.p2.get(all=True)[num])

class Surface(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.pos = None
        self.selected = None
        self.nodes = []
        # variable qui definit l'action ("move", "alpha", "record")
        self.action = "move"
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.autoRefresh)
        self.timer.Start(75)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.MouseRightDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_RIGHT_UP, self.MouseUp)
        self.Bind(wx.EVT_MOTION, self.Motion)

    # Menage, avant l'ouverture d'un nouveau fichier ou avant de quitter
    def clear(self):
        [node.delete() for node in self.nodes]
        self.nodes = []

    # Recupere l'etat courant de tous les nodes
    def getCurrentState(self):
        return [node.getCurrentState() for node in self.nodes]

    def autoRefresh(self, evt):
        self.Refresh()

    def setRecord(self, state):
        if state:
            self.action = "record"
        else:
            self.action = "move"

    def addNode(self, audio_mod, col):
        w,h = self.GetSize()
        self.nodes.append(Node(w/2, h/2, col, audio_mod))
        self.nodes[-1].setSize(w, h) # EVT_SIZE
        self.Refresh()

    def OnPaint(self, evt):
        w,h = self.GetSize()
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext_Create(dc)
        dc.SetBrush(wx.Brush("#444444"))
        dc.DrawRectangle(0,0,w,h)

        dc.SetPen(wx.Pen("#666666"))
        dc.SetTextForeground("#AAAAAA")
        for i in range(0, w, 50):
            dc.DrawLine(i, 0, i, h)
            dc.DrawText("%.2f" % (i/float(w)), i+2, h-12)
            #tw, th = dc.GetTextExtent("%.2f" % (i/float(w)))
        for i in range(0, h, 50):
            dc.DrawLine(0, i, w, i)
            dc.DrawText("%.2f" % (1-i/float(h)), 2, i+2)

        if self.pos != None:
            dc.SetPen(wx.Pen("#AAAAAA"))
            x = self.pos[0] / float(w)
            y = 1 - self.pos[1] / float(h)
            dc.DrawText("%.3f, %.3f" % (x, y), w-80, 5)

            if self.selected != None:
                if self.action == "move":
                    self.nodes[self.selected].setPos(self.pos)
                    self.nodes[self.selected].setNormPos(x, y)
                    dc.DrawLine(0, self.pos[1], w, self.pos[1])
                    dc.DrawLine(self.pos[0], 0, self.pos[0], h)
                elif self.action == "alpha":
                    amp = self.nodes[self.selected].getAlpha() / 255.
                    pos = self.nodes[self.selected].getPos()
                    dc.DrawText("%.3f" % amp, pos[0]+10, pos[1]-10)
            
        dc.SetTextForeground("#FFFFFF")
        for i, node in enumerate(self.nodes):
            col = node.getCol()
            color = wx.Colour(col[0], col[1], col[2], node.getAlpha())

            if len(node.traj) >= 2:
                try:
                    gc.SetPen(wx.Pen(color, width=2))
                    gc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                    gc.DrawLines(node.getDraw())
                except Exception, e:
                    print str(e)

            gc.SetBrush(wx.Brush(color))
            gc.SetPen(wx.Pen("#FFFFFF", width=1))
            gc.DrawEllipse(node.getPos()[0]-7, node.getPos()[1]-7, 15, 15)
            dc.DrawText(str(i), node.getPos()[0]-3, node.getPos()[1]-5)

            gc.SetBrush(wx.Brush(color))
            gc.SetPen(wx.Pen(color, width=1))
            for i, marble in enumerate(node.marbles):
                if marble != None:
                    norm_pos = node.updateMarble(i)
                    posx = norm_pos[0] * w
                    posy = (1.0 - norm_pos[1]) * h
                    gc.DrawEllipse(posx-5, posy-5, 10, 10)

    def MouseDown(self, evt):
        self.CaptureMouse()
        self.pos = evt.GetPosition()
        # verifie si le bouton gauche a ete enfonce sur un cercle
        for i, node in enumerate(self.nodes):
            if node.contains(self.pos):
                self.selected = i
                if self.action == "record":
                    self.nodes[i].initTraj()
                else:
                    self.action = "move"
                break
        self.Refresh()

    def MouseRightDown(self, evt):
        if self.action != "record":
            self.CaptureMouse()
            self.pos = evt.GetPosition()
            for i, node in enumerate(self.nodes):
                if node.contains(self.pos):
                    self.selected = i
                    self.action = "alpha"
        
    def MouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
            self.pos = self.selected = None
            self.Refresh()

    def Motion(self, evt):
        w,h = self.GetSize()
        pos = evt.GetPosition()
        if self.HasCapture():
            if self.action == "move":
                pos = self.clipArea(pos, w, h)
                if self.selected != None:
                    if self.nodes[self.selected].traj != []:
                        if self.clipListArea(self.nodes[self.selected].getDraw(), w, h):
                            self.pos = pos
                    else:
                        self.pos = pos
                else:
                    self.pos = pos
            elif self.action == "alpha":
                if self.selected != None:
                    # Right-click, on modifie l'alpha du Node
                    circlePos = self.nodes[self.selected].getPos()[1]
                    alpha = circlePos - pos[1] + 128
                    if alpha < 0:
                        alpha = 0
                    elif alpha > 255:
                        alpha = 255
                    self.nodes[self.selected].setAlpha(alpha)
            elif self.action == "record":
                if self.selected != None:
                    pos = self.clipArea(pos, w, h)
                    self.nodes[self.selected].addTrajPoint(pos)
            self.Refresh()

    def clipArea(self, pos, w, h):
        if pos[0] < 2:
            pos[0] = 2
        elif pos[0] > (w-2):
            pos[0] = w-2
        if pos[1] < 2:
            pos[1] = 2
        elif pos[1] > (h-2):
            pos[1] = h-2
        return pos

    def clipListArea(self, listpos, w, h):
        for pos in listpos:
            if pos[0] < 2 or pos[0] > (w-2):
                flag = False
                return False
            if pos[1] < 2 or pos[1] > (h-2):
                flag = False
                return False
        return True

if __name__ == "__main__":
    class MyFrame(wx.Frame):
        def __init__(self, parent=None, id=wx.ID_ANY, title="Interface 2D", pos=(50,50), size=(500,500)):
            wx.Frame.__init__(self, parent, id, title, pos, size)
            self.panel = wx.Panel(self)
            self.surface = Surface(self.panel, pos=(50,50), size=(150,150), callback=self.getXY)
            self.Show()
            
        def getXY(self, x, y):
            print x, y

    app = wx.App(False)
    frame = MyFrame()
    app.MainLoop()