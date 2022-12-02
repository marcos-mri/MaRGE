"""
Created on Thu June 2 2022
@author: J.M. Algarín, MRILab, i3M, CSIC, Valencia
@email: josalggui@i3m.upv.es
@Summary: rare sequence class
"""

import os
import sys
#*****************************************************************************
# Add path to the working directory
path = os.path.realpath(__file__)
ii = 0
for char in path:
    if (char=='\\' or char=='/') and path[ii+1:ii+14]=='PhysioMRI_GUI':
        sys.path.append(path[0:ii+1]+'PhysioMRI_GUI')
        sys.path.append(path[0:ii+1]+'marcos_client')
    ii += 1
#******************************************************************************
import numpy as np
import experiment as ex
import scipy.signal as sig
import configs.hw_config as hw # Import the scanner hardware config
import seq.mriBlankSeq as blankSeq  # Import the mriBlankSequence for any new sequence.
from plotview.spectrumplot import SpectrumPlot # To plot nice 1d images
from plotview.spectrumplot import Spectrum3DPlot # To show nice 2d or 3d images
import pyqtgraph as pg

#*********************************************************************************
#*********************************************************************************
#*********************************************************************************

class RARE(blankSeq.MRIBLANKSEQ):
    def __init__(self):
        super(RARE, self).__init__()
        # Input the parameters
        self.addParameter(key='seqName', string='RAREInfo', val='RARE')
        self.addParameter(key='nScans', string='Number of scans', val=1, field='IM')
        self.addParameter(key='freqOffset', string='Larmor frequency offset (kHz)', val=0.0, field='RF')
        self.addParameter(key='rfExFA', string='Exitation flip angle (º)', val=90, field='RF')
        self.addParameter(key='rfReFA', string='Refocusing flip angle (º)', val=180, field='RF')
        self.addParameter(key='rfExTime', string='RF excitation time (us)', val=35.0, field='RF')
        self.addParameter(key='rfReTime', string='RF refocusing time (us)', val=70.0, field='RF')
        self.addParameter(key='echoSpacing', string='Echo spacing (ms)', val=20.0, field='SEQ')
        self.addParameter(key='preExTime', string='Preexitation time (ms)', val=0.0, field='SEQ')
        self.addParameter(key='inversionTime', string='Inversion time (ms)', val=0.0, field='SEQ')
        self.addParameter(key='repetitionTime', string='Repetition time (ms)', val=300., field='SEQ')
        self.addParameter(key='fov', string='FOV[x,y,z] (cm)', val=[15.0, 15.0, 15.0], field='IM')
        self.addParameter(key='dfov', string='dFOV[x,y,z] (mm)', val=[0.0, 0.0, 0.0], field='IM')
        self.addParameter(key='nPoints', string='nPoints[rd, ph, sl]', val=[30, 1, 1], field='IM')
        self.addParameter(key='etl', string='Echo train length', val=5, field='SEQ')
        self.addParameter(key='acqTime', string='Acquisition time (ms)', val=2.0, field='SEQ')
        self.addParameter(key='axesOrientation', string='Axes[rd,ph,sl]', val=[0, 1, 2], field='IM')
        self.addParameter(key='axesEnable', string='Axes enable', val=[1, 0, 0], field='IM')
        self.addParameter(key='sweepMode', string='Sweep mode', val=1, field='SEQ')
        self.addParameter(key='rdGradTime', string='Rd gradient time (ms)', val=2.5, field='OTH')
        self.addParameter(key='rdDephTime', string='Rd dephasing time (ms)', val=1.0, field='OTH')
        self.addParameter(key='phGradTime', string='Ph gradient time (ms)', val=1.0, field='OTH')
        self.addParameter(key='rdPreemphasis', string='Rd preemphasis', val=1.0, field='OTH')
        self.addParameter(key='dummyPulses', string='Dummy pulses', val=1, field='SEQ')
        self.addParameter(key='shimming', string='Shimming (*1e4)', val=[-12.5, -12.5, 7.5], field='OTH')
        self.addParameter(key='parFourierFraction', string='Partial fourier fraction', val=1.0, field='OTH')
        self.addParameter(key='freqCal', string='Calibrate frequency (0 or 1)', val=1, field='OTH')

    def sequenceInfo(self):
        print(" ")
        print("3D RARE sequence")
        print("Author: Dr. J.M. Algarín")
        print("Contact: josalggui@i3m.upv.es")
        print("mriLab @ i3M, CSIC, Spain \n")
        print("Sweep modes: 0:k20, 1:02k, 2:k2k")
        print("Axes: 0:x, 1:y, 2:z")

    def sequenceTime(self):
        nScans = self.mapVals['nScans']
        nPoints = np.array(self.mapVals['nPoints'])
        etl = self.mapVals['etl']
        repetitionTime = self.mapVals['repetitionTime']
        parFourierFraction = self.mapVals['parFourierFraction']

        # check if rf amplitude is too high
        rfExFA = self.mapVals['rfExFA'] / 180 * np.pi  # rads
        rfReFA = self.mapVals['rfReFA'] / 180 * np.pi  # rads
        rfExTime = self.mapVals['rfExTime']  # us
        rfReTime = self.mapVals['rfReTime']  # us
        rfExAmp = rfExFA / (rfExTime * hw.b1Efficiency)
        rfReAmp = rfReFA / (rfReTime * hw.b1Efficiency)
        if rfExAmp>1 or rfReAmp>1:
            print("RF amplitude is too high, try with longer RF pulse time.")
            return(0)

        seqTime = nPoints[1]/etl*nPoints[2]*repetitionTime*1e-3*nScans*parFourierFraction/60
        seqTime = np.round(seqTime, decimals=1)
        return(seqTime)  # minutes, scanTime

    def sequenceRun(self, plotSeq=0, demo=False):
        init_gpa=False # Starts the gpa
        demo = False

        # Create the inputs automatically as a property of the class
        for key in self.mapKeys:
            setattr(self, key, self.mapVals[key])

        # Create the inputs automatically. For some reason it only works if there is a few code later...
        # for key in self.mapKeys:
        #     locals()[key] = self.mapVals[key]
        #     if not key in locals():
        #         print('Error')
        #         locals()[key] = self.mapVals[key]

        # Create the inputs manually, pufff
        # seqName = self.mapVals['seqName']
        # nScans = self.mapVals['nScans']
        # larmorFreq = self.mapVals['larmorFreq']# MHz
        # rfExFA = self.mapVals['rfExFA']/180*np.pi # rads
        # rfReFA = self.mapVals['rfReFA']/180*np.pi # rads
        # rfExTime = self.mapVals['rfExTime'] # us
        # rfReTime = self.mapVals['rfReTime'] # us
        # echoSpacing = self.mapVals['echoSpacing'] # ms
        # preExTime = self.mapVals['preExTime'] # ms
        # inversionTime = self.mapVals['inversionTime'] # ms
        # repetitionTime = self.mapVals['repetitionTime'] # ms
        # fov = np.array(self.mapVals['fov']) # cm
        # dfov = np.array(self.mapVals['dfov']) # mm
        # nPoints = np.array(self.mapVals['nPoints'])
        # etl = self.mapVals['etl']
        # acqTime = self.mapVals['acqTime'] # ms
        # axes = self.mapVals['axes']
        # axesEnable = self.mapVals['axesEnable']
        # sweepMode = self.mapVals['sweepMode']
        # rdGradTime = self.mapVals['rdGradTime'] # ms
        # rdDephTime = self.mapVals['rdDephTime'] # ms
        # phGradTime = self.mapVals['phGradTime'] # ms
        # rdPreemphasis = self.mapVals['rdPreemphasis']
        # drfPhase = self.mapVals['drfPhase'] # degrees
        # dummyPulses = self.mapVals['dummyPulses']
        # shimming = np.array(self.mapVals['shimming']) # *1e4
        # parFourierFraction = self.mapVals['parFourierFraction']
        # freqCal = self.mapVals['freqCal']

        # Conversion of variables to non-multiplied units
        self.freqOffset = self.freqOffset*1e3
        self.rfExTime = self.rfExTime*1e-6
        self.rfReTime = self.rfReTime*1e-6
        self.fov = np.array(self.fov)*1e-2
        self.dfov = np.array(self.dfov)*1e-3
        self.echoSpacing = self.echoSpacing*1e-3
        self.acqTime = self.acqTime*1e-3
        self.shimming = np.array(self.shimming)*1e-4
        self.repetitionTime= self.repetitionTime*1e-3
        self.preExTime = self.preExTime*1e-3
        self.inversionTime = self.inversionTime*1e-3
        self.rdGradTime = self.rdGradTime*1e-3
        self.rdDephTime = self.rdDephTime*1e-3
        self.phGradTime = self.phGradTime*1e-3

        # Miscellaneous
        self.fov = self.fov[self.axesOrientation]
        self.dfov = self.dfov[self.axesOrientation]
        self.freqOffset = self.freqOffset*1e6 # MHz
        gradRiseTime = 400e-6       # s
        gSteps = int(gradRiseTime*1e6/5)*0+1
        addRdPoints = 10             # Initial rd points to avoid artifact at the begining of rd
        randFactor = 0e-3                        # Random amplitude to add to the phase gradients
        resolution = self.fov/self.nPoints
        rfExAmp = self.rfExFA/(self.rfExTime*1e6*hw.b1Efficiency)*np.pi/180
        rfReAmp = self.rfReFA/(self.rfReTime*1e6*hw.b1Efficiency)*np.pi/180
        self.mapVals['rfExAmp'] = rfExAmp
        self.mapVals['rfReAmp'] = rfReAmp
        self.mapVals['resolution'] = resolution
        self.mapVals['gradRiseTime'] = gradRiseTime
        self.mapVals['randFactor'] = randFactor
        self.mapVals['addRdPoints'] = addRdPoints

        if rfExAmp>1 or rfReAmp>1:
            print("RF amplitude is too high, try with longer RF pulse time.")
            return(0)

        # Matrix size
        nRD = self.nPoints[0]+2*addRdPoints
        nPH = self.nPoints[1]
        nSL = self.nPoints[2]

        # ETL if etl>nPH
        if self.etl>nPH:
            self.etl = nPH

        # parAcqLines in case parAcqLines = 0
        parAcqLines = int(int(self.nPoints[2]*self.parFourierFraction)-self.nPoints[2]/2)
        self.mapVals['partialAcquisition'] = parAcqLines

        # BW
        BW = self.nPoints[0]/self.acqTime*1e-6        # MHz
        BWov = BW*hw.oversamplingFactor     # MHz
        samplingPeriod = 1/BWov             # us

        # Readout gradient time
        if self.rdGradTime<self.acqTime:
            self.rdGradTime = self.acqTime
        self.mapVals['rdGradTime'] = self.rdGradTime * 1e3 # ms

        # Phase and slice de- and re-phasing time
        if self.phGradTime==0 or self.phGradTime>self.echoSpacing/2-self.rfExTime/2-self.rfReTime/2-2*gradRiseTime:
            self.phGradTime = self.echoSpacing/2-self.rfExTime/2-self.rfReTime/2-2*gradRiseTime
        self.mapVals['phGradTime'] = self.phGradTime*1e3 # ms

        # Max gradient amplitude
        rdGradAmplitude = self.nPoints[0]/(hw.gammaB*self.fov[0]*self.acqTime)*self.axesEnable[0]
        phGradAmplitude = nPH/(2*hw.gammaB*self.fov[1]*(self.phGradTime+gradRiseTime))*self.axesEnable[1]
        slGradAmplitude = nSL/(2*hw.gammaB*self.fov[2]*(self.phGradTime+gradRiseTime))*self.axesEnable[2]
        self.mapVals['rdGradAmplitude'] = rdGradAmplitude
        self.mapVals['phGradAmplitude'] = phGradAmplitude
        self.mapVals['slGradAmplitude'] = slGradAmplitude

        # Readout dephasing amplitude
        rdDephAmplitude = 0.5*rdGradAmplitude*(gradRiseTime+self.rdGradTime)/(gradRiseTime+self.rdDephTime)
        self.mapVals['rdDephAmplitude'] = rdDephAmplitude

        # Phase and slice gradient vector
        phGradients = np.linspace(-phGradAmplitude,phGradAmplitude,num=nPH,endpoint=False)
        slGradients = np.linspace(-slGradAmplitude,slGradAmplitude,num=nSL,endpoint=False)

        # Now fix the number of slices to partailly acquired k-space
        nSL = (int(self.nPoints[2]/2)+parAcqLines)*self.axesEnable[2]+(1-self.axesEnable[2])

        # Add random displacemnt to phase encoding lines
        for ii in range(nPH):
            if ii<np.ceil(nPH/2-nPH/20) or ii>np.ceil(nPH/2+nPH/20):
                phGradients[ii] = phGradients[ii]+randFactor*np.random.randn()
        kPH = hw.gammaB*phGradients*(gradRiseTime+self.phGradTime)
        self.mapVals['phGradients'] = phGradients
        self.mapVals['slGradients'] = slGradients

        # Set phase vector to given sweep mode
        ind = self.getIndex(self.etl, nPH, self.sweepMode)
        self.mapVals['sweepOrder'] = ind
        phGradients = phGradients[ind]

        def createSequenceDemo(phIndex=0, slIndex=0, repeIndexGlobal=0, rewrite=True):
            repeIndex = 0
            acqPoints = 0
            orders = 0
            data = []
            while acqPoints + self.etl * nRD <= hw.maxRdPoints and orders <= hw.maxOrders and repeIndexGlobal < nRepetitions:
                if repeIndex == 0:
                    acqPoints += nRD
                    data = np.concatenate((data, np.random.randn(nRD * hw.oversamplingFactor)), axis=0)

                for echoIndex in range(self.etl):
                    if (repeIndex == 0 or repeIndex >= self.dummyPulses):
                        acqPoints += nRD
                        data = np.concatenate((data, np.random.randn(nRD * hw.oversamplingFactor)), axis=0)

                    # Update the phase and slice gradient
                    if repeIndex >= self.dummyPulses:
                        if phIndex == nPH - 1:
                            phIndex = 0
                            slIndex += 1
                        else:
                            phIndex += 1
                if repeIndex >= self.dummyPulses: repeIndexGlobal += 1  # Update the global repeIndex
                repeIndex += 1  # Update the repeIndex after the ETL

            # Return the output variables
            return (phIndex, slIndex, repeIndexGlobal, acqPoints, data)

        def createSequence(phIndex=0, slIndex=0, repeIndexGlobal=0, rewrite=True):
            repeIndex = 0
            if self.rdGradTime==0:   # Check if readout gradient is dc or pulsed
                dc = True
            else:
                dc = False
            acqPoints = 0
            orders = 0
            # Check in case of dummy pulse fill the cache
            if (self.dummyPulses>0 and self.etl*nRD*2>hw.maxRdPoints) or (self.dummyPulses==0 and self.etl*nRD>hw.maxRdPoints):
                print('ERROR: Too many acquired points.')
                return()
            # Set shimming
            self.iniSequence(20, self.shimming, rewrite=rewrite)
            while acqPoints+self.etl*nRD<=hw.maxRdPoints and orders<=hw.maxOrders and repeIndexGlobal<nRepetitions:
                # Initialize time
                tEx = 20e3+self.repetitionTime*repeIndex+self.inversionTime+self.preExTime

                # First I do a noise measurement.
                if repeIndex==0:
                    t0 = tEx-self.preExTime-self.inversionTime-4*self.acqTime
                    self.rxGate(t0, self.acqTime+2*addRdPoints/BW)
                    acqPoints += nRD

                # Pre-excitation pulse
                if repeIndex>=self.dummyPulses and self.preExTime!=0:
                    t0 = tEx-self.preExTime-self.inversionTime-self.rfExTime/2-hw.blkTime
                    self.rfRecPulse(t0, self.rfExTime, rfExAmp, 0)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.preExTime*0.5, -0.005, gSteps, self.axesOrientation[0], self.shimming)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.preExTime*0.5, -0.005, gSteps, self.axesOrientation[1], self.shimming)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.preExTime*0.5, -0.005, gSteps, self.axesOrientation[2], self.shimming)
                    orders = orders+gSteps*6

                # Inversion pulse
                if repeIndex>=self.dummyPulses and self.inversionTime!=0:
                    t0 = tEx-self.inversionTime-self.rfReTime/2-hw.blkTime
                    self.rfRecPulse(t0, self.rfReTime, rfReAmp, 0)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.inversionTime*0.5, 0.005, gSteps, self.axesOrientation[0], self.shimming)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.inversionTime*0.5, 0.005, gSteps, self.axesOrientation[1], self.shimming)
                    self.gradTrap(t0+hw.blkTime+self.rfReTime, gradRiseTime, self.inversionTime*0.5, 0.005, gSteps, self.axesOrientation[2], self.shimming)
                    orders = orders+gSteps*6

                # DC gradient if desired
                if (repeIndex==0 or repeIndex>=self.dummyPulses) and dc==True:
                    t0 = tEx-10e3
                    self.gradTrap(t0, gradRiseTime, 10e3+self.echoSpacing*(self.etl+1), rdGradAmplitude, gSteps, self.axesOrientation[0], self.shimming)
                    orders = orders+gSteps*2

                # Excitation pulse
                t0 = tEx-hw.blkTime-self.rfExTime/2
                self.rfRecPulse(t0,self.rfExTime,rfExAmp,0)

                # Dephasing readout
                if (repeIndex==0 or repeIndex>=self.dummyPulses) and dc==False:
                    t0 = tEx+self.rfExTime/2-hw.gradDelay
                    self.gradTrap(t0, gradRiseTime, self.rdDephTime, rdDephAmplitude*self.rdPreemphasis, gSteps, self.axesOrientation[0], self.shimming)
                    orders = orders+gSteps*2

                # Echo train
                for echoIndex in range(self.etl):
                    tEcho = tEx+self.echoSpacing*(echoIndex+1)

                    # Refocusing pulse
                    t0 = tEcho-self.echoSpacing/2-self.rfReTime/2-hw.blkTime
                    self.rfRecPulse(t0, self.rfReTime, rfReAmp, np.pi/2)

                    # Dephasing phase and slice gradients
                    if repeIndex>=self.dummyPulses:         # This is to account for dummy pulses
                        t0 = tEcho-self.echoSpacing/2+self.rfReTime/2-hw.gradDelay
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, phGradients[phIndex], gSteps, self.axesOrientation[1], self.shimming)
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, slGradients[slIndex], gSteps, self.axesOrientation[2], self.shimming)
                        orders = orders+gSteps*4

                    # Readout gradient
                    if (repeIndex==0 or repeIndex>=self.dummyPulses) and dc==False:         # This is to account for dummy pulses
                        t0 = tEcho-self.rdGradTime/2-gradRiseTime-hw.gradDelay
                        self.gradTrap(t0, gradRiseTime, self.rdGradTime, rdGradAmplitude, gSteps, self.axesOrientation[0], self.shimming)
                        orders = orders+gSteps*2

                    # Rx gate
                    if (repeIndex==0 or repeIndex>=self.dummyPulses):
                        t0 = tEcho-self.acqTime/2-addRdPoints/BW
                        self.rxGate(t0, self.acqTime+2*addRdPoints/BW)
                        acqPoints += nRD

                    # Rephasing phase and slice gradients
                    t0 = tEcho+self.acqTime/2+addRdPoints/BW-hw.gradDelay
                    if (echoIndex<self.etl-1 and repeIndex>=self.dummyPulses):
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, -phGradients[phIndex], gSteps, self.axesOrientation[1], self.shimming)
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, -slGradients[slIndex], gSteps, self.axesOrientation[2], self.shimming)
                        orders = orders+gSteps*4
                    elif(echoIndex==self.etl-1 and repeIndex>=self.dummyPulses):
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, +phGradients[phIndex], gSteps, self.axesOrientation[1], self.shimming)
                        self.gradTrap(t0, gradRiseTime, self.phGradTime, +slGradients[slIndex], gSteps, self.axesOrientation[2], self.shimming)
                        orders = orders+gSteps*4

                    # Update the phase and slice gradient
                    if repeIndex>=self.dummyPulses:
                        if phIndex == nPH-1:
                            phIndex = 0
                            slIndex += 1
                        else:
                            phIndex += 1
                if repeIndex>=self.dummyPulses: repeIndexGlobal += 1 # Update the global repeIndex
                repeIndex+=1 # Update the repeIndex after the ETL

            # Turn off the gradients after the end of the batch
            self.endSequence(repeIndex*self.repetitionTime)

            # Return the output variables
            return(phIndex, slIndex, repeIndexGlobal, acqPoints)

        # Changing time parameters to us
        self.rfExTime = self.rfExTime*1e6
        self.rfReTime = self.rfReTime*1e6
        self.echoSpacing = self.echoSpacing*1e6
        self.repetitionTime = self.repetitionTime*1e6
        gradRiseTime = gradRiseTime*1e6
        self.phGradTime = self.phGradTime*1e6
        self.rdGradTime = self.rdGradTime*1e6
        self.rdDephTime = self.rdDephTime*1e6
        self.inversionTime = self.inversionTime*1e6
        self.preExTime = self.preExTime*1e6
        nRepetitions = int(nSL*nPH/self.etl)
        scanTime = nRepetitions*self.repetitionTime
        self.mapVals['scanTime'] = scanTime*nSL*1e-6

        # Calibrate frequency
        if self.freqCal and (not plotSeq) and (not demo):
            hw.larmorFreq = self.freqCalibration(bw=0.05)
            hw.larmorFreq = self.freqCalibration(bw=0.005)
        self.mapVals['larmorFreq'] = hw.larmorFreq

        # Create full sequence
        # Run the experiment
        dataFull = []
        dummyData = []
        overData = []
        noise = []
        nBatches = 0
        repeIndexArray = np.array([0])
        repeIndexGlobal = repeIndexArray[0]
        phIndex = 0
        slIndex = 0
        acqPointsPerBatch = []
        while repeIndexGlobal<nRepetitions:
            nBatches += 1
            if not demo:
                self.expt = ex.Experiment(lo_freq=hw.larmorFreq+self.freqOffset, rx_t=samplingPeriod, init_gpa=init_gpa, gpa_fhdo_offset_time=(1 / 0.2 / 3.1))
                samplingPeriod = self.expt.get_rx_ts()[0]
                BW = 1/samplingPeriod/hw.oversamplingFactor
                self.acqTime = self.nPoints[0]/BW        # us
                self.mapVals['bw'] = BW
                phIndex, slIndex, repeIndexGlobal, aa = createSequence(phIndex=phIndex,
                                                                   slIndex=slIndex,
                                                                   repeIndexGlobal=repeIndexGlobal,
                                                                   rewrite=nBatches==1)
                repeIndexArray = np.concatenate((repeIndexArray, np.array([repeIndexGlobal-1])), axis=0)
                acqPointsPerBatch.append(aa)
            else:
                phIndex, slIndex, repeIndexGlobal, aa, dataA = createSequenceDemo(phIndex=phIndex,
                                                                   slIndex=slIndex,
                                                                   repeIndexGlobal=repeIndexGlobal,
                                                                   rewrite=nBatches==1)
                repeIndexArray = np.concatenate((repeIndexArray, np.array([repeIndexGlobal-1])), axis=0)
                acqPointsPerBatch.append(aa)
                self.mapVals['bw'] = 1/samplingPeriod/hw.oversamplingFactor

            for ii in range(self.nScans):
                if not demo:
                    if not plotSeq:
                        print('Batch ', nBatches, ', Scan ', ii+1, ' runing...')
                        rxd, msgs = self.expt.run()
                        rxd['rx0'] = rxd['rx0']*13.788   # Here I normalize to get the result in mV
                        # Get noise data
                        noise = np.concatenate((noise, rxd['rx0'][0:nRD*hw.oversamplingFactor]), axis = 0)
                        rxd['rx0'] = rxd['rx0'][nRD*hw.oversamplingFactor::]
                        # Get data
                        if self.dummyPulses>0:
                            dummyData = np.concatenate((dummyData, rxd['rx0'][0:nRD*self.etl*hw.oversamplingFactor]), axis = 0)
                            overData = np.concatenate((overData, rxd['rx0'][nRD*self.etl*hw.oversamplingFactor::]), axis = 0)
                        else:
                            overData = np.concatenate((overData, rxd['rx0']), axis = 0)
                else:
                    print('Batch ', nBatches, ', Scan ', ii, ' runing...')
                    data = dataA
                    noise = np.concatenate((noise, data[0:nRD*hw.oversamplingFactor]), axis = 0)
                    data = data[nRD*hw.oversamplingFactor::]
                    # Get data
                    if self.dummyPulses>0:
                        dummyData = np.concatenate((dummyData, data[0:nRD*self.etl*hw.oversamplingFactor]), axis = 0)
                        overData = np.concatenate((overData, data[nRD*self.etl*hw.oversamplingFactor::]), axis = 0)
                    else:
                        overData = np.concatenate((overData, data), axis = 0)

            if not demo: self.expt.__del__()
        del aa

        if not plotSeq:
            acqPointsPerBatch= (np.array(acqPointsPerBatch)-self.etl*nRD*(self.dummyPulses>0)-nRD)*self.nScans
            print('Scans done!')
            self.mapVals['noiseData'] = noise
            self.mapVals['overData'] = overData

            # Fix the echo position using oversampled data
            if self.dummyPulses>0:
                dummyData = np.reshape(dummyData,  (nBatches*self.nScans, self.etl, nRD*hw.oversamplingFactor))
                dummyData = np.average(dummyData, axis=0)
                self.mapVals['dummyData'] = dummyData
                overData = np.reshape(overData, (-1, self.etl, nRD*hw.oversamplingFactor))
                overData = self.fixEchoPosition(dummyData, overData)
                overData = np.reshape(overData, -1)

            # Generate dataFull
            dataFull = sig.decimate(overData, hw.oversamplingFactor, ftype='fir', zero_phase=True)
            if nBatches>1:
                dataFullA = dataFull[0:sum(acqPointsPerBatch[0:-1])]
                dataFullB = dataFull[sum(acqPointsPerBatch[0:-1])::]

            # Reorganize dataFull
            dataProv = np.zeros([self.nScans,nSL*nPH*nRD])
            dataProv = dataProv+1j*dataProv
            dataFull = np.reshape(dataFull, (nBatches, self.nScans, -1, nRD))
            if nBatches>1:
                dataFullA = np.reshape(dataFullA, (nBatches-1, self.nScans, -1, nRD))
                dataFullB = np.reshape(dataFullB, (1, self.nScans, -1, nRD))
            for scan in range(self.nScans):
                if nBatches>1:
                    dataProv[scan, :] = np.concatenate((np.reshape(dataFullA[:,scan,:,:],-1), np.reshape(dataFullB[:,scan,:,:],-1)), axis=0)
                else:
                    dataProv[scan, :] = np.reshape(dataFull[:,scan,:,:],-1)
            dataFull = np.reshape(dataProv,-1)

            # Get index for krd = 0
            # Average data
            dataProv = np.reshape(dataFull, (self.nScans, nRD*nPH*nSL))
            dataProv = np.average(dataProv, axis=0)
            # Reorganize the data acording to sweep mode
            dataProv = np.reshape(dataProv, (nSL, nPH, nRD))
            dataTemp = dataProv*0
            for ii in range(nPH):
                dataTemp[:, ind[ii], :] = dataProv[:,  ii, :]
            dataProv = dataTemp
            # Check where is krd = 0
            dataProv = dataProv[int(self.nPoints[2]/2), int(nPH/2), :]
            indkrd0 = np.argmax(np.abs(dataProv))
            if  indkrd0 < nRD/2-addRdPoints or indkrd0 > nRD/2+addRdPoints:
                indkrd0 = int(nRD/2)

            # Get individual images
            dataFull = np.reshape(dataFull, (self.nScans, nSL, nPH, nRD))
            dataFull = dataFull[:, :, :, indkrd0-int(self.nPoints[0]/2):indkrd0+int(self.nPoints[0]/2)]
            dataTemp = dataFull*0
            for ii in range(nPH):
                dataTemp[:, :, ind[ii], :] = dataFull[:, :,  ii, :]
            dataFull = dataTemp
            imgFull = dataFull*0
            for ii in range(self.nScans):
                imgFull[ii, :, :, :] = np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(dataFull[ii, :, :, :])))
            self.mapVals['dataFull'] = dataFull
            self.mapVals['imgFull'] = imgFull

            # Average data
            data = np.average(dataFull, axis=0)
            data = np.reshape(data, (nSL, nPH, self.nPoints[0]))

            # Do zero padding
            dataTemp = np.zeros((self.nPoints[2], self.nPoints[1], self.nPoints[0]))
            dataTemp = dataTemp+1j*dataTemp
            dataTemp[0:nSL, :, :] = data
            data = np.reshape(dataTemp, (1, self.nPoints[0]*self.nPoints[1]*self.nPoints[2]))

            # Fix the position of the sample according to dfov
            kMax = np.array(self.nPoints)/(2*np.array(self.fov))*np.array(self.axesEnable)
            kRD = np.linspace(-kMax[0],kMax[0],num=self.nPoints[0],endpoint=False)
        #        kPH = np.linspace(-kMax[1],kMax[1],num=nPoints[1],endpoint=False)
            kSL = np.linspace(-kMax[2],kMax[2],num=self.nPoints[2],endpoint=False)
            kPH = kPH[::-1]
            kPH, kSL, kRD = np.meshgrid(kPH, kSL, kRD)
            kRD = np.reshape(kRD, (1, self.nPoints[0]*self.nPoints[1]*self.nPoints[2]))
            kPH = np.reshape(kPH, (1, self.nPoints[0]*self.nPoints[1]*self.nPoints[2]))
            kSL = np.reshape(kSL, (1, self.nPoints[0]*self.nPoints[1]*self.nPoints[2]))
            dPhase = np.exp(-2*np.pi*1j*(self.dfov[0]*kRD-self.dfov[1]*kPH-self.dfov[2]*kSL))
            data = np.reshape(data*dPhase, (self.nPoints[2], self.nPoints[1], self.nPoints[0]))
            self.mapVals['kSpace3D'] = data
            img=np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(data)))
            self.mapVals['image3D'] = img
            data = np.reshape(data, (1, self.nPoints[0]*self.nPoints[1]*self.nPoints[2]))

            # Create sampled data
            kRD = np.reshape(kRD, (self.nPoints[0]*self.nPoints[1]*self.nPoints[2], 1))
            kPH = np.reshape(kPH, (self.nPoints[0]*self.nPoints[1]*self.nPoints[2], 1))
            kSL = np.reshape(kSL, (self.nPoints[0]*self.nPoints[1]*self.nPoints[2], 1))
            data = np.reshape(data, (self.nPoints[0]*self.nPoints[1]*self.nPoints[2], 1))
            self.mapVals['kMax'] = kMax
            self.mapVals['sampled'] = np.concatenate((kRD, kPH, kSL, data), axis=1)
            self.mapVals['sampledCartesian'] = self.mapVals['sampled']  # To sweep
            data = np.reshape(data, (self.nPoints[2], self.nPoints[1], self.nPoints[0]))


    def sequenceAnalysis(self, obj=''):
        self.saveRawData()
        nPoints = self.mapVals['nPoints']
        axesEnable = self.mapVals['axesEnable']

        # Get axes in strings
        axes = self.mapVals['axesOrientation']
        axesDict = {'x':0, 'y':1, 'z':2}
        axesKeys = list(axesDict.keys())
        axesVals = list(axesDict.values())
        axesStr = ['','','']
        n = 0
        for val in axes:
            index = axesVals.index(val)
            axesStr[n] = axesKeys[index]
            n += 1

        # Create widget to introduce the figures
        win = pg.LayoutWidget()
        win.resize(300, 1000)

        if (axesEnable[1] == 0 and axesEnable[2] == 0):
            bw = self.mapVals['bw']*1e-3 # kHz
            acqTime = self.mapVals['acqTime'] # ms
            tVector = np.linspace(-acqTime/2, acqTime/2, nPoints[0])
            sVector = self.mapVals['sampled'][:, 3]
            fVector = np.linspace(-bw/2, bw/2, nPoints[0])
            iVector = np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(sVector)))

            # Plots to show into the GUI
            f_plotview = SpectrumPlot(fVector, [np.abs(iVector)], ['Spectrum magnitude'],
                                      "Frequency (kHz)", "Amplitude (a.u.)",
                                      "Spectrum")
            t_plotview = SpectrumPlot(tVector, [np.abs(sVector), np.real(sVector), np.imag(sVector)],
                                      ['Magnitude', 'Real', 'Imaginary'],
                                      'Time (ms)', "Signal amplitude (mV)",
                                      "Signal")

            # Introduce the images into the layout
            win.addWidget(t_plotview, row=0, col=0)
            win.addWidget(f_plotview, row=0, col=1)

            if obj=="Standalone":
                pg.exec()
            return([win])
        else:
            # Plot image
            image = np.abs(self.mapVals['image3D'])
            image = image/np.max(np.reshape(image,-1))*100

            # Image orientation
            if self.axesOrientation[2] == 2:  # Sagital
                title = "Sagital"
                if self.axesOrientation[0] == 0 and self.axesOrientation[1] == 1:
                    image = np.flip(image, axis=2)
                    image = np.flip(image, axis=1)
                    xLabel = "A | PHASE | P"
                    yLabel = "I | READOUT | S"
                else:
                    image = np.transpose(image, (0, 2, 1))
                    image = np.flip(image, axis=2)
                    image = np.flip(image, axis=1)
                    xLabel = "A | READOUT | P"
                    yLabel = "I | PHASE | S"
            if self.axesOrientation[2] == 1: # Coronal
                title = "Coronal"
                if self.axesOrientation[0] == 0 and self.axesOrientation[1] == 2:
                    image = np.flip(image, axis=2)
                    xLabel = "L | PHASE | R"
                    yLabel = "I | READOUT | S"
                else:
                    image = np.transpose(image, (0, 2, 1))
                    image = np.flip(image, axis=2)
                    xLabel = "L | READOUT | R"
                    yLabel = "I | PHASE | S"
            if self.axesOrientation[2] == 0:  # Transversal
                title = "Transversal"
                if self.axesOrientation[0] == 1 and self.axesOrientation[1] == 2:
                    image = np.flip(image, axis=2)
                    xLabel = "L | PHASE | R"
                    yLabel = "P | READOUT | A"
                else:
                    image = np.transpose(image, (0, 2, 1))
                    image = np.flip(image, axis=2)
                    xLabel = "L | READOUT | R"
                    yLabel = "P | PHASE | A"

            image = Spectrum3DPlot(image,
                                   title=title,
                                   xLabel=xLabel,
                                   yLabel=yLabel)
            imageWidget = image.getImageWidget()

            try:
                kSpace = Spectrum3DPlot(np.log10(np.abs(self.mapVals['kSpace3D'])),
                                        title='k-Space',
                                        xLabel="k%s"%axesStr[1],
                                        yLabel="k%s"%axesStr[0])
            except:
                kSpace = Spectrum3DPlot(np.abs(self.mapVals['kSpace3D']),
                                        title='k-Space',
                                        xLabel="k%s" % axesStr[1],
                                        yLabel="k%s" % axesStr[0])
            kSpaceWidget = kSpace.getImageWidget()

            win.addWidget(imageWidget, row=0, col=0)
            win.addWidget(kSpaceWidget, row=0, col=1)

            if obj=="Standalone":
                pg.exec()
            return([win])

if __name__=="__main__":
    seq = RARE()
    seq.sequenceRun()
    seq.sequenceAnalysis(obj='Standalone')
