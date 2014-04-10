class SumOscMod(AudioNode):
    name = "Sumation Osc"
    color = (0, 0, 255)
    def __init__(self):
        AudioNode.__init__(self, mode=1)
        self.ratio = Scale(self.p1, outmin=0.01, outmax=4, exp=4)
        self.index = Scale(self.p2, outmax=0.99, exp=2)
        self.fm1 = SumOsc(freq=self.pitch, ratio=self.ratio, index=self.index, mul=self.amp*0.1).mix(1)
        self.fm2 = SumOsc(freq=self.pitch*1.01, ratio=self.ratio, index=self.index, mul=self.amp*0.1).mix(1)
        self.fm3 = SumOsc(freq=self.pitch*0.993, ratio=self.ratio, index=self.index, mul=self.amp*0.1).mix(1)
        self.fm4 = SumOsc(freq=self.pitch*1.005, ratio=self.ratio, index=self.index, mul=self.amp*0.1).mix(1)
        self.outmix = Mix([self.fm1, self.fm2, self.fm3, self.fm4], voices=self.chnls)

CLASS = SumOscMod