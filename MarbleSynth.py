import wx, os
from pyo import *
from Resources.surface import Surface
from Resources.audio import *
from Resources.config import config

pm_list_devices()

s = Server()
s.setMidiInputDevice(3)
s.boot().start()

class MyFrame(wx.Frame):
    def __init__(self, parent=None, id=wx.ID_ANY, title="Marble", pos=(50,50), size=(500,500)):
        wx.Frame.__init__(self, parent, id, title, pos, size)
        # variables
        self.currentFile = None
        
        # Creation de la barre de menu
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        modmenu = wx.Menu()
        id = 8000 # id offset pour le sous-menu de modules
        for i, module in enumerate(audio_modules):
            modmenu.Append(id, module.name+"\tCtrl+%d" % (i+1))
            id += 1
        self.Bind(wx.EVT_MENU, self.addModuleFromMenu, id=8000, id2=id)
        filemenu.AppendSubMenu(modmenu, "Add Module...")
        filemenu.AppendSeparator()
        filemenu.Append(wx.ID_NEW, "New\tCtrl+N")
        self.Bind(wx.EVT_MENU, self.new, id=wx.ID_NEW)
        filemenu.Append(wx.ID_OPEN, "Open\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.open, id=wx.ID_OPEN)
        filemenu.Append(wx.ID_SAVE, "Save\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.save, id=wx.ID_SAVE)
        filemenu.Append(wx.ID_SAVEAS, "Save As...\tShift+Ctrl+S")
        self.Bind(wx.EVT_MENU, self.saveas, id=wx.ID_SAVEAS)
        filemenu.AppendSeparator()
        quititem = filemenu.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "")
        self.Bind(wx.EVT_MENU, self.onQuit, id=wx.ID_EXIT)
        
        actionmenu = wx.Menu()
        actionmenu.Append(10000, "Record...\tCtrl+R", kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.actionMode, id=10000)

        menubar.Append(filemenu, "&File")
        menubar.Append(actionmenu, "&Action")
        self.SetMenuBar(menubar)

        self.panel = wx.Panel(self)
        self.surface = Surface(self.panel, pos=(50,50), size=(400,400))
        self.Show()

    # Efface les nodes presents dans l'interface.
    def new(self, evt):
        self.surface.clear()
        self.currentFile = None
        self.SetTitle("Marble")

    # Ouvre un dialogue standard pour la selection d'un fichier
    def open(self, evt):
        # Filtre les fichiers disponibles en fonction de l'extension .mbl
        wildcard = "Marble file (.mbl)|*.mbl"
        # Creation du dialogue
        dlg = wx.FileDialog(self, "Open Marble file...", os.path.expanduser("~"), 
                            wildcard=wildcard, style=wx.FD_OPEN)
        # La methode ShowModal() ouvre une fenetre flottante qui attend le resultat
        # de l'action (bouton "Open" ou "Cancel" pour retourner la valeur. On 
        # utilise le retour pour decider de la suite des operations. Le bouton
        # "Open" retourne la constante wx.ID_OK.
        if dlg.ShowModal() == wx.ID_OK:
            # Recupere le path du fichier choisi
            path = dlg.GetPath()
            # On s'assure qu'un fichier a bel et bien ete choisi
            if path == "":
                return
            # On garde en memoire le path du fichier (principalement pour la methode "Save".
            self.currentFile = path
            # On ajuste le titre de la fenetre
            self.SetTitle("Marble - %s" % os.path.split(path)[1])
            # On elimine les nodes existants
            self.surface.clear()
            # Ouverture du fichier en mode lecture
            f = open(path, "r")
            # Lecture du texte dans un gros string
            text = f.read()
            # on ferme le fichier
            f.close()
            # Le string contient une liste de dictionnaires python.
            # eval(statement) evalue le texte en tant que commande python.
            state = eval(text)
            # Pour chaque dictionnaire (un node) dans la liste
            for d in state:
                # On cree un module
                if self.addModuleFromOpen(d["module"]):
                    del d["module"]
                    # On lui envoie les valeurs de la sauvegarde
                    self.surface.nodes[-1].setState(d)
        # Ne pas oublier de detruire le dialogue
        dlg.Destroy()

    # Sauvegarde l'etat courant dans le fichier courant si possible
    # sinon, bascule sur la methode Save As...
    def save(self, evt):
        if self.currentFile == None:
            self.saveas(evt)
        else:
            f = open(self.currentFile, "w")
            f.write(str(self.surface.getCurrentState()))
            f.close()
            
    # Ouvre un dialogue standard pour la sauvegarde de fichier
    def saveas(self, evt):
        # Filtre les fichiers visibles en fonction de l'extension .mbl        
        wildcard = "Marble file (.mbl)|*.mbl"
        # Creation du dialogue avec le style wx.FD_SAVE
        dlg = wx.FileDialog(self, "Save file as...", os.path.expanduser("~"), "mon_template.mbl", 
                            wildcard=wildcard, style=wx.FD_SAVE)
        # Si "Open", et non "Cancel"
        if dlg.ShowModal() == wx.ID_OK:
            # Recupere le path du nouveau fichier
            # ou du fichier selectionne. Pas de sauvegarde, il faudrait verifier nous-memes si
            # le fichier existe et afficher un avertissement
            path = dlg.GetPath()
            # On garde en memoire le path du fichier
            self.currentFile = path
            # On ajuste la barre de titre
            self.SetTitle("Marble - %s" % path)
            # Ouverture du fichier en mode ecriture
            f = open(path, "w")
            # On ecrit une representation en "string" de la liste de dictionnaire de l'etat courant
            f.write(str(self.surface.getCurrentState()))
            # On ferme le fichier
            f.close()
        # On detruit le dialogue
        dlg.Destroy()

    def actionMode(self, evt):
        self.surface.setRecord(evt.GetInt())

    def onQuit(self, evt):
        # Arret du serveur audio
        s.stop()
        # Menage avant de quitter
        for node in self.surface.nodes:
            # Elimine la reference au node visuel dans la classe AudioNode
            #node.module.setVisualNode(None)
            # Elimine les references aux methodes des TrigFunc
            node.module.cleanup()
            #node.module._func.function = dump
            #node.module._endFunc.function = dump
        self.Destroy()

    def addModuleFromOpen(self, name):
        for i, module in enumerate(audio_modules):
            if name == module.name:
                self.addModule(i)
                return True
        msg = 'Module "%s" not found!' % name
        dlg = wx.MessageDialog(self, msg, "WARNING!", style=wx.ICON_ERROR|wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
        return False
        
    def addModuleFromMenu(self, evt):
        # Gestion de l'index en fonction des ids des commandes menu
        index = evt.GetId() - 8000
        self.addModule(index)
        
    def addModule(self, index):
        module = audio_modules[index]
        self.surface.addNode(module().out(), module.color)

app = wx.App(False)
frame = MyFrame()
app.MainLoop()
    