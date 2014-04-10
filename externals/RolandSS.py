class RolandSS(AudioNode):
    name = "Roland Super Saw"
    color = (0, 255, 0)
    def __init__(self):
        AudioNode.__init__(self, mode=1)
        self.ratio = Scale(self.p1, outmin=0.01, outmax=4, exp=4)
        self.index = Scale(self.p2, outmax=20, exp=2)
        self.sig1 = SuperSaw(freq=self.pitch, detune=self.p1, bal=self.p2, mul=self.amp*0.3).mix(1)
        self.sig2 = SuperSaw(freq=self.pitch*1.01, detune=self.p1, bal=self.p2, mul=self.amp*0.3).mix(1)
        self.outmix = Mix([self.sig1, self.sig2], voices=self.chnls)

CLASS = RolandSS