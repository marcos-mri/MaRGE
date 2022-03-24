# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 12:40:05 2021
@author: José Miguel Algarín Guisado
MRILAB @ I3M
"""

import sys
# marcos_client path for linux
sys.path.append('../marcos_client')
# marcos_client and PhysioMRI_GUI for Windows
sys.path.append('D:\CSIC\REPOSITORIOS\marcos_client')
sys.path.append('D:\CSIC\REPOSITORIOS\PhysioMRI_GUI')
import numpy as np
import experiment as ex
import matplotlib.pyplot as plt
import scipy.signal as sig
import os
from scipy.io import savemat
from datetime import date,  datetime 
import pdb
from configs.hw_config import Gx_factor
from configs.hw_config import Gy_factor
from configs.hw_config import Gz_factor
st = pdb.set_trace



#*********************************************************************************
#*********************************************************************************
#*********************************************************************************


def rare_standalone(
    init_gpa=False, # Starts the gpa
    nScans = 1, # NEX
    larmorFreq = 3.075, # MHz, Larmor frequency
    rfExAmp = 0.4, # a.u., rf excitation pulse amplitude
    rfReAmp = 0.4, # a.u., rf refocusing pulse amplitude
    rfExTime = 21, # us, rf excitation pulse time
    rfReTime = 42, # us, rf refocusing pulse time
    echoSpacing = 10., # ms, time between echoes
    preExTime = 0., # ms, Time from preexcitation pulse to inversion pulse
    inversionTime = 500., # ms, Inversion recovery time
    repetitionTime = 2000., # ms, TR
    fov = np.array([72., 72., 70.]), # mm, FOV along readout, phase and slice
    dfov = np.array([-3., 35., -10.]), # mm, displacement of fov center
    nPoints = np.array([36, 36, 8]), # Number of points along readout, phase and slice
    etl = 36, # Echo train length
    acqTime = 2, # ms, acquisition time
    axes = np.array([2, 1, 0]), # 0->x, 1->y and 2->z defined as [rd,ph,sl]
    axesEnable = np.array([1, 1, 1]), # 1-> Enable, 0-> Disable
    sweepMode = 1, # 0->k2k (T2),  1->02k (T1),  2->k20 (T2), 3->Niquist modulated (T2)
    rdGradTime = 4,  # ms, readout gradient time
    phGradTime = 1, # ms, phase and slice dephasing time
    rdPreemphasis = 1.010, # readout dephasing gradient is multiplied by this factor
    drfPhase = 0, # degrees, phase of the excitation pulse
    dummyPulses = 1, # number of dummy pulses for T1 stabilization
    shimming = np.array([-70., -90., 10.]), # a.u.*1e4, shimming along the X,Y and Z axes
    parAcqLines = 0 # number of additional lines, Full sweep if 0
    ):
    
    # rawData fields
    rawData = {}
    
    # Conversion of variables to non-multiplied units
    larmorFreq = larmorFreq*1e6
    rfExTime = rfExTime*1e-6
    rfReTime = rfReTime*1e-6
    fov = np.array(fov)*1e-3
    dfov = np.array(dfov)*1e-3
    echoSpacing = echoSpacing*1e-3
    acqTime = acqTime*1e-3
    shimming = shimming*1e-4
    repetitionTime= repetitionTime*1e-3
    preExTime = preExTime*1e-3
    inversionTime = inversionTime*1e-3
    rdGradTime = rdGradTime*1e-3
    phGradTime = phGradTime*1e-3
    
    # Inputs for rawData
    rawData['nScans'] = nScans
    rawData['larmorFreq'] = larmorFreq      # Larmor frequency
    rawData['rfExAmp'] = rfExAmp             # rf excitation pulse amplitude
    rawData['rfReAmp'] = rfReAmp             # rf refocusing pulse amplitude
    rawData['rfExTime'] = rfExTime          # rf excitation pulse time
    rawData['rfReTime'] = rfReTime            # rf refocusing pulse time
    rawData['echoSpacing'] = echoSpacing        # time between echoes
    rawData['preExTime'] = preExTime
    rawData['inversionTime'] = inversionTime       # Inversion recovery time
    rawData['repetitionTime'] = repetitionTime     # TR
    rawData['fov'] = fov           # FOV along readout, phase and slice
    rawData['dfov'] = dfov            # Displacement of fov center
    rawData['nPoints'] = nPoints                 # Number of points along readout, phase and slice
    rawData['etl'] = etl                    # Echo train length
    rawData['acqTime'] = acqTime             # Acquisition time
    rawData['axesOrientation'] = axes       # 0->x, 1->y and 2->z defined as [rd,ph,sl]
    rawData['axesEnable'] = axesEnable # 1-> Enable, 0-> Disable
    rawData['sweepMode'] = sweepMode               # 0->k2k (T2),  1->02k (T1),  2->k20 (T2), 3->Niquist modulated (T2)
    rawData['rdPreemphasis'] = rdPreemphasis
    rawData['drfPhase'] = drfPhase 
    rawData['dummyPulses'] = dummyPulses                    # Dummy pulses for T1 stabilization
    rawData['partialAcquisition'] = parAcqLines
    
    # Miscellaneous
    blkTime = 10             # Deblanking time (us)
    larmorFreq = larmorFreq*1e-6
    gradRiseTime = 400e-6       # Estimated gradient rise time
    gSteps = int(gradRiseTime*1e6/5)*0+1
    gradDelay = 9            # Gradient amplifier delay
    addRdPoints = 1             # Initial rd points to avoid artifact at the begining of rd
    gammaB = 42.56e6            # Gyromagnetic ratio in Hz/T
    oversamplingFactor = 6
    randFactor = 0e-3                        # Random amplitude to add to the phase gradients
    if rfReAmp==0:
        rfReAmp = rfExAmp
    if rfReTime==0:
        rfReTime = 2*rfExTime
    resolution = fov/nPoints
    rawData['resolution'] = resolution
    rawData['gradDelay'] = gradDelay*1e-6
    rawData['gradRiseTime'] = gradRiseTime
    rawData['oversamplingFactor'] = oversamplingFactor
    rawData['randFactor'] = randFactor
    rawData['addRdPoints'] = addRdPoints
    
    # Matrix size
    nRD = nPoints[0]+2*addRdPoints
    nPH = nPoints[1]*axesEnable[1]+(1-axesEnable[1])
    nSL = nPoints[2]*axesEnable[2]+(1-axesEnable[2])
    
    # ETL if nPH = 1
    if etl>nPH:
        etl = nPH
    
    # parAcqLines in case parAcqLines = 0
    if parAcqLines==0:
        parAcqLines = int(nSL/2)
    
    # BW
    BW = nPoints[0]/acqTime*1e-6
    BWov = BW*oversamplingFactor
    samplingPeriod = 1/BWov
    
    # Readout gradient time
    if rdGradTime>0 and rdGradTime<acqTime:
        rdGradTime = acqTime
    rawData['rdGradTime'] = rdGradTime
    
    # Phase and slice de- and re-phasing time
    if phGradTime==0 or phGradTime>echoSpacing/2-rfExTime/2-rfReTime/2-2*gradRiseTime:
        phGradTime = echoSpacing/2-rfExTime/2-rfReTime/2-2*gradRiseTime
    rawData['phGradTime'] = phGradTime
    
    # Readout dephasing time
    rdDephTime = (rdGradTime-gradRiseTime)/2

    # Max gradient amplitude
    rdGradAmplitude = nPoints[0]/(gammaB*fov[0]*acqTime)*axesEnable[0]
    phGradAmplitude = nPH/(2*gammaB*fov[1]*(phGradTime+gradRiseTime))*axesEnable[1]
    slGradAmplitude = nSL/(2*gammaB*fov[2]*(phGradTime+gradRiseTime))*axesEnable[2]
    rawData['rdGradAmplitude'] = rdGradAmplitude
    rawData['phGradAmplitude'] = phGradAmplitude
    rawData['slGradAmplitude'] = slGradAmplitude

    # Get factors to OCRA1 units
    gFactor = reorganizeGfactor(axes)
    rawData['gFactor'] = gFactor
    
    # Phase and slice gradient vector
    phGradients = np.linspace(-phGradAmplitude,phGradAmplitude,num=nPH,endpoint=False)
    slGradients = np.linspace(-slGradAmplitude,slGradAmplitude,num=nSL,endpoint=False)
    
    # Now fix the number of slices to partailly acquired k-space
    nSL = (int(nPoints[2]/2)+parAcqLines)*axesEnable[2]+(1-axesEnable[2])
    
    # Add random displacemnt to phase encoding lines
    for ii in range(nPH):
        if ii<np.ceil(nPH/2-nPH/20) or ii>np.ceil(nPH/2+nPH/20):
            phGradients[ii] = phGradients[ii]+randFactor*np.random.randn()
    kPH = gammaB*phGradients*(gradRiseTime+phGradTime)
    rawData['phGradients'] = phGradients
    rawData['slGradients'] = slGradients
    
    # Change units to OCRA1 board
    rdGradAmplitude = rdGradAmplitude/gFactor[0]*1000/5
    phGradients = phGradients/gFactor[1]*1000/5
    slGradients = slGradients/gFactor[2]*1000/5
    
    # Set phase vector to given sweep mode
    ind = getIndex(phGradients, etl, nPH, sweepMode)
    rawData['sweepOrder'] = ind
    phGradients = phGradients[::-1]
    phGradients = phGradients[ind]

    # Create functions
    def rfPulse(tStart,rfTime,rfAmplitude,rfPhase):
        txTime = np.array([tStart+blkTime,tStart+blkTime+rfTime])
        txAmp = np.array([rfAmplitude*np.exp(1j*rfPhase),0.])
        txGateTime = np.array([tStart,tStart+blkTime+rfTime])
        txGateAmp = np.array([1,0])
        expt.add_flodict({
            'tx0': (txTime, txAmp),
            'tx_gate': (txGateTime, txGateAmp)
            })

    def rxGate(tStart,gateTime):
        rxGateTime = np.array([tStart,tStart+gateTime])
        rxGateAmp = np.array([1,0])
        expt.add_flodict({
            'rx0_en':(rxGateTime, rxGateAmp), 
            'rx_gate': (rxGateTime, rxGateAmp), 
            })

    def gradTrap(tStart, gTime, gAmp, gAxis):
        tUp = np.linspace(tStart, tStart+gradRiseTime, num=gSteps, endpoint=False)
        tDown = tUp+gradRiseTime+gTime
        t = np.concatenate((tUp, tDown), axis=0)
        dAmp = gAmp/gSteps
        aUp = np.linspace(dAmp, gAmp, num=gSteps)
        aDown = np.linspace(gAmp-dAmp, 0, num=gSteps)
        a = np.concatenate((aUp, aDown), axis=0)
        if gAxis==0:
            expt.add_flodict({'grad_vx': (t, a+shimming[0])})
        elif gAxis==1:
            expt.add_flodict({'grad_vy': (t, a+shimming[1])})
        elif gAxis==2:
            expt.add_flodict({'grad_vz': (t, a+shimming[2])})
    
    def gradPulse(tStart, gTime, gAmp,  gAxes):
        t = np.array([tStart, tStart+gradRiseTime+gTime])
        for gIndex in range(np.size(gAxes)):
            a = np.array([gAmp[gIndex], 0])
            if gAxes[gIndex]==0:
                expt.add_flodict({'grad_vx': (t, a+shimming[0])})
            elif gAxes[gIndex]==1:
                expt.add_flodict({'grad_vy': (t, a+shimming[1])})
            elif gAxes[gIndex]==2:
                expt.add_flodict({'grad_vz': (t, a+shimming[2])})
    
    def endSequence(tEnd):
        expt.add_flodict({
                'grad_vx': (np.array([tEnd]),np.array([0]) ), 
                'grad_vy': (np.array([tEnd]),np.array([0]) ), 
                'grad_vz': (np.array([tEnd]),np.array([0]) ),
             })
             
    def iniSequence(tEnd):
        expt.add_flodict({
                'grad_vx': (np.array([tEnd]),np.array([shimming[0]]) ), 
                'grad_vy': (np.array([tEnd]),np.array([shimming[1]]) ), 
                'grad_vz': (np.array([tEnd]),np.array([shimming[2]]) ),
             })

    def createSequence():
        phIndex = 0
        slIndex = 0
        nRepetitions = int(nPH*nSL/etl+dummyPulses)
        scanTime = 20e3+nRepetitions*repetitionTime
        rawData['scanTime'] = scanTime*1e-6
        # Set shimming
        iniSequence(20)
        for repeIndex in range(nRepetitions):
            # Initialize time
            tEx = 20e3+repetitionTime*repeIndex+inversionTime+preExTime+blkTime+rfExTime/2
            
            # Pre-excitation pulse
            if preExTime!=0:
                t0 = tEx-preExTime-inversionTime-rfExTime/2-blkTime
                rfPulse(t0,rfExTime,rfExAmp/90*90,0)
                
            # Inversion pulse
            if inversionTime!=0:
                t0 = tEx-inversionTime-rfReTime/2-blkTime
                rfPulse(t0,rfReTime,rfReAmp,0)
                gradTrap(t0+blkTime+rfReTime, inversionTime*0.25, 0.2, axes[0])
                gradTrap(t0+blkTime+rfReTime, inversionTime*0.25, 0.2, axes[1])
                gradTrap(t0+blkTime+rfReTime, inversionTime*0.25, 0.2, axes[2])
                
            # Excitation pulse
            t0 = tEx-blkTime-rfExTime/2
            rfPulse(t0,rfExTime,rfExAmp,drfPhase*np.pi/180)
        
            # Dephasing readout
            t0 = tEx+rfExTime/2-gradDelay
            if repeIndex>=dummyPulses:         # This is to account for dummy pulses
                gradTrap(t0, rdDephTime, rdGradAmplitude*rdPreemphasis, axes[0])
            
            # Echo train
            for echoIndex in range(etl):
                tEcho = tEx+echoSpacing*(echoIndex+1)
                
                # Refocusing pulse
                t0 = tEcho-echoSpacing/2-rfReTime/2-blkTime
                rfPulse(t0, rfReTime, rfReAmp, np.pi/2)
    
                # Dephasing phase and slice gradients
                t0 = tEcho-echoSpacing/2+rfReTime/2-gradDelay
                if repeIndex>=dummyPulses:         # This is to account for dummy pulses
                    gradTrap(t0, phGradTime, phGradients[phIndex], axes[1])
                    gradTrap(t0, phGradTime, slGradients[slIndex], axes[2])
                
                # Readout gradient
                t0 = tEcho-rdGradTime/2-gradRiseTime-gradDelay
                if repeIndex>=dummyPulses:         # This is to account for dummy pulses
                    gradTrap(t0, rdGradTime, rdGradAmplitude, axes[0])
    
                # Rx gate
                t0 = tEcho-acqTime/2-addRdPoints/BW
                if repeIndex>=dummyPulses:         # This is to account for dummy pulses
                    rxGate(t0, acqTime+2*addRdPoints/BW)
    
                # Rephasing phase and slice gradients
                t0 = tEcho+acqTime/2+addRdPoints/BW-gradDelay
                if (echoIndex<etl-1 and repeIndex>=dummyPulses):
                    gradTrap(t0, phGradTime, -phGradients[phIndex], axes[1])
                    gradTrap(t0, phGradTime, -slGradients[slIndex], axes[2])
    
                # Update the phase and slice gradient
                if repeIndex>=dummyPulses:
                    if phIndex == nPH-1:
                        phIndex = 0
                        slIndex += 1
                    else:
                        phIndex += 1
                
            if repeIndex==nRepetitions-1:
                endSequence(scanTime)
    
    
    def createFreqCalSequence():
        t0 = 20
        
        # Shimming
        iniSequence(t0)
            
        # Excitation pulse
        rfPulse(t0,rfExTime,rfExAmp,drfPhase*np.pi/180)
        
        # Refocusing pulse
        t0 += rfExTime/2+echoSpacing/2-rfReTime/2
        rfPulse(t0, rfReTime, rfReAmp, np.pi/2)
        
        # Rx
        t0 += blkTime+rfReTime/2+echoSpacing/2-acqTime/2-addRdPoints/BW
        rxGate(t0, acqTime+2*addRdPoints/BW)
        
        # Finalize sequence
        endSequence(repetitionTime)
        
    
    # Changing time parameters to us
    rfExTime = rfExTime*1e6
    rfReTime = rfReTime*1e6
    echoSpacing = echoSpacing*1e6
    repetitionTime = repetitionTime*1e6
    gradRiseTime = gradRiseTime*1e6
    phGradTime = phGradTime*1e6
    rdGradTime = rdGradTime*1e6
    rdDephTime = rdDephTime*1e6
    inversionTime = inversionTime*1e6
    preExTime = preExTime*1e6
    
    # Calibrate frequency
    expt = ex.Experiment(lo_freq=larmorFreq, rx_t=samplingPeriod, init_gpa=init_gpa, gpa_fhdo_offset_time=(1 / 0.2 / 3.1))
    samplingPeriod = expt.get_rx_ts()[0]
    BW = 1/samplingPeriod/oversamplingFactor
    acqTime = nPoints[0]/BW        # us
    rawData['bw'] = BW*1e6
    createFreqCalSequence()
    rxd, msgs = expt.run()
    dataFreqCal = sig.decimate(rxd['rx0']*13.788, oversamplingFactor, ftype='fir', zero_phase=True)
    dataFreqCal = dataFreqCal[addRdPoints:nPoints[0]+addRdPoints]
    # Plot fid
#    plt.figure(1)
    tVector = np.linspace(-acqTime/2, acqTime/2, num=nPoints[0],endpoint=True)*1e-3
#    plt.subplot(1, 2, 1)
#    plt.plot(tVector, np.abs(dataFreqCal))
#    plt.title("Signal amplitude")
#    plt.xlabel("Time (ms)")
#    plt.ylabel("Amplitude (mV)")
#    plt.subplot(1, 2, 2)
    angle = np.unwrap(np.angle(dataFreqCal))
#    plt.title("Signal phase")
#    plt.xlabel("Time (ms)")
#    plt.ylabel("Phase (rad)")
#    plt.plot(tVector, angle)
    # Get larmor frequency
    dPhi = angle[-1]-angle[0]
    df = dPhi/(2*np.pi*acqTime)
    larmorFreq += df
    rawData['larmorFreq'] = larmorFreq*1e6
    print("f0 = %s MHz" % (round(larmorFreq, 5)))
    # Plot sequence:
#    expt.plot_sequence()
#    plt.show()
    # Delete experiment:
    expt.__del__()
    
    # Create full sequence
    expt = ex.Experiment(lo_freq=larmorFreq, rx_t=samplingPeriod, init_gpa=init_gpa, gpa_fhdo_offset_time=(1 / 0.2 / 3.1))
    samplingPeriod = expt.get_rx_ts()[0]
    BW = 1/samplingPeriod/oversamplingFactor
    acqTime = nPoints[0]/BW        # us
    createSequence()
    
    # Plot sequence:
#    expt.plot_sequence()
    
    
    # Run the experiment
    dataFull = []
    for ii in range(nScans):
        print("Scan %s ..." % (ii+1))
        rxd, msgs = expt.run()
        rxd['rx0'] = rxd['rx0']*13.788   # Here I normalize to get the result in mV
        # Get data
        scanData = sig.decimate(rxd['rx0'], oversamplingFactor, ftype='fir', zero_phase=True)
        dataFull = np.concatenate((dataFull, scanData), axis = 0)
    expt.__del__()
    print('Scans done!')
    
    # Get index for krd = 0
    # Average data
    dataProv = np.reshape(dataFull, (nScans, nRD*nPH*nSL))
    dataProv = np.average(dataProv, axis=0)
    dataProv = np.reshape(dataProv, (nSL, nPH, nRD))
    # Reorganize the data acording to sweep mode
    dataTemp = dataProv*0
    for ii in range(nPH):
        dataTemp[:, ind[ii], :] = dataProv[:,  ii, :]
    dataProv = dataTemp
    # Check where is krd = 0
    dataProv = dataProv[int(nSL/2), int(nPH/2), :]
    indkrd0 = np.argmax(np.abs(dataProv))
    if  indkrd0 < nRD/2-addRdPoints or indkrd0 > nRD+addRdPoints:
        indkrd0 = int(nRD/2)

    # Get individual images
    dataProv = np.reshape(dataFull, (nScans, nSL, nPH, nRD))
    dataProv = dataProv[:, :, :, indkrd0-int(nPoints[0]/2):indkrd0+int(nPoints[0]/2)]
    dataTemp = dataProv*0
    for ii in range(nPH):
        dataTemp[:, :, ind[ii], :] = dataProv[:, :,  ii, :]
    imgFull = dataProv*0
    for ii in(range(nScans)):
        imgFull[ii, :, :, :] = np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(dataTemp[ii, :, :, :])))
    rawData['dataFull'] = dataTemp
    rawData['imgFull'] = imgFull    

    # Get required readout points
    dataFull = np.reshape(dataFull, (nPH*nSL*nScans, nRD))
    dataFull = dataFull[:, indkrd0-int(nPoints[0]/2):indkrd0+int(nPoints[0]/2)]
    dataFull = np.reshape(dataFull, (1, nPoints[0]*nPH*nSL*nScans))
    
    # Average data
    data = np.reshape(dataFull, (nScans, nPoints[0]*nPH*nSL))
    data = np.average(data, axis=0)
    data = np.reshape(data, (nSL, nPH, nPoints[0]))
    
    # Reorganize the data acording to sweep mode
    dataTemp = data*0
    for ii in range(nPH):
        dataTemp[:, ind[ii], :] = data[:,  ii, :]
    
    # Do zero padding
    data = np.zeros((nPoints[2], nPoints[1], nPoints[0]))
    data = data+1j*data
    if nSL==1:
        data = dataTemp
    else:
        data[0:nSL-1, :, :] = dataTemp[0:nSL-1, :, :]
    data = np.reshape(data, (1, nPoints[0]*nPoints[1]*nPoints[2]))
        
    # Fix the position of the sample according t dfov
    kMax = np.array(nPoints)/(2*np.array(fov))*np.array(axesEnable)
    kRD = np.linspace(-kMax[0],kMax[0],num=nPoints[0],endpoint=False)
#        kPH = np.linspace(-kMax[1],kMax[1],num=nPoints[1],endpoint=False)
    kSL = np.linspace(-kMax[2],kMax[2],num=nPoints[2],endpoint=False)
    kPH = kPH[::-1]
    kPH, kSL, kRD = np.meshgrid(kPH, kSL, kRD)
    kRD = np.reshape(kRD, (1, nPoints[0]*nPoints[1]*nPoints[2]))
    kPH = np.reshape(kPH, (1, nPoints[0]*nPoints[1]*nPoints[2]))
    kSL = np.reshape(kSL, (1, nPoints[0]*nPoints[1]*nPoints[2]))
    dPhase = np.exp(-2*np.pi*1j*(dfov[0]*kRD+dfov[1]*kPH+dfov[2]*kSL))
    data = np.reshape(data*dPhase, (nPoints[2], nPoints[1], nPoints[0]))
    rawData['kSpace3D'] = data
    img=np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(data)))
    rawData['image3D'] = img
    data = np.reshape(data, (1, nPoints[0]*nPoints[1]*nPoints[2]))
    
    # Create sampled data
    kRD = np.reshape(kRD, (nPoints[0]*nPoints[1]*nPoints[2], 1))
    kPH = np.reshape(kPH, (nPoints[0]*nPoints[1]*nPoints[2], 1))
    kSL = np.reshape(kSL, (nPoints[0]*nPoints[1]*nPoints[2], 1))
    data = np.reshape(data, (nPoints[0]*nPoints[1]*nPoints[2], 1))
    rawData['kMax'] = kMax
    rawData['sampled'] = np.concatenate((kRD, kPH, kSL, data), axis=1)
    data = np.reshape(data, (nPoints[2], nPoints[1], nPoints[0]))
    
    
    # Save data
    dt = datetime.now()
    dt_string = dt.strftime("%Y.%m.%d.%H.%M.%S")
    dt2 = date.today()
    dt2_string = dt2.strftime("%Y.%m.%d")
    if not os.path.exists('experiments/acquisitions/%s' % (dt2_string)):
        os.makedirs('experiments/acquisitions/%s' % (dt2_string))
            
    if not os.path.exists('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)):
        os.makedirs('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)) 
    rawData['fileName'] = "%s.%s.mat" % ("RARE",dt_string)
    savemat("experiments/acquisitions/%s/%s/%s.%s.mat" % (dt2_string, dt_string, "Old_RARE",dt_string),  rawData) 
    
    # Plot data for 1D case
    if (nPH==1 and nSL==1):
        # Plot k-space
        plt.figure(3)
        dataPlot = data[0, 0, :]
        plt.subplot(1, 2, 1)
        if axesEnable[0]==0:
            tVector = np.linspace(-acqTime/2, acqTime/2, num=nPoints[0],endpoint=False)*1e-3
            sMax = np.max(np.abs(dataPlot))
            indMax = np.argmax(np.abs(dataPlot))
            timeMax = tVector[indMax]
            sMax3 = sMax/3
            dataPlot3 = np.abs(np.abs(dataPlot)-sMax3)
            indMin = np.argmin(dataPlot3)
            timeMin = tVector[indMin]
            T2 = np.abs(timeMax-timeMin)
            plt.plot(tVector, np.abs(dataPlot))
            plt.plot(tVector, np.real(dataPlot))
            plt.plot(tVector, np.imag(dataPlot))
            plt.xlabel('t (ms)')
            plt.ylabel('Signal (mV)')
            print("T2 = %s us" % (T2))
        else:
            plt.plot(kRD[:, 0], np.abs(dataPlot))
            plt.yscale('log')
            plt.xlabel('krd (mm^-1)')
            plt.ylabel('Signal (mV)')
            echoTime = np.argmax(np.abs(dataPlot))
            echoTime = kRD[echoTime, 0]
            print("Echo position = %s mm^{-1}" %round(echoTime, 1))
        
        # Plot image
        plt.subplot(122)
        img = img[0, 0, :]
        if axesEnable[0]==0:
            xAxis = np.linspace(-BW/2, BW/2, num=nPoints[0], endpoint=False)*1e3
            plt.plot(xAxis, np.abs(img), '.')
            plt.xlabel('Frequency (kHz)')
            plt.ylabel('Density (a.u.)')
            print("Smax = %s mV" % (np.max(np.abs(img))))
        else:
            xAxis = np.linspace(-fov[0]/2*1e2, fov[0]/2*1e2, num=nPoints[0], endpoint=False)
            plt.plot(xAxis, np.abs(img))
            plt.xlabel('Position RD (cm)')
            plt.ylabel('Density (a.u.)')
    else:
        # Plot k-space
        plt.figure(3)
        dataPlot = data[round(nSL/2), :, :]
        plt.subplot(121)
        plt.imshow(np.log(np.abs(dataPlot)),cmap='gray')
        plt.axis('off')
        # Plot image
        if sweepMode==3:
            imgPlot = img[round(nSL/2), round(nPH/4):round(3*nPH/4), :]
        else:
            imgPlot = img[round(nSL/2), :, :]
        plt.subplot(122)
        plt.imshow(np.abs(imgPlot), cmap='gray')
        plt.axis('off')
        plt.title("RARE.%s.mat" % (dt_string))
    
    # plot full image
    plt.figure(4)
    img2d = np.zeros((nPoints[1], nPoints[0]*nPoints[2]))
    img2d = img2d+1j*img2d
    for ii in range(nPoints[2]):
        img2d[:, ii*nPoints[0]:(ii+1)*nPoints[0]] = img[ii, :, :]
    plt.imshow(np.abs(img2d), cmap='gray')
    plt.axis('off')
    plt.title("RARE.%s.mat" % (dt_string))
    
    plt.show()
    

#*********************************************************************************
#*********************************************************************************
#*********************************************************************************


def getIndex(g_amps, echos_per_tr, n_ph, sweep_mode):
    n2ETL=int(n_ph/2/echos_per_tr)
    ind:int = [];
    if n_ph==1:
         ind = np.linspace(int(n_ph)-1, 0, n_ph)
    
    else: 
        if sweep_mode==0:   # Sequential for T2 contrast
            for ii in range(int(n_ph/echos_per_tr)):
               ind = np.concatenate((ind, np.arange(1, n_ph+1, n_ph/echos_per_tr)+ii))
            ind = ind-1

        elif sweep_mode==1: # Center-out for T1 contrast
            if echos_per_tr==n_ph:
                for ii in range(int(n_ph/2)):
                    cont = 2*ii
                    ind = np.concatenate((ind, np.array([n_ph/2-cont/2])), axis=0);
                    ind = np.concatenate((ind, np.array([n_ph/2+1+cont/2])), axis=0);
            else:
                for ii in range(n2ETL):
                    ind = np.concatenate((ind,np.arange(n_ph/2, 0, -n2ETL)-(ii)), axis=0);
                    ind = np.concatenate((ind,np.arange(n_ph/2+1, n_ph+1, n2ETL)+(ii)), axis=0);
            ind = ind-1
        elif sweep_mode==2: # Out-to-center for T2 contrast
            if echos_per_tr==n_ph:
                ind=np.arange(1, n_ph+1, 1)
            else:
                for ii in range(n2ETL):
                    ind = np.concatenate((ind,np.arange(1, n_ph/2+1, n2ETL)+(ii)), axis=0);
                    ind = np.concatenate((ind,np.arange(n_ph, n_ph/2, -n2ETL)-(ii)), axis=0);
            ind = ind-1
        elif sweep_mode==3:
            if echos_per_tr==n_ph:
                ind = np.arange(0, n_ph, 1)
            else:
                for ii in range(int(n2ETL)):
                    ind = np.concatenate((ind, np.arange(0, n_ph, 2*n2ETL)+2*ii), axis=0)
                    ind = np.concatenate((ind, np.arange(n_ph-1, 0, -2*n2ETL)-2*ii), axis=0)

    return np.int32(ind)


#*********************************************************************************
#*********************************************************************************
#*********************************************************************************


def reorganizeGfactor(axes):
    gFactor = np.array([0., 0., 0.])
    
    # Set the normalization factor for readout, phase and slice gradient
    for ii in range(3):
        if axes[ii]==0:
            gFactor[ii] = Gx_factor
        elif axes[ii]==1:
            gFactor[ii] = Gy_factor
        elif axes[ii]==2:
            gFactor[ii] = Gz_factor
    
    return(gFactor)

#*********************************************************************************
#*********************************************************************************
#*********************************************************************************


if __name__ == "__main__":

    rare_standalone()
